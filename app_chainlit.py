"""
Nexus — Multi-Agent Research Assistant
Run: chainlit run app.py
"""
import chainlit as cl
from src.core.graph import research_agent
from src.core.llm import get_llm, get_provider_info
import time
import logging

logger = logging.getLogger(__name__)

# ─── Fail fast if LLM config is broken ───────────────
try:
    _boot_llm = get_llm(temperature=0.0)
    logger.info("LLM provider validated at startup")
except ValueError as e:
    raise SystemExit(f"Startup failed — {e}") from e


# ─── Starter prompts on empty chat ────────────────────

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="LLM hallucination research",
            message="What are the latest approaches to reducing hallucination in large language models?",
            icon="/public/icons/brain.svg",
        ),
        cl.Starter(
            label="Compare transformer architectures",
            message="How do vision transformers compare to CNNs for medical image classification?",
            icon="/public/icons/compare.svg",
        ),
        cl.Starter(
            label="AI agents deep dive",
            message="What are the latest developments in AI agents and multi-agent systems in 2024-2026?",
            icon="/public/icons/agent.svg",
        ),
        cl.Starter(
            label="Federated learning in healthcare",
            message="What is federated learning and what are the main challenges of using it in healthcare?",
            icon="/public/icons/shield.svg",
        ),
    ]


# ─── Welcome message + avatars on chat start ──────────

@cl.on_chat_start
async def on_start():
    info = get_provider_info()
    welcome = (
        "**Welcome to Nexus** — your multi-agent research assistant.\n\n"
        "Ask me any complex research question and I'll deploy "
        "**4 specialized AI agents** to:\n\n"
        "| Agent | Role |\n"
        "|-------|------|\n"
        "| 🎯 Planner | Break your question into focused sub-queries |\n"
        "| 🔍 Retriever | Search arXiv + Semantic Scholar in parallel |\n"
        "| 📝 Synthesizer | Build a structured summary with citations |\n"
        "| 🔎 Critic | Fact-check every claim against sources |\n\n"
        f"*Running on `{info['model']}` via {info['provider'].title()} — "
        f"{info['cost']}*"
    )
    await cl.Message(content=welcome, author="Nexus").send()
    # #region agent log
    import json as _json, time as _time; open("debug-4a2b3a.log","a").write(_json.dumps({"sessionId":"4a2b3a","hypothesisId":"H1-fix","location":"app.py:on_start","message":"welcome sent ok","timestamp":int(_time.time()*1000)})+"\n")
    # #endregion


# ─── Agent step config ─────────────────────────────────

AGENT_CONFIG = {
    "planner": {
        "label": "Planner",
        "author": "Planner",
        "icon": "🎯",
        "msg": "Breaking down your question into focused sub-queries...",
    },
    "retriever": {
        "label": "Retriever",
        "author": "Retriever",
        "icon": "🔍",
        "msg": "Searching arXiv and Semantic Scholar for papers...",
    },
    "synthesizer": {
        "label": "Synthesizer",
        "author": "Synthesizer",
        "icon": "📝",
        "msg": "Building structured research summary with citations...",
    },
    "critic": {
        "label": "Critic",
        "author": "Critic",
        "icon": "🔎",
        "msg": "Fact-checking claims against source papers...",
    },
    "format_answer": {
        "label": "Formatter",
        "author": "Nexus",
        "icon": "✅",
        "msg": "Packaging your verified research summary...",
    },
}


# ─── Helper: format planner output ────────────────────

def _format_planner_output(sub_qs: list[str]) -> str:
    if not sub_qs:
        return "No sub-questions generated."
    lines = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(sub_qs))
    return f"**Decomposed into {len(sub_qs)} sub-questions:**\n{lines}"


# ─── Helper: format retriever output ──────────────────

def _format_retriever_output(papers: dict) -> str:
    total_papers = 0
    for text in papers.values():
        total_papers += text.count("Title:")
    return (
        f"**Retrieved {total_papers} papers** across "
        f"{len(papers)} sub-questions from arXiv + Semantic Scholar"
    )


# ─── Helper: format critic output ─────────────────────

def _format_critic_output(node_data: dict) -> str:
    passed = node_data.get("critique_passed", False)
    rev = node_data.get("revision_count", 0)
    critique = node_data.get("critique", "")

    if passed:
        verdict_line = "**Verdict:** ✅ PASS — All claims verified against sources"
    else:
        verdict_line = f"**Verdict:** ⚠️ NEEDS REVISION — Revision {rev}/2"

    output = verdict_line
    if critique and not passed:
        short_critique = critique[:300].replace("\n", " ")
        output += f"\n\n> {short_critique}..."

    return output


# ─── Helper: build final answer with expandable sections

def _build_final_message(final_answer: str, elapsed: float, step_count: int, critique_passed: bool) -> str:
    quality_text = "✅ Verified" if critique_passed else "⚠️ Best Effort"

    footer = (
        f"\n\n---\n"
        f"*{quality_text} · {elapsed:.1f}s · {step_count} agent steps*"
    )

    return final_answer + footer


# ─── Handle user messages ──────────────────────────────

@cl.on_message
async def main(message: cl.Message):
    start_time = time.time()
    query = message.content

    initial_state = {
        "query": query,
        "sub_questions": [],
        "retrieved_papers": {},
        "synthesis": "",
        "critique": "",
        "critique_passed": False,
        "revision_count": 0,
        "messages": [],
        "final_answer": "",
    }

    final_answer = ""
    critique_passed = False
    step_count = 0

    async for step in research_agent.astream(initial_state):
        node_name = list(step.keys())[0]
        node_data = step[node_name]

        if node_name in AGENT_CONFIG:
            config = AGENT_CONFIG[node_name]
            step_count += 1

            async with cl.Step(
                name=f"{config['icon']} {config['label']}",
            ) as agent_step:
                agent_step.output = config["msg"]

                if node_name == "planner" and "sub_questions" in node_data:
                    agent_step.output = _format_planner_output(
                        node_data["sub_questions"]
                    )

                elif node_name == "retriever" and "retrieved_papers" in node_data:
                    agent_step.output = _format_retriever_output(
                        node_data["retrieved_papers"]
                    )

                elif node_name == "critic":
                    agent_step.output = _format_critic_output(node_data)
                    critique_passed = node_data.get("critique_passed", False)

        if "final_answer" in node_data:
            final_answer = node_data["final_answer"]

        # #region agent log
        import json as _json, time as _time; open("debug-4a2b3a.log","a").write(_json.dumps({"sessionId":"4a2b3a","hypothesisId":"H2-timing","location":"app.py:astream","message":f"node {node_name} done","data":{"node":node_name,"elapsed_so_far":round(time.time()-start_time,1)},"timestamp":int(_time.time()*1000)})+"\n")
        # #endregion

    elapsed = time.time() - start_time
    content = _build_final_message(
        final_answer or "Could not generate a research summary.",
        elapsed,
        step_count,
        critique_passed,
    )

    await cl.Message(
        content=content,
        author="Nexus",
    ).send()
    # #region agent log
    import json as _json, time as _time; open("debug-4a2b3a.log","a").write(_json.dumps({"sessionId":"4a2b3a","hypothesisId":"H1-final","location":"app.py:main","message":"final msg sent ok","data":{"elapsed":round(elapsed,1),"steps":step_count},"timestamp":int(_time.time()*1000)})+"\n")
    # #endregion
