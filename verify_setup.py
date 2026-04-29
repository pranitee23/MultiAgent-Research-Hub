#!/usr/bin/env python3
"""Nexus — 15 automated setup checks."""
import sys, importlib
P, F = 0, 0

def chk(name, fn):
    global P, F
    try:
        r = fn(); P += 1; print(f"  ✅  {name}\n      → {r}")
    except Exception as e:
        F += 1; print(f"  ❌  {name}\n      → {e}")

def c1():
    v = sys.version_info; assert v.major == 3 and v.minor >= 10; return f"Python {v.major}.{v.minor}"
def c2():
    from importlib.metadata import version; return f"langgraph {version('langgraph')}"
def c3():
    import langchain; return f"langchain {langchain.__version__}"
def c4():
    importlib.import_module("langchain_groq"); return "langchain-groq OK"
def c5():
    importlib.import_module("langchain_google_genai"); return "langchain-google-genai OK"
def c6():
    import faiss; return "faiss-cpu OK"
def c7():
    import sentence_transformers; return f"sentence-transformers {sentence_transformers.__version__}"
def c8():
    import arxiv; return "arxiv OK"
def c9():
    import semanticscholar; return "semanticscholar OK"
def c10():
    import chainlit; return f"chainlit {chainlit.__version__}"
def c11():
    from src.config.settings import settings; return f"provider={settings.llm_provider}"
def c12():
    from src.core.llm import get_provider_info; i = get_provider_info()
    if i["provider"] != "ollama" and not i.get("has_key"): raise AssertionError("API key empty in .env")
    return f"{i['provider']}, model={i['model']}"
def c13():
    from src.core.state import ResearchState; return f"{len(ResearchState.__annotations__)} fields"
def c14():
    from src.config.prompts import PLANNER_SYSTEM, CRITIC_SYSTEM; return f"prompts loaded"
def c15():
    from src.core.llm import get_llm; r = get_llm(temperature=0).invoke("Say hello"); return f"LLM: '{r.content[:40]}'"

if __name__ == "__main__":
    print("=" * 50 + "\n  Nexus — Setup Verification\n" + "=" * 50)
    for n, f in [("Python ≥3.10",c1),("LangGraph",c2),("LangChain",c3),("Groq",c4),("Gemini",c5),("FAISS",c6),
                  ("Sentence-Trans",c7),("arXiv",c8),("Scholar",c9),("Chainlit",c10),("Settings",c11),
                  ("LLM key",c12),("State",c13),("Prompts",c14),("LLM live",c15)]:
        chk(n, f); print()
    print(f"{'='*50}\n  {P} passed, {F} failed\n{'='*50}")
    print("\n🎉 Ready for app built!" if F == 0 else "\n⚠️ Fix failures above.")
    sys.exit(F)