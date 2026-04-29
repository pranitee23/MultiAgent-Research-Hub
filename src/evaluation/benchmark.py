"""
Nexus — Evaluation benchmark dataset.

Hand-crafted (query, sources, good_synthesis, bad_synthesis) pairs with known
verdicts. Used to measure true-positive, true-negative, false-positive, and
false-negative rates of the judge.

Each case is a dict with:
    query:             The user's research question
    source_papers:     Simulated retrieval output (titles + abstracts)
    synthesis:         The synthesis to evaluate
    expected_verdict:  "pass" or "fail"
    failure_mode:      Why a bad synthesis should fail (for diagnostics)
"""

# ---------------------------------------------------------------------------
# Source paper banks — reused across good and bad cases for the same query
# ---------------------------------------------------------------------------

_RAG_SOURCES = (
    "Title: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks\n"
    "Authors: Lewis et al.\n"
    "Year: 2020 | Citations: 4200\n"
    "Abstract: We explore a general-purpose fine-tuning recipe for retrieval-"
    "augmented generation (RAG). RAG models combine pre-trained parametric and "
    "non-parametric memory for language generation. We find that RAG models "
    "generate more specific, diverse, and factual text than state-of-the-art "
    "parametric-only seq2seq models. RAG achieves state-of-the-art results on "
    "open-domain QA, abstractive QA, and fact verification.\n"
    "URL: https://arxiv.org/abs/2005.11401\n"
    "\n---\n\n"
    "Title: Self-RAG: Learning to Retrieve, Generate, and Critique\n"
    "Authors: Asai et al.\n"
    "Year: 2023 | Citations: 890\n"
    "Abstract: We introduce Self-RAG, a framework that trains a single LM to "
    "adaptively retrieve passages on-demand, generate text informed by the "
    "retrieved passages, and critique its own output using special reflection "
    "tokens. Self-RAG significantly outperforms existing RAG approaches and "
    "ChatGPT on six tasks, improving factuality and citation accuracy.\n"
    "URL: https://arxiv.org/abs/2310.11511\n"
    "\n---\n\n"
    "Title: CRAG: Corrective Retrieval Augmented Generation\n"
    "Authors: Yan et al.\n"
    "Year: 2024 | Citations: 310\n"
    "Abstract: We propose CRAG, a method to improve the robustness of RAG by "
    "incorporating a lightweight retrieval evaluator that assesses the quality "
    "of retrieved documents and triggers corrective actions such as web search "
    "when low-confidence retrievals are detected. CRAG improves performance on "
    "short- and long-form generation tasks by 5-18%.\n"
    "URL: https://arxiv.org/abs/2401.15884"
)

_HALLUCINATION_SOURCES = (
    "Title: A Survey on Hallucination in Large Language Models\n"
    "Authors: Huang et al.\n"
    "Year: 2023 | Citations: 1500\n"
    "Abstract: This survey provides a comprehensive overview of LLM "
    "hallucination, categorizing it into factuality hallucination and "
    "faithfulness hallucination. We review over 30 mitigation strategies "
    "including retrieval augmentation, self-consistency decoding, and "
    "knowledge-grounded generation. We find no single method eliminates "
    "hallucination entirely.\n"
    "URL: https://arxiv.org/abs/2311.05232\n"
    "\n---\n\n"
    "Title: Chain-of-Verification Reduces Hallucination in LLMs\n"
    "Authors: Dhuliawala et al.\n"
    "Year: 2023 | Citations: 420\n"
    "Abstract: We present Chain-of-Verification (CoVe), where the model first "
    "drafts an initial response, then plans verification questions to fact-check "
    "its own output, and finally produces a revised response. CoVe reduces "
    "hallucination rates by 30-50% on list-based and long-form generation tasks "
    "compared to standard prompting.\n"
    "URL: https://arxiv.org/abs/2309.11495\n"
    "\n---\n\n"
    "Title: FActScore: Fine-grained Atomic Evaluation of Factual Precision\n"
    "Authors: Min et al.\n"
    "Year: 2023 | Citations: 680\n"
    "Abstract: We introduce FActScore, which breaks a generation into atomic "
    "facts and verifies each against a knowledge source. On biographies generated "
    "by ChatGPT, InstructGPT, and PerplexityAI, factual precision ranges from "
    "58% to 83%. FActScore correlates with human judgments at r=0.89.\n"
    "URL: https://arxiv.org/abs/2305.14251"
)

