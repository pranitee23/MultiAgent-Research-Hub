"""
Nexus — Multi-dimensional LLM-as-judge.

Scores a synthesis on 5 independent axes to prevent reward hacking
(no single axis can carry a bad synthesis) and reward denial
(calibration examples anchor the scoring so good work isn't penalized).

Designed so that:
  - True positives:  good syntheses score >= 3.5 avg and all dims >= 3
  - True negatives:  bad syntheses score < 3.5 avg or any dim < 3
  - No false positives:  fabricated/off-topic work can't game all 5 axes
  - No false negatives:  calibration examples prevent arbitrary strictness
"""

import re
import logging
from dataclasses import dataclass, field, asdict
from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm

logger = logging.getLogger(__name__)

# ── Judge system prompt with calibration examples ─────────────────────────

JUDGE_SYSTEM = """\
You are a strict but fair research quality judge. Your job is to evaluate \
a research synthesis against the source papers it was supposed to summarize.

Score the synthesis on 5 INDEPENDENT dimensions. For each, give a score \
from 1-5 with a one-sentence justification.

DIMENSIONS:

1. FACTUAL_ACCURACY: Are all claims supported by the provided source papers?
   5 = every claim is directly traceable to a specific source paper
   4 = claims are accurate with minor imprecisions in wording
   3 = mostly accurate but one claim lacks clear source support
   2 = multiple claims exaggerated or unsupported by sources
   1 = contains fabricated facts, invented statistics, or hallucinated papers

2. RELEVANCE: Does the synthesis answer the original query?
   5 = directly and thoroughly addresses every aspect of the query
   4 = addresses the query with minor tangents
   3 = partially addresses the query but misses a key aspect
   2 = loosely related but misses the core question
   1 = completely off-topic or answers a different question

3. CITATION_GROUNDING: Are specific papers cited for specific claims?
   5 = every factual claim cites a specific paper by author and year
   4 = most claims are cited, one or two are attributed vaguely
   3 = some claims are cited but several lack attribution
   2 = only generic references ("studies show"), few specific citations
   1 = no citations or fabricated paper references

4. COMPLETENESS: Are the key findings from the source papers represented?
   5 = covers all major findings, methods, and results from sources
   4 = covers most findings, misses one minor point
   3 = covers the main theme but omits significant findings from sources
   2 = superficial — mentions papers but ignores their core contributions
   1 = essentially empty or ignores the source material

5. COHERENCE: Is the synthesis logically structured and readable?
   5 = clear narrative flow, well-organized sections, no contradictions
   4 = well-structured with minor awkwardness
   3 = adequate structure but some logical gaps
   2 = disorganized, hard to follow, or internally contradictory
   1 = incoherent or self-contradictory

CALIBRATION EXAMPLES:

--- Example: FACTUAL_ACCURACY = 5 ---
Claim: "Lewis et al. (2020) showed RAG achieves state-of-the-art on open-domain QA"
Source says: "RAG achieves state-of-the-art results on open-domain QA"
→ Direct match. Score: 5

--- Example: FACTUAL_ACCURACY = 1 ---
Claim: "RAG was invented by OpenAI in 2022 and eliminates hallucination entirely"
Source says: Lewis et al. 2020 introduced RAG; no source claims it eliminates hallucination
→ Fabricated origin and overstated result. Score: 1

--- Example: RELEVANCE = 1 ---
Query: "What is retrieval augmented generation?"
Synthesis: "CNNs have been the backbone of computer vision since AlexNet..."
→ Completely off-topic. Score: 1

--- Example: CITATION_GROUNDING = 3 ---
"Recent work shows RAG improves accuracy. Self-RAG adds reflection tokens (Asai et al., 2023)."
→ First claim uncited, second properly cited. Score: 3

--- Example: COMPLETENESS = 2 ---
Source papers discuss FedAvg, FedProx, and healthcare privacy challenges.
Synthesis says: "Federated learning is a machine learning technique. It is useful."
→ Ignores all substantive findings. Score: 2

OUTPUT FORMAT (you MUST follow this exactly):
FACTUAL_ACCURACY: <score>/5 | <one-sentence justification>
RELEVANCE: <score>/5 | <one-sentence justification>
CITATION_GROUNDING: <score>/5 | <one-sentence justification>
COMPLETENESS: <score>/5 | <one-sentence justification>
COHERENCE: <score>/5 | <one-sentence justification>
VERDICT: PASS or FAIL

VERDICT RULES:
- PASS if ALL scores >= 3 AND average >= 3.5
- FAIL if ANY score < 3 OR average < 3.5
- When in doubt, FAIL. It is better to reject a borderline synthesis than \
to approve a flawed one."""


JUDGE_HUMAN = """\
QUERY: {query}

SOURCE PAPERS:
{source_papers}

SYNTHESIS TO EVALUATE:
{synthesis}

Score each dimension and give your verdict:"""


judge_prompt = ChatPromptTemplate.from_messages([
    ("system", JUDGE_SYSTEM),
    ("human", JUDGE_HUMAN),
])


# ── Parsed result ─────────────────────────────────────────────────────────

@dataclass
class JudgeResult:
    factual_accuracy: int = 0
    relevance: int = 0
    citation_grounding: int = 0
    completeness: int = 0
    coherence: int = 0
    verdict: str = "fail"
    raw_output: str = ""
    justifications: dict = field(default_factory=dict)

    @property
    def average_score(self) -> float:
        scores = [
            self.factual_accuracy,
            self.relevance,
            self.citation_grounding,
            self.completeness,
            self.coherence,
        ]
        return sum(scores) / len(scores) if any(scores) else 0.0

    @property
    def min_score(self) -> int:
        return min(
            self.factual_accuracy,
            self.relevance,
            self.citation_grounding,
            self.completeness,
            self.coherence,
        )

    @property
    def passed(self) -> bool:
        return self.verdict.lower() == "pass"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["average_score"] = self.average_score
        d["min_score"] = self.min_score
        d["passed"] = self.passed
        return d


# ── Parsing logic ─────────────────────────────────────────────────────────

_SCORE_PATTERN = re.compile(
    r"(FACTUAL_ACCURACY|RELEVANCE|CITATION_GROUNDING|COMPLETENESS|COHERENCE)"
    r"\s*:\s*(\d)\s*/\s*5\s*\|\s*(.+)",
    re.IGNORECASE,
)
_VERDICT_PATTERN = re.compile(
    r"VERDICT\s*:\s*(PASS|FAIL)",
    re.IGNORECASE,
)

_DIM_MAP = {
    "FACTUAL_ACCURACY": "factual_accuracy",
    "RELEVANCE": "relevance",
    "CITATION_GROUNDING": "citation_grounding",
    "COMPLETENESS": "completeness",
    "COHERENCE": "coherence",
}


def _parse_judge_output(raw: str) -> JudgeResult:
    """Parse the structured judge output into a JudgeResult."""
    result = JudgeResult(raw_output=raw)

    for match in _SCORE_PATTERN.finditer(raw):
        dim_name = match.group(1).upper()
        score = int(match.group(2))
        justification = match.group(3).strip()
        attr = _DIM_MAP.get(dim_name)
        if attr:
            setattr(result, attr, score)
            result.justifications[dim_name] = justification

    verdict_match = _VERDICT_PATTERN.search(raw)
    if verdict_match:
        result.verdict = verdict_match.group(1).lower()
    else:
        # Derive verdict from scores if LLM didn't output one clearly
        if result.min_score >= 3 and result.average_score >= 3.5:
            result.verdict = "pass"
        else:
            result.verdict = "fail"

    return result


# ── Public API ────────────────────────────────────────────────────────────

def judge_synthesis(
    query: str,
    source_papers: str,
    synthesis: str,
    temperature: float = 0.0,
) -> JudgeResult:
    """Run the multi-dimensional judge on a single synthesis.

    Uses temperature=0 by default for maximum determinism.
    """
    llm = get_llm(temperature=temperature)
    chain = judge_prompt | llm
    response = chain.invoke({
        "query": query,
        "source_papers": source_papers,
        "synthesis": synthesis,
    })

    raw = response.content
    result = _parse_judge_output(raw)

    logger.info(
        "Judge: %s (avg=%.1f, min=%d) — %s",
        result.verdict.upper(),
        result.average_score,
        result.min_score,
        {k: v for k, v in result.justifications.items()},
    )

    return result
