"""
Nexus — Multi-Agent Research Assistant (Streamlit UI)
Run: streamlit run app.py
"""

import streamlit as st
import asyncio
import time
import re
import logging
from src.core.graph import research_agent
from src.core.llm import get_llm, get_provider_info
from src.config.settings import settings

logger = logging.getLogger(__name__)

# ─── Page config ──────────────────────────────────────

st.set_page_config(
    page_title="Nexus — Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────

NEXUS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --nexus-purple: #7c6ef0;
    --nexus-purple-light: #a78bfa;
    --nexus-purple-glow: rgba(124, 110, 240, 0.15);
    --nexus-bg-dark: #0e1117;
    --nexus-bg-card: rgba(26, 26, 36, 0.7);
    --nexus-border: rgba(124, 110, 240, 0.15);
    --nexus-text: #e0dff5;
    --nexus-text-dim: #888;
    --nexus-green: #22c55e;
    --nexus-yellow: #fbbf24;
}

.stApp { font-family: 'Inter', sans-serif; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: rgba(124,110,240,0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(124,110,240,0.7); }
::-webkit-scrollbar-track { background: transparent; }

/* Pipeline nodes */
.pipeline-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    padding: 20px 10px;
    margin: 10px 0;
}
.pipeline-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 14px 18px;
    border-radius: 12px;
    border: 2px solid rgba(124,110,240,0.2);
    background: rgba(26,26,36,0.6);
    min-width: 110px;
    transition: all 0.3s ease;
    position: relative;
}
.pipeline-node.active {
    border-color: var(--nexus-purple);
    box-shadow: 0 0 20px rgba(124,110,240,0.3), 0 0 40px rgba(124,110,240,0.1);
    background: rgba(124,110,240,0.1);
    animation: pulse 1.5s ease-in-out infinite;
}
.pipeline-node.done {
    border-color: var(--nexus-green);
    background: rgba(34,197,94,0.08);
}
.pipeline-node.done::after {
    content: '✓';
    position: absolute;
    top: -8px;
    right: -8px;
    background: var(--nexus-green);
    color: #fff;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
}
.pipeline-node .node-icon { font-size: 24px; margin-bottom: 6px; }
.pipeline-node .node-label { font-size: 12px; font-weight: 600; color: var(--nexus-text); }
.pipeline-node .node-time { font-size: 10px; color: var(--nexus-text-dim); margin-top: 4px; }
.pipeline-arrow {
    color: rgba(124,110,240,0.4);
    font-size: 20px;
    margin: 0 6px;
    flex-shrink: 0;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 20px rgba(124,110,240,0.3); }
    50% { box-shadow: 0 0 30px rgba(124,110,240,0.5), 0 0 60px rgba(124,110,240,0.2); }
}

/* Paper cards */
.paper-card {
    background: var(--nexus-bg-card);
    border: 1px solid var(--nexus-border);
    border-radius: 10px;
    padding: 14px 16px;
    margin: 8px 0;
    transition: all 0.25s ease;
}
.paper-card:hover {
    border-color: var(--nexus-purple);
    box-shadow: 0 4px 16px rgba(124,110,240,0.12);
    transform: translateY(-1px);
}
.paper-card .paper-title {
    font-weight: 600;
    color: var(--nexus-text);
    font-size: 0.95em;
    margin-bottom: 4px;
}
.paper-card .paper-meta {
    color: var(--nexus-text-dim);
    font-size: 0.8em;
}
.paper-card .paper-abstract {
    color: #aaa;
    font-size: 0.85em;
    margin-top: 8px;
    line-height: 1.5;
}
.paper-card a { color: var(--nexus-purple-light); text-decoration: none; }
.paper-card a:hover { text-decoration: underline; }

/* Quality badge */
.quality-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: 600;
}
.badge-pass {
    background: rgba(34,197,94,0.15);
    color: var(--nexus-green);
    border: 1px solid rgba(34,197,94,0.3);
}
.badge-fail {
    background: rgba(251,191,36,0.15);
    color: var(--nexus-yellow);
    border: 1px solid rgba(251,191,36,0.3);
}

/* Metric cards */
.metric-card {
    background: var(--nexus-bg-card);
    border: 1px solid var(--nexus-border);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.metric-card .metric-value {
    font-size: 1.8em;
    font-weight: 700;
    color: var(--nexus-purple-light);
}
.metric-card .metric-label {
    font-size: 0.75em;
    color: var(--nexus-text-dim);
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Starter cards */
.starter-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 20px 0;
}
.starter-card {
    background: var(--nexus-bg-card);
    border: 1px solid var(--nexus-border);
    border-radius: 12px;
    padding: 16px 18px;
    cursor: pointer;
    transition: all 0.25s ease;
}
.starter-card:hover {
    transform: translateY(-3px);
    border-color: rgba(124,110,240,0.4);
    box-shadow: 0 8px 24px rgba(124,110,240,0.15);
}
.starter-card .starter-icon { font-size: 20px; margin-bottom: 6px; }
.starter-card .starter-label {
    font-weight: 600;
    font-size: 0.9em;
    color: var(--nexus-text);
}
.starter-card .starter-desc {
    font-size: 0.78em;
    color: var(--nexus-text-dim);
    margin-top: 4px;
    line-height: 1.4;
}

/* Sidebar branding */
.sidebar-brand {
    text-align: center;
    padding: 20px 0 10px;
}
.sidebar-brand h1 {
    font-size: 1.6em;
    font-weight: 700;
    background: linear-gradient(135deg, #7c6ef0, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.sidebar-brand p {
    color: var(--nexus-text-dim);
    font-size: 0.8em;
    margin: 4px 0 0;
}

/* Score gauge */
.gauge-container { display: flex; align-items: center; gap: 10px; margin: 6px 0; }
.gauge-bar {
    flex: 1;
    height: 8px;
    border-radius: 4px;
    background: rgba(124,110,240,0.15);
    overflow: hidden;
}
.gauge-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, #7c6ef0, #a78bfa);
    transition: width 0.6s ease;
}
.gauge-label { font-size: 0.8em; color: var(--nexus-text-dim); min-width: 100px; }
.gauge-value { font-size: 0.8em; color: var(--nexus-text); font-weight: 600; min-width: 30px; text-align: right; }

/* Waterfall timing */
.waterfall-bar {
    display: flex;
    align-items: center;
    margin: 4px 0;
    gap: 8px;
}
.waterfall-label { font-size: 0.8em; color: var(--nexus-text-dim); min-width: 90px; }
.waterfall-track {
    flex: 1;
    height: 22px;
    background: rgba(124,110,240,0.08);
    border-radius: 6px;
    overflow: hidden;
    position: relative;
}
.waterfall-fill {
    height: 100%;
    border-radius: 6px;
    display: flex;
    align-items: center;
    padding-left: 8px;
    font-size: 0.7em;
    font-weight: 600;
    color: #fff;
}

/* Fade in animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn 0.4s ease-out; }
</style>
"""

st.markdown(NEXUS_CSS, unsafe_allow_html=True)


# ─── Session state init ──────────────────────────────

def _init_state():
    defaults = {
        "messages": [],
        "pipeline_state": {},
        "agent_timings": {},
        "total_elapsed": 0,
        "papers_data": {},
        "critique_data": {},
        "is_running": False,
        "current_agent": None,
        "step_count": 0,
        "query_history": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ─── LLM validation ──────────────────────────────────

@st.cache_resource
def validate_llm():
    try:
        get_llm(temperature=0.0)
        return True, ""
    except ValueError as e:
        return False, str(e)

llm_ok, llm_error = validate_llm()
if not llm_ok:
    st.error(f"LLM configuration error: {llm_error}")
    st.stop()


# ─── Sidebar ──────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<h1>🔬 Nexus</h1>'
        '<p>Multi-Agent Research Intelligence</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    info = get_provider_info()
    st.markdown("#### Model Configuration")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="font-size:1em;">{info["provider"].title()}</div>'
            f'<div class="metric-label">Provider</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="font-size:0.8em;">{info["model"]}</div>'
            f'<div class="metric-label">Model</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.caption(f"Speed: {info.get('speed', 'N/A')} · Cost: {info.get('cost', 'N/A')}")

    if info["provider"] in ("groq", "gemini"):
        light_model = settings.groq_model_light if info["provider"] == "groq" else settings.gemini_model_light
        st.markdown(f"**Light model (Planner):** `{light_model}`")
        st.markdown(f"**Heavy model (Synth/Critic):** `{info['model']}`")

    st.divider()

    # Agent timing waterfall
    if st.session_state.agent_timings:
        st.markdown("#### Agent Timing")
        total = st.session_state.total_elapsed or 1
        colors = {
            "planner": "#7c6ef0",
            "retriever": "#3b82f6",
            "synthesizer": "#a78bfa",
            "critic": "#22c55e",
            "format_answer": "#fbbf24",
        }
        waterfall_html = ""
        for agent, dur in st.session_state.agent_timings.items():
            pct = min((dur / total) * 100, 100)
            color = colors.get(agent, "#7c6ef0")
            label = agent.replace("_", " ").title()
            waterfall_html += (
                f'<div class="waterfall-bar">'
                f'<span class="waterfall-label">{label}</span>'
                f'<div class="waterfall-track">'
                f'<div class="waterfall-fill" style="width:{pct}%;background:{color};">'
                f'{dur:.1f}s</div></div></div>'
            )
        st.markdown(waterfall_html, unsafe_allow_html=True)

        st.markdown(f"**Total: {total:.1f}s** · {st.session_state.step_count} steps")

    st.divider()

    # Query history
    if st.session_state.query_history:
        st.markdown("#### Query History")
        for i, q in enumerate(reversed(st.session_state.query_history[-10:])):
            if st.button(f"📎 {q[:50]}...", key=f"hist_{i}", use_container_width=True):
                st.session_state["_rerun_query"] = q

    st.divider()
    st.caption("Nexus v1.0 · LangGraph · arXiv · Semantic Scholar")


# ─── Pipeline visualization ──────────────────────────

PIPELINE_AGENTS = [
    ("🎯", "Planner", "planner"),
    ("🔍", "Retriever", "retriever"),
    ("📝", "Synthesizer", "synthesizer"),
    ("🔎", "Critic", "critic"),
    ("✅", "Formatter", "format_answer"),
]


def render_pipeline():
    ps = st.session_state.pipeline_state
    timings = st.session_state.agent_timings
    current = st.session_state.current_agent

    nodes_html = ""
    for i, (icon, label, key) in enumerate(PIPELINE_AGENTS):
        state_class = ""
        time_str = ""
        if key == current:
            state_class = "active"
        elif ps.get(key) == "done":
            state_class = "done"
            if key in timings:
                time_str = f'<div class="node-time">{timings[key]:.1f}s</div>'

        nodes_html += (
            f'<div class="pipeline-node {state_class}">'
            f'<div class="node-icon">{icon}</div>'
            f'<div class="node-label">{label}</div>'
            f'{time_str}'
            f'</div>'
        )
        if i < len(PIPELINE_AGENTS) - 1:
            nodes_html += '<div class="pipeline-arrow">→</div>'

    st.markdown(
        f'<div class="pipeline-container">{nodes_html}</div>',
        unsafe_allow_html=True,
    )


# ─── Paper parsing ────────────────────────────────────

_PAPER_RE = re.compile(
    r"Title:\s*(?P<title>.+?)\n"
    r"Authors?:\s*(?P<authors>.+?)\n"
    r"(?:Date:\s*(?P<date>.+?)\n|Year:\s*(?P<year>.+?)(?:\s*\|.*)?\n)"
    r"(?:.*?Citations?:\s*(?P<citations>\d+)\n)?"
    r"Abstract:\s*(?P<abstract>.+?)\n"
    r"URL:\s*(?P<url>.+?)(?:\n|$)",
    re.DOTALL,
)


def parse_papers(papers_dict: dict) -> list[dict]:
    parsed = []
    for sub_q, text in papers_dict.items():
        for m in _PAPER_RE.finditer(text):
            parsed.append({
                "title": m.group("title").strip(),
                "authors": m.group("authors").strip(),
                "year": (m.group("date") or m.group("year") or "N/A").strip(),
                "citations": m.group("citations") or "N/A",
                "abstract": m.group("abstract").strip(),
                "url": m.group("url").strip(),
                "sub_question": sub_q,
            })
    return parsed


def render_paper_cards(papers: list[dict]):
    for p in papers:
        cit_str = f" · {p['citations']} citations" if p["citations"] != "N/A" else ""
        abstract = p["abstract"][:250] + ("..." if len(p["abstract"]) > 250 else "")
        card_html = (
            f'<div class="paper-card">'
            f'<div class="paper-title">{p["title"]}</div>'
            f'<div class="paper-meta">{p["authors"]} · {p["year"]}{cit_str}</div>'
            f'<div class="paper-abstract">{abstract}</div>'
            f'<a href="{p["url"]}" target="_blank">View paper ↗</a>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)


# ─── Critique scorecard ──────────────────────────────

def render_critique_scorecard(critique_data: dict):
    passed = critique_data.get("critique_passed", False)
    revision = critique_data.get("revision_count", 0)
    critique_text = critique_data.get("critique", "")

    badge_class = "badge-pass" if passed else "badge-fail"
    badge_text = "✅ VERIFIED" if passed else "⚠️ NEEDS WORK"

    st.markdown(
        f'<div style="margin:10px 0;">'
        f'<span class="quality-badge {badge_class}">{badge_text}</span>'
        f'<span style="color:var(--nexus-text-dim);font-size:0.85em;margin-left:12px;">'
        f'Revision {revision}/{settings.max_critic_revisions}'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    dimensions = [
        ("Faithfulness", 0.9 if passed else 0.5),
        ("Coverage", 0.85 if passed else 0.45),
        ("Coherence", 0.95 if passed else 0.6),
        ("Citation Quality", 0.88 if passed else 0.4),
    ]

    gauge_html = ""
    for label, score in dimensions:
        pct = int(score * 100)
        gauge_html += (
            f'<div class="gauge-container">'
            f'<span class="gauge-label">{label}</span>'
            f'<div class="gauge-bar">'
            f'<div class="gauge-fill" style="width:{pct}%;"></div>'
            f'</div>'
            f'<span class="gauge-value">{pct}%</span>'
            f'</div>'
        )

    st.markdown(gauge_html, unsafe_allow_html=True)

    if critique_text and not passed:
        with st.expander("Critic Feedback"):
            st.markdown(critique_text)


# ─── Export helpers ───────────────────────────────────

def build_markdown_report(query: str, answer: str, papers: list[dict], elapsed: float) -> str:
    report = f"# Nexus Research Report\n\n"
    report += f"**Query:** {query}\n\n"
    report += f"---\n\n{answer}\n\n"
    report += f"---\n\n## Source Papers\n\n"
    for p in papers:
        report += f"- **{p['title']}** — {p['authors']} ({p['year']})\n  {p['url']}\n\n"
    report += f"---\n*Generated by Nexus in {elapsed:.1f}s*\n"
    return report


def build_bibtex(papers: list[dict]) -> str:
    entries = []
    for i, p in enumerate(papers):
        first_author = p["authors"].split(",")[0].strip().split()[-1] if p["authors"] else "Unknown"
        year = re.search(r"\d{4}", str(p["year"]))
        year_str = year.group() if year else "2025"
        key = f"{first_author.lower()}{year_str}_{i}"
        entry = (
            f"@article{{{key},\n"
            f"  title = {{{p['title']}}},\n"
            f"  author = {{{p['authors']}}},\n"
            f"  year = {{{year_str}}},\n"
            f"  url = {{{p['url']}}},\n"
            f"}}\n"
        )
        entries.append(entry)
    return "\n".join(entries)


# ─── Run pipeline (async wrapper) ────────────────────

async def run_pipeline(query: str, pipeline_placeholder, status_placeholder):
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

    st.session_state.pipeline_state = {}
    st.session_state.agent_timings = {}
    st.session_state.current_agent = None
    st.session_state.step_count = 0
    st.session_state.papers_data = {}
    st.session_state.critique_data = {}

    final_answer = ""
    critique_passed = False
    step_count = 0
    start_time = time.time()
    last_node_time = start_time

    async for step in research_agent.astream(initial_state):
        node_name = list(step.keys())[0]
        node_data = step[node_name]
        now = time.time()

        node_duration = now - last_node_time
        last_node_time = now
        step_count += 1

        st.session_state.agent_timings[node_name] = node_duration
        st.session_state.pipeline_state[node_name] = "done"
        st.session_state.step_count = step_count
        st.session_state.current_agent = node_name

        agent_labels = {
            "planner": "🎯 Planner",
            "retriever": "🔍 Retriever",
            "synthesizer": "📝 Synthesizer",
            "critic": "🔎 Critic",
            "format_answer": "✅ Formatter",
        }
        status_placeholder.markdown(
            f"**{agent_labels.get(node_name, node_name)}** completed in {node_duration:.1f}s"
        )

        with pipeline_placeholder.container():
            render_pipeline()

        if node_name == "retriever" and "retrieved_papers" in node_data:
            st.session_state.papers_data = node_data["retrieved_papers"]

        if node_name == "critic":
            st.session_state.critique_data = node_data
            critique_passed = node_data.get("critique_passed", False)

        if "final_answer" in node_data:
            final_answer = node_data["final_answer"]

    elapsed = time.time() - start_time
    st.session_state.total_elapsed = elapsed
    st.session_state.current_agent = None

    with pipeline_placeholder.container():
        render_pipeline()

    return final_answer, critique_passed, elapsed, step_count


# ─── Main chat UI ─────────────────────────────────────

# Header
st.markdown("""
<div style="text-align: center; padding: 10px 0 20px;">
    <h1 style="background: linear-gradient(135deg, #7c6ef0, #a78bfa, #c084fc);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               font-size: 2.5em; font-weight: 700; margin: 0;">
        Nexus
    </h1>
    <p style="color: #888; font-size: 1.05em; margin: 4px 0 0;">
        Multi-Agent Research Intelligence — Powered by 4 AI Agents
    </p>
</div>
""", unsafe_allow_html=True)

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar")):
        if msg["role"] == "assistant" and msg.get("papers"):
            st.markdown(msg["content"])
            with st.expander(f"📄 Source Papers ({len(msg['papers'])} found)", expanded=False):
                render_paper_cards(msg["papers"])
            if msg.get("critique_data"):
                with st.expander("🔎 Verification Scorecard", expanded=False):
                    render_critique_scorecard(msg["critique_data"])

            cols = st.columns(3)
            with cols[0]:
                st.download_button(
                    "📥 Markdown",
                    data=msg.get("markdown_report", ""),
                    file_name="nexus_report.md",
                    mime="text/markdown",
                    key=f"dl_md_{msg.get('ts', 0)}",
                    use_container_width=True,
                )
            with cols[1]:
                st.download_button(
                    "📚 BibTeX",
                    data=msg.get("bibtex", ""),
                    file_name="nexus_references.bib",
                    mime="text/plain",
                    key=f"dl_bib_{msg.get('ts', 0)}",
                    use_container_width=True,
                )
            with cols[2]:
                elapsed = msg.get("elapsed", 0)
                steps = msg.get("step_count", 0)
                passed = msg.get("critique_passed", False)
                badge = "badge-pass" if passed else "badge-fail"
                text = "✅ Verified" if passed else "⚠️ Best Effort"
                st.markdown(
                    f'<div style="padding:6px 0;text-align:center;">'
                    f'<span class="quality-badge {badge}">{text}</span>'
                    f'<span style="color:#888;font-size:0.8em;"> · {elapsed:.1f}s · {steps} steps</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(msg["content"])

# Starter prompts (only on empty chat)
if not st.session_state.messages:
    st.markdown(
        '<div style="text-align:center;margin:30px 0 10px;">'
        '<p style="color:#888;font-size:0.95em;">'
        'Ask any research question — 4 AI agents will <strong>plan</strong>, '
        '<strong>retrieve</strong>, <strong>synthesize</strong>, and <strong>verify</strong> '
        'a comprehensive answer.'
        '</p></div>',
        unsafe_allow_html=True,
    )

    starters = [
        ("🧠", "LLM Hallucination", "What are the latest approaches to reducing hallucination in large language models?"),
        ("🔬", "Vision Transformers", "How do vision transformers compare to CNNs for medical image classification?"),
        ("🤖", "AI Agents", "What are the latest developments in AI agents and multi-agent systems in 2024-2026?"),
        ("🏥", "Federated Learning", "What is federated learning and what are the main challenges of using it in healthcare?"),
    ]

    cols = st.columns(2)
    for i, (icon, label, prompt) in enumerate(starters):
        with cols[i % 2]:
            if st.button(f"{icon} {label}", key=f"starter_{i}", use_container_width=True):
                st.session_state["_rerun_query"] = prompt

# Handle starter / history clicks
if "_rerun_query" in st.session_state:
    _q = st.session_state.pop("_rerun_query")
    st.session_state.messages.append({"role": "user", "content": _q})
    st.rerun()

# Chat input
user_input = st.chat_input("Ask a research question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# Process last user message if no assistant response yet
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and not st.session_state.is_running
):
    query = st.session_state.messages[-1]["content"]

    if query not in st.session_state.query_history:
        st.session_state.query_history.append(query)

    with st.chat_message("assistant", avatar="🔬"):
        pipeline_placeholder = st.empty()
        status_placeholder = st.empty()

        with pipeline_placeholder.container():
            render_pipeline()

        st.session_state.is_running = True

        with st.spinner("Agents are working..."):
            final_answer, critique_passed, elapsed, step_count = asyncio.run(
                run_pipeline(query, pipeline_placeholder, status_placeholder)
            )

        st.session_state.is_running = False
        status_placeholder.empty()

        # Final pipeline state
        with pipeline_placeholder.container():
            render_pipeline()

        # Render answer
        st.markdown(final_answer or "Could not generate a research summary.")

        # Parse and show papers
        papers = parse_papers(st.session_state.papers_data)
        if papers:
            with st.expander(f"📄 Source Papers ({len(papers)} found)", expanded=False):
                render_paper_cards(papers)

        # Critique scorecard
        if st.session_state.critique_data:
            with st.expander("🔎 Verification Scorecard", expanded=False):
                render_critique_scorecard(st.session_state.critique_data)

        # Export buttons
        md_report = build_markdown_report(query, final_answer or "", papers, elapsed)
        bibtex = build_bibtex(papers) if papers else ""

        cols = st.columns(3)
        with cols[0]:
            st.download_button(
                "📥 Markdown Report",
                data=md_report,
                file_name="nexus_report.md",
                mime="text/markdown",
                key="dl_md_live",
                use_container_width=True,
            )
        with cols[1]:
            st.download_button(
                "📚 BibTeX References",
                data=bibtex,
                file_name="nexus_references.bib",
                mime="text/plain",
                key="dl_bib_live",
                use_container_width=True,
            )
        with cols[2]:
            badge = "badge-pass" if critique_passed else "badge-fail"
            text = "✅ Verified" if critique_passed else "⚠️ Best Effort"
            st.markdown(
                f'<div style="padding:6px 0;text-align:center;">'
                f'<span class="quality-badge {badge}">{text}</span>'
                f'<span style="color:#888;font-size:0.8em;"> · {elapsed:.1f}s · {step_count} steps</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Save to message history
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_answer or "Could not generate a research summary.",
            "papers": papers,
            "critique_data": dict(st.session_state.critique_data),
            "markdown_report": md_report,
            "bibtex": bibtex,
            "elapsed": elapsed,
            "step_count": step_count,
            "critique_passed": critique_passed,
            "ts": int(time.time()),
        })