_VIT_SOURCES = (
    "Title: An Image is Worth 16x16 Words: Transformers for Image Recognition\n"
    "Authors: Dosovitskiy et al.\n"
    "Year: 2021 | Citations: 28000\n"
    "Abstract: We show that a pure transformer applied directly to sequences "
    "of image patches can perform very well on image classification. Vision "
    "Transformer (ViT) attains excellent results compared to state-of-the-art "
    "CNNs while requiring substantially fewer computational resources when "
    "pre-trained on large datasets.\n"
    "URL: https://arxiv.org/abs/2010.11929\n"
    "\n---\n\n"
    "Title: Medical Image Classification with Vision Transformers: A Survey\n"
    "Authors: Shamshad et al.\n"
    "Year: 2023 | Citations: 950\n"
    "Abstract: We survey over 100 papers applying ViTs to medical imaging "
    "tasks. ViTs outperform CNNs in data-rich settings (>50k images) but "
    "underperform when data is limited due to lack of inductive biases. "
    "Hybrid CNN-ViT models achieve the best overall accuracy on 7 of 12 "
    "benchmarks we evaluated.\n"
    "URL: https://arxiv.org/abs/2305.03000"
)

_FEDERATED_SOURCES = (
    "Title: Communication-Efficient Learning of Deep Networks\n"
    "Authors: McMahan et al.\n"
    "Year: 2017 | Citations: 12000\n"
    "Abstract: We propose Federated Averaging (FedAvg), a practical method "
    "for training deep networks on decentralized data. FedAvg reduces "
    "communication rounds by 10-100x compared to synchronized SGD. "
    "We show results on MNIST, CIFAR-10, and a language modeling task.\n"
    "URL: https://arxiv.org/abs/1602.05629\n"
    "\n---\n\n"
    "Title: Federated Learning Challenges in Healthcare: A Systematic Review\n"
    "Authors: Rieke et al.\n"
    "Year: 2020 | Citations: 3800\n"
    "Abstract: We review federated learning applications in healthcare, "
    "identifying key challenges: non-IID data distributions across hospitals, "
    "differential privacy requirements under HIPAA/GDPR, communication "
    "overhead in cross-silo settings, and model heterogeneity. Privacy-"
    "preserving techniques add 15-40% training overhead.\n"
    "URL: https://arxiv.org/abs/2006.07850\n"
    "\n---\n\n"
    "Title: FedProx: Heterogeneous Federated Optimization\n"
    "Authors: Li et al.\n"
    "Year: 2020 | Citations: 4500\n"
    "Abstract: We propose FedProx, which addresses statistical heterogeneity "
    "in federated networks by adding a proximal term to the local objective. "
    "FedProx demonstrates more stable and faster convergence than FedAvg on "
    "non-IID partitions, with up to 22% accuracy improvement on heterogeneous "
    "data distributions.\n"
    "URL: https://arxiv.org/abs/1812.06127"
)

_RLHF_SOURCES = (
    "Title: Training Language Models to Follow Instructions with Human Feedback\n"
    "Authors: Ouyang et al.\n"
    "Year: 2022 | Citations: 9500\n"
    "Abstract: We train InstructGPT using RLHF — collecting human comparisons "
    "to train a reward model, then optimizing a policy via PPO. The resulting "
    "1.3B parameter model outputs are preferred over the 175B GPT-3 outputs "
    "on 85% of prompts. RLHF reduces toxicity and hallucination.\n"
    "URL: https://arxiv.org/abs/2203.02155\n"
    "\n---\n\n"
    "Title: Direct Preference Optimization: Your Language Model is a Reward Model\n"
    "Authors: Rafailov et al.\n"
    "Year: 2023 | Citations: 3200\n"
    "Abstract: We introduce DPO, which directly optimizes a policy from "
    "preference data without fitting an explicit reward model or using RL. "
    "DPO is simpler, more stable, and computationally lighter than RLHF-PPO "
    "while achieving comparable or superior performance on summarization and "
    "dialogue tasks.\n"
    "URL: https://arxiv.org/abs/2305.18290\n"
    "\n---\n\n"
    "Title: KTO: Model Alignment as Prospect Theoretic Optimization\n"
    "Authors: Ethayarajh et al.\n"
    "Year: 2024 | Citations: 280\n"
    "Abstract: We propose KTO, which aligns models using only binary feedback "
    "(good/bad) instead of pairwise preferences. KTO matches or exceeds DPO "
    "performance on 1B-30B parameter models while requiring half the annotation "
    "effort. We show losses in the DPO family implicitly model human loss "
    "aversion.\n"
    "URL: https://arxiv.org/abs/2402.01306"
)

_AGENT_SOURCES = (
    "Title: ReAct: Synergizing Reasoning and Acting in Language Models\n"
    "Authors: Yao et al.\n"
    "Year: 2023 | Citations: 2800\n"
    "Abstract: We propose ReAct, which interleaves chain-of-thought reasoning "
    "with environment actions. ReAct overcomes issues of hallucination and error "
    "propagation in chain-of-thought by grounding reasoning in actions and "
    "observations, achieving state-of-the-art on HotpotQA and ALFWorld.\n"
    "URL: https://arxiv.org/abs/2210.03629\n"
    "\n---\n\n"
    "Title: Voyager: An Open-Ended Embodied Agent with LLMs\n"
    "Authors: Wang et al.\n"
    "Year: 2023 | Citations: 1100\n"
    "Abstract: We introduce Voyager, the first LLM-powered embodied lifelong "
    "learning agent in Minecraft. Voyager builds a skill library, uses "
    "curriculum-driven exploration, and iterative prompting. It obtains 3.3x "
    "more unique items than prior SOTA agents without any parameter updates.\n"
    "URL: https://arxiv.org/abs/2305.16291\n"
    "\n---\n\n"
    "Title: AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation\n"
    "Authors: Wu et al.\n"
    "Year: 2023 | Citations: 1800\n"
    "Abstract: We present AutoGen, a framework for building multi-agent "
    "conversational systems. AutoGen agents are customizable, conversable, and "
    "can operate in various modes combining LLMs, human inputs, and tools. "
    "We demonstrate effectiveness on math, coding, and decision-making tasks.\n"
    "URL: https://arxiv.org/abs/2308.08155"
)

# ---------------------------------------------------------------------------
# Benchmark cases
# ---------------------------------------------------------------------------

BENCHMARK_CASES: list[dict] = [
    # ── CASE 1: RAG — Good synthesis (should PASS) ───────────────────────
    {
        "id": "rag_good",
        "query": "What is retrieval augmented generation and how has it evolved?",
        "source_papers": _RAG_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Retrieval-Augmented Generation (RAG) combines parametric LLM memory "
            "with non-parametric retrieval to improve factual accuracy. Lewis et al. "
            "(2020) showed RAG achieves state-of-the-art on open-domain QA and fact "
            "verification by conditioning generation on retrieved passages.\n\n"
            "### Consensus\n"
            "All three papers agree that grounding generation in retrieved documents "
            "reduces hallucination. Self-RAG (Asai et al., 2023) extends this by "
            "training the model to decide when to retrieve and to self-critique via "
            "reflection tokens, improving factuality and citation accuracy.\n\n"
            "### Contradictions\n"
            "No direct contradictions were found, though the approaches differ in "
            "mechanism: Lewis et al. use retrieval at every step, while Self-RAG "
            "retrieves adaptively on-demand.\n\n"
            "### Knowledge gaps\n"
            "CRAG (Yan et al., 2024) identifies that standard RAG is brittle when "
            "retrieved documents are low quality, proposing corrective actions that "
            "improve performance by 5-18%. The gap between retrieval quality and "
            "generation quality remains underexplored.\n\n"
            "### Sources\n"
            "- Lewis et al. (2020) — Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks\n"
            "- Asai et al. (2023) — Self-RAG: Learning to Retrieve, Generate, and Critique\n"
            "- Yan et al. (2024) — CRAG: Corrective Retrieval Augmented Generation"
        ),
        "expected_verdict": "pass",
        "failure_mode": None,
    },

    # ── CASE 2: RAG — Fabricated claims (should FAIL) ────────────────────
    {
        "id": "rag_fabricated",
        "query": "What is retrieval augmented generation and how has it evolved?",
        "source_papers": _RAG_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "RAG was invented by OpenAI in 2022 as part of the GPT-4 training pipeline. "
            "It uses convolutional neural networks to encode documents before retrieval. "
            "RAG eliminates hallucination entirely, achieving 100% factual accuracy on "
            "all benchmarks tested.\n\n"
            "### Consensus\n"
            "All researchers agree RAG has solved the hallucination problem completely.\n\n"
            "### Contradictions\n"
            "None — the field is in full agreement.\n\n"
            "### Knowledge gaps\n"
            "There are no remaining knowledge gaps in RAG research.\n\n"
            "### Sources\n"
            "- OpenAI (2022) — RAG Technical Report"
        ),
        "expected_verdict": "fail",
        "failure_mode": "fabricated_claims",
    },

    # ── CASE 3: RAG — Off-topic (should FAIL) ───────────────────────────
    {
        "id": "rag_offtopic",
        "query": "What is retrieval augmented generation and how has it evolved?",
        "source_papers": _RAG_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Convolutional neural networks have been the backbone of computer vision "
            "since AlexNet (2012). ResNet introduced skip connections enabling training "
            "of 150+ layer networks. EfficientNet uses compound scaling to balance "
            "width, depth, and resolution.\n\n"
            "### Consensus\n"
            "All papers agree CNNs are effective for image classification.\n\n"
            "### Contradictions\n"
            "None identified in the CNN literature.\n\n"
            "### Knowledge gaps\n"
            "More work is needed on CNN efficiency for edge devices.\n\n"
            "### Sources\n"
            "- Krizhevsky et al. (2012) — ImageNet Classification with Deep CNNs"
        ),
        "expected_verdict": "fail",
        "failure_mode": "off_topic",
    },

    # ── CASE 4: Hallucination — Good synthesis (should PASS) ─────────────
    {
        "id": "hallucination_good",
        "query": "What are the latest approaches to reducing hallucination in LLMs?",
        "source_papers": _HALLUCINATION_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Huang et al. (2023) categorize LLM hallucination into factuality "
            "hallucination (generating false facts) and faithfulness hallucination "
            "(deviating from source context). They review 30+ mitigation strategies "
            "and conclude no single method eliminates hallucination entirely.\n\n"
            "### Consensus\n"
            "Both Huang et al. and Dhuliawala et al. (2023) agree that verification-"
            "based approaches are promising. Chain-of-Verification (CoVe) reduces "
            "hallucination rates by 30-50% through self-planned verification questions.\n\n"
            "### Contradictions\n"
            "No direct contradictions, though Huang et al. emphasize breadth of "
            "strategies while CoVe focuses on a single self-verification mechanism.\n\n"
            "### Knowledge gaps\n"
            "FActScore (Min et al., 2023) reveals that even ChatGPT achieves only "
            "58-83% factual precision on biographies, highlighting that fine-grained "
            "evaluation of atomic facts remains an open challenge. The correlation "
            "with human judgment (r=0.89) suggests automated evaluation is viable "
            "but imperfect.\n\n"
            "### Sources\n"
            "- Huang et al. (2023) — A Survey on Hallucination in Large Language Models\n"
            "- Dhuliawala et al. (2023) — Chain-of-Verification Reduces Hallucination\n"
            "- Min et al. (2023) — FActScore: Fine-grained Atomic Evaluation"
        ),
        "expected_verdict": "pass",
        "failure_mode": None,
    },

    # ── CASE 5: Hallucination — Misrepresented findings (should FAIL) ────
    {
        "id": "hallucination_misrepresented",
        "query": "What are the latest approaches to reducing hallucination in LLMs?",
        "source_papers": _HALLUCINATION_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Huang et al. (2023) found that retrieval augmentation alone completely "
            "eliminates hallucination in LLMs. CoVe by Dhuliawala et al. (2023) "
            "reduces hallucination rates by 90-95% on all tasks tested.\n\n"
            "### Consensus\n"
            "The field has converged on retrieval augmentation as the definitive "
            "solution to hallucination.\n\n"
            "### Contradictions\n"
            "FActScore found ChatGPT achieves 98% factual precision, contradicting "
            "claims that hallucination is a problem.\n\n"
            "### Knowledge gaps\n"
            "None — hallucination is largely a solved problem.\n\n"
            "### Sources\n"
            "- Huang et al. (2023) — Hallucination Survey\n"
            "- Dhuliawala et al. (2023) — CoVe"
        ),
        "expected_verdict": "fail",
        "failure_mode": "misrepresented_findings",
    },

    # ── CASE 6: ViT — Good synthesis (should PASS) ──────────────────────
    {
        "id": "vit_good",
        "query": "How do vision transformers compare to CNNs for medical image classification?",
        "source_papers": _VIT_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Dosovitskiy et al. (2021) demonstrated that Vision Transformer (ViT), "
            "a pure transformer applied to 16x16 image patches, achieves excellent "
            "results compared to state-of-the-art CNNs when pre-trained on large "
            "datasets, while requiring fewer computational resources.\n\n"
            "### Consensus\n"
            "Both papers agree transformers can match or exceed CNN performance. "
            "Shamshad et al. (2023) surveyed 100+ papers and confirmed ViTs outperform "
            "CNNs in data-rich settings (>50k images).\n\n"
            "### Contradictions\n"
            "Shamshad et al. found ViTs underperform CNNs when data is limited, due to "
            "lack of inductive biases — a nuance not addressed in the original ViT paper.\n\n"
            "### Knowledge gaps\n"
            "Hybrid CNN-ViT models achieve the best accuracy on 7 of 12 medical imaging "
            "benchmarks (Shamshad et al., 2023), suggesting neither pure architecture "
            "dominates. Optimal hybridization strategies remain underexplored.\n\n"
            "### Sources\n"
            "- Dosovitskiy et al. (2021) — An Image is Worth 16x16 Words\n"
            "- Shamshad et al. (2023) — Medical Image Classification with Vision Transformers"
        ),
        "expected_verdict": "pass",
        "failure_mode": None,
    },

    # ── CASE 7: ViT — Partially correct with hallucinated stat (should FAIL)
    {
        "id": "vit_partial_hallucination",
        "query": "How do vision transformers compare to CNNs for medical image classification?",
        "source_papers": _VIT_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Vision Transformers (Dosovitskiy et al., 2021) process images as 16x16 "
            "patches and achieve state-of-the-art results. ViTs achieve 99.2% accuracy "
            "on all medical imaging tasks, making them strictly superior to CNNs in "
            "every clinical setting.\n\n"
            "### Consensus\n"
            "All researchers agree ViTs have completely replaced CNNs in medical imaging.\n\n"
            "### Contradictions\n"
            "None found.\n\n"
            "### Knowledge gaps\n"
            "None — ViTs are the definitive solution for medical imaging.\n\n"
            "### Sources\n"
            "- Dosovitskiy et al. (2021) — ViT paper"
        ),
        "expected_verdict": "fail",
        "failure_mode": "hallucinated_statistics",
    },

    # ── CASE 8: Federated Learning — Good synthesis (should PASS) ────────
    {
        "id": "federated_good",
        "query": "What is federated learning and what are the main challenges in healthcare?",
        "source_papers": _FEDERATED_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Federated learning enables training deep networks on decentralized data "
            "without centralizing it. McMahan et al. (2017) proposed FedAvg, which "
            "reduces communication rounds by 10-100x compared to synchronized SGD.\n\n"
            "### Consensus\n"
            "All papers agree that data heterogeneity is a core challenge. Rieke et al. "
            "(2020) identify non-IID distributions, differential privacy (HIPAA/GDPR), "
            "communication overhead, and model heterogeneity as key obstacles. Li et al. "
            "(2020) address heterogeneity specifically via FedProx's proximal term, "
            "achieving up to 22% accuracy improvement on non-IID data.\n\n"
            "### Contradictions\n"
            "FedAvg assumes relatively homogeneous local updates, while FedProx shows "
            "this assumption fails on heterogeneous data — motivating the proximal "
            "regularization term.\n\n"
            "### Knowledge gaps\n"
            "Privacy-preserving techniques add 15-40% training overhead (Rieke et al., "
            "2020). Balancing privacy guarantees with computational efficiency remains "
            "an open problem in clinical deployment.\n\n"
            "### Sources\n"
            "- McMahan et al. (2017) — Communication-Efficient Learning of Deep Networks\n"
            "- Rieke et al. (2020) — Federated Learning Challenges in Healthcare\n"
            "- Li et al. (2020) — FedProx: Heterogeneous Federated Optimization"
        ),
        "expected_verdict": "pass",
        "failure_mode": None,
    },

    # ── CASE 9: Federated — Missing key findings (should FAIL) ──────────
    {
        "id": "federated_incomplete",
        "query": "What is federated learning and what are the main challenges in healthcare?",
        "source_papers": _FEDERATED_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Federated learning is a machine learning technique.\n\n"
            "### Consensus\n"
            "It is useful.\n\n"
            "### Contradictions\n"
            "None.\n\n"
            "### Knowledge gaps\n"
            "More research is needed.\n\n"
            "### Sources\n"
            "- McMahan et al. (2017)"
        ),
        "expected_verdict": "fail",
        "failure_mode": "incomplete_superficial",
    },

    # ── CASE 10: RLHF/DPO — Good synthesis (should PASS) ────────────────
    {
        "id": "rlhf_good",
        "query": "How does RLHF compare to DPO for LLM alignment?",
        "source_papers": _RLHF_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "RLHF (Ouyang et al., 2022) trains a reward model from human comparisons "
            "then optimizes a policy via PPO. The resulting 1.3B InstructGPT is "
            "preferred over 175B GPT-3 on 85% of prompts. DPO (Rafailov et al., 2023) "
            "bypasses the reward model entirely, directly optimizing from preference data "
            "with comparable or superior results.\n\n"
            "### Consensus\n"
            "All three papers agree that human preference data is essential for alignment. "
            "KTO (Ethayarajh et al., 2024) further simplifies this to binary good/bad "
            "feedback, matching DPO while requiring half the annotation effort.\n\n"
            "### Contradictions\n"
            "RLHF requires training a separate reward model and running PPO (complex, "
            "unstable), while DPO achieves similar results without RL — challenging the "
            "necessity of explicit reward modeling.\n\n"
            "### Knowledge gaps\n"
            "KTO shows DPO-family losses implicitly model human loss aversion, opening "
            "questions about whether alignment objectives should be designed around "
            "cognitive biases. Scaling behavior of DPO vs. RLHF beyond 30B parameters "
            "is not yet studied.\n\n"
            "### Sources\n"
            "- Ouyang et al. (2022) — Training LMs to Follow Instructions with Human Feedback\n"
            "- Rafailov et al. (2023) — Direct Preference Optimization\n"
            "- Ethayarajh et al. (2024) — KTO: Model Alignment as Prospect Theoretic Optimization"
        ),
        "expected_verdict": "pass",
        "failure_mode": None,
    },

    # ── CASE 11: RLHF/DPO — Inverted claims (should FAIL) ──────────────
    {
        "id": "rlhf_inverted",
        "query": "How does RLHF compare to DPO for LLM alignment?",
        "source_papers": _RLHF_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "DPO (Rafailov et al., 2023) is more complex than RLHF, requiring both a "
            "reward model and PPO optimization. RLHF (Ouyang et al., 2022) is the simpler "
            "method that directly optimizes from preferences without reinforcement learning. "
            "KTO requires 3x more annotation effort than DPO.\n\n"
            "### Consensus\n"
            "Researchers agree RLHF is simpler than DPO.\n\n"
            "### Contradictions\n"
            "None found.\n\n"
            "### Knowledge gaps\n"
            "Whether DPO can work without a reward model is unknown.\n\n"
            "### Sources\n"
            "- Rafailov et al. (2023) — DPO\n"
            "- Ouyang et al. (2022) — RLHF"
        ),
        "expected_verdict": "fail",
        "failure_mode": "inverted_claims",
    },

    # ── CASE 12: AI Agents — Good synthesis (should PASS) ────────────────
    {
        "id": "agents_good",
        "query": "What are the latest developments in AI agents and multi-agent systems?",
        "source_papers": _AGENT_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "ReAct (Yao et al., 2023) interleaves chain-of-thought reasoning with "
            "environment actions, achieving state-of-the-art on HotpotQA and ALFWorld "
            "by grounding reasoning in observations. Voyager (Wang et al., 2023) "
            "demonstrates lifelong learning in Minecraft, building a skill library and "
            "obtaining 3.3x more unique items than prior SOTA without parameter updates.\n\n"
            "### Consensus\n"
            "All papers agree that LLMs can serve as effective controllers for autonomous "
            "agents. AutoGen (Wu et al., 2023) enables multi-agent conversation combining "
            "LLMs, human inputs, and tools for math, coding, and decision-making tasks.\n\n"
            "### Contradictions\n"
            "ReAct uses a single agent with interleaved reasoning, while AutoGen "
            "emphasizes multi-agent collaboration — suggesting the field is still debating "
            "whether single or multi-agent approaches are more effective.\n\n"
            "### Knowledge gaps\n"
            "None of the papers address long-term safety or alignment of autonomous "
            "agents. Voyager's skill library approach is tested only in Minecraft — "
            "transferability to real-world tasks is unexplored.\n\n"
            "### Sources\n"
            "- Yao et al. (2023) — ReAct: Synergizing Reasoning and Acting\n"
            "- Wang et al. (2023) — Voyager: Open-Ended Embodied Agent with LLMs\n"
            "- Wu et al. (2023) — AutoGen: Multi-Agent Conversation Framework"
        ),
        "expected_verdict": "pass",
        "failure_mode": None,
    },

    # ── CASE 13: AI Agents — No citations (should FAIL) ─────────────────
    {
        "id": "agents_no_citations",
        "query": "What are the latest developments in AI agents and multi-agent systems?",
        "source_papers": _AGENT_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "AI agents are becoming increasingly capable. Recent work shows that LLMs "
            "can reason and act in environments. Some agents can learn continuously "
            "without retraining. Multi-agent systems allow agents to collaborate.\n\n"
            "### Consensus\n"
            "Everyone agrees AI agents are powerful and useful.\n\n"
            "### Contradictions\n"
            "There are no major disagreements in the field.\n\n"
            "### Knowledge gaps\n"
            "Safety and alignment need more work.\n\n"
            "### Sources\n"
            "- Various papers on AI agents"
        ),
        "expected_verdict": "fail",
        "failure_mode": "missing_citations",
    },

    # ── CASE 14: Hallucination — Correct but unusual phrasing (should PASS)
    {
        "id": "hallucination_unusual_phrasing",
        "query": "What are the latest approaches to reducing hallucination in LLMs?",
        "source_papers": _HALLUCINATION_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "The hallucination problem in large language models breaks down into two "
            "categories according to the comprehensive survey by Huang and colleagues "
            "from 2023: making up facts that are wrong (factuality hallucination) and "
            "straying from what the input said (faithfulness hallucination). Their review "
            "of more than thirty different fixes found that nothing works perfectly.\n\n"
            "### Consensus\n"
            "A self-checking approach called CoVe, published by Dhuliawala's team in "
            "2023, cut hallucination by roughly a third to a half. The model asks itself "
            "verification questions about its own draft, then revises. This aligns with "
            "Huang et al.'s finding that verification-based methods are among the most "
            "promising directions.\n\n"
            "### Contradictions\n"
            "While Huang et al. survey many strategies at a high level, CoVe focuses "
            "deeply on one technique — these are complementary rather than contradictory.\n\n"
            "### Knowledge gaps\n"
            "Min et al. (2023) built FActScore to measure factual precision at the level "
            "of individual atomic facts. They found even the best models (ChatGPT, etc.) "
            "top out around 83% on biographies. The 0.89 correlation with human ratings "
            "is encouraging but not perfect — better automated evaluation is needed.\n\n"
            "### Sources\n"
            "- Huang et al. (2023) — A Survey on Hallucination in Large Language Models\n"
            "- Dhuliawala et al. (2023) — Chain-of-Verification Reduces Hallucination in LLMs\n"
            "- Min et al. (2023) — FActScore: Fine-grained Atomic Evaluation of Factual Precision"
        ),
        "expected_verdict": "pass",
        "failure_mode": None,
    },

    # ── CASE 15: Federated — Correct facts, wrong query (should FAIL) ───
    {
        "id": "federated_wrong_query",
        "query": "What is federated learning and what are the main challenges in healthcare?",
        "source_papers": _FEDERATED_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "McMahan et al. (2017) proposed FedAvg which reduces communication rounds "
            "by 10-100x. FedProx (Li et al., 2020) adds a proximal term achieving 22% "
            "accuracy gains on non-IID data.\n\n"
            "### Consensus\n"
            "Both papers agree communication efficiency is important.\n\n"
            "### Contradictions\n"
            "FedAvg and FedProx differ on handling heterogeneity.\n\n"
            "### Knowledge gaps\n"
            "More efficient communication protocols are needed.\n\n"
            "### Sources\n"
            "- McMahan et al. (2017) — FedAvg\n"
            "- Li et al. (2020) — FedProx"
        ),
        "expected_verdict": "fail",
        "failure_mode": "ignores_healthcare_focus",
    },

    # ── CASE 16: RLHF — Good but minimal (borderline PASS) ─────────────
    {
        "id": "rlhf_minimal_pass",
        "query": "How does RLHF compare to DPO for LLM alignment?",
        "source_papers": _RLHF_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "RLHF (Ouyang et al., 2022) uses a reward model trained on human "
            "comparisons plus PPO optimization, producing a 1.3B model preferred "
            "over 175B GPT-3 on 85% of prompts. DPO (Rafailov et al., 2023) achieves "
            "comparable results without an explicit reward model or RL, making it "
            "simpler and more stable.\n\n"
            "### Consensus\n"
            "Both approaches rely on human preference data for alignment.\n\n"
            "### Contradictions\n"
            "RLHF requires a separate reward model; DPO questions whether that is "
            "necessary at all.\n\n"
            "### Knowledge gaps\n"
            "KTO (Ethayarajh et al., 2024) shows binary feedback can replace pairwise "
            "preferences, halving annotation cost. Scaling properties beyond 30B "
            "parameters remain unknown.\n\n"
            "### Sources\n"
            "- Ouyang et al. (2022) — InstructGPT / RLHF\n"
            "- Rafailov et al. (2023) — DPO\n"
            "- Ethayarajh et al. (2024) — KTO"
        ),
        "expected_verdict": "pass",
        "failure_mode": None,
    },

    # ── CASE 17: RAG — Mixes real and fabricated sources (should FAIL) ───
    {
        "id": "rag_mixed_fabrication",
        "query": "What is retrieval augmented generation and how has it evolved?",
        "source_papers": _RAG_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Lewis et al. (2020) introduced RAG combining retrieval with generation. "
            "Google's RAG-2 system (Chen et al., 2025) later achieved human-level "
            "performance on all knowledge tasks using a novel sparse-dense hybrid "
            "retriever. Self-RAG (Asai et al., 2023) adds adaptive retrieval.\n\n"
            "### Consensus\n"
            "All papers agree RAG is effective for reducing hallucination.\n\n"
            "### Contradictions\n"
            "RAG-2 claims to solve the problem while Self-RAG suggests more work "
            "is needed.\n\n"
            "### Knowledge gaps\n"
            "Integration of RAG with tool use remains underexplored.\n\n"
            "### Sources\n"
            "- Lewis et al. (2020) — RAG\n"
            "- Chen et al. (2025) — RAG-2\n"
            "- Asai et al. (2023) — Self-RAG"
        ),
        "expected_verdict": "fail",
        "failure_mode": "fabricated_source",
    },

    # ── CASE 18: ViT — Contradicts source but sounds confident (should FAIL)
    {
        "id": "vit_confident_wrong",
        "query": "How do vision transformers compare to CNNs for medical image classification?",
        "source_papers": _VIT_SOURCES,
        "synthesis": (
            "### Key findings\n"
            "Extensive research has conclusively demonstrated that CNNs are strictly "
            "superior to Vision Transformers in all medical imaging settings. "
            "Dosovitskiy et al. (2021) showed that ViTs require 10x more compute "
            "than CNNs and never surpass their accuracy. Shamshad et al. (2023) "
            "confirmed CNNs outperform ViTs on all 12 medical benchmarks.\n\n"
            "### Consensus\n"
            "The field unanimously recommends CNNs over ViTs for healthcare.\n\n"
            "### Contradictions\n"
            "None — results are consistent across all studies.\n\n"
            "### Knowledge gaps\n"
            "Whether ViTs have any use in medical imaging remains doubtful.\n\n"
            "### Sources\n"
            "- Dosovitskiy et al. (2021) — ViT paper\n"
            "- Shamshad et al. (2023) — Medical ViT Survey"
        ),
        "expected_verdict": "fail",
        "failure_mode": "contradicts_sources",
    },
]


def get_pass_cases() -> list[dict]:
    return [c for c in BENCHMARK_CASES if c["expected_verdict"] == "pass"]


def get_fail_cases() -> list[dict]:
    return [c for c in BENCHMARK_CASES if c["expected_verdict"] == "fail"]
