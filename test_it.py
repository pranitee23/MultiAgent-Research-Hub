# test_it.py
import time
from src.core.graph import research_agent

query = "What are the latest approaches to reducing hallucination in LLMs?"

print(f"Question: {query}\n")
print("Starting pipeline...")
start = time.time()

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

for step in research_agent.stream(initial_state):
    node = list(step.keys())[0]
    elapsed = time.time() - start
    print(f"  [{elapsed:.0f}s] ✅ {node} completed")

print(f"\nTotal time: {time.time() - start:.0f}s\n")
print("=" * 50)
print(step[node].get("final_answer", "No answer generated"))