from __future__ import annotations

import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

load_dotenv()

from app.agent import LabAgent
from app.tracing import get_langfuse_client

def run_request(agent: LabAgent, label: str, correlation_id: str, message: str = "Explain traces"):
    os.environ["LANGFUSE_PROMPT_LABEL"] = label
    # Clear client prompt cache if available
    client = get_langfuse_client()
    if hasattr(client, "clear_prompt_cache"):
        client.clear_prompt_cache()
    res = agent.run(
        user_id="student-2A202602596",
        feature="qa",
        session_id="session-cp2",
        message=message,
        correlation_id=correlation_id,
    )
    # Get current trace id from observation
    client.flush()
    time.sleep(1)
    return res

def main():
    client = get_langfuse_client()
    agent = LabAgent()

    print("=== Bước 1: Chạy request với version 1 (label: baseline) ===")
    res1 = run_request(agent, "baseline", "req-base-0001", "How do traces and logs correlate?")
    print("Baseline result:", res1.answer[:60], "...", "latency:", res1.latency_ms)

    print("\n=== Bước 2: Chạy request với version 2 (label: candidate) ===")
    res2 = run_request(agent, "candidate", "req-cand-0002", "How do traces and logs correlate?")
    print("Candidate result:", res2.answer[:60], "...", "latency:", res2.latency_ms)

    print("\n=== Bước 3: Promote - Gán label production cho version 2 ===")
    p2 = client.update_prompt(name="day13-chat", version=2, new_labels=["candidate", "production"])
    print("Version 2 labels now:", p2.labels)
    res3 = run_request(agent, "production", "req-prom-0003", "Explain prompt promotion")
    print("Promoted result:", res3.answer[:60], "...", "latency:", res3.latency_ms)

    print("\n=== Bước 4: Rollback - Trả label production về version 1 ===")
    p1 = client.update_prompt(name="day13-chat", version=1, new_labels=["baseline", "production"])
    print("Version 1 labels now:", p1.labels)
    res4 = run_request(agent, "production", "req-roll-0004", "Explain prompt rollback")
    print("Rollback result:", res4.answer[:60], "...", "latency:", res4.latency_ms)

    print("\n=== Bước 5: Chạy thêm workload để đạt >= 10 traces ===")
    queries = [
        "Explain metrics percentiles P95 and P99",
        "How does vector retrieval work in RAG?",
        "What is an Error Budget and SLO?",
        "How to sanitize PII in structured logs?",
        "Why is correlation ID important in distributed systems?",
        "What is time to first token TTFT?",
    ]
    for i, q in enumerate(queries, start=5):
        req_id = f"req-workload-{i:04d}"
        r = run_request(agent, "production", req_id, q)
        print(f"Request {i} ({req_id}): latency={r.latency_ms}ms, quality={r.quality_score}")

    client.flush()
    print("\nĐã hoàn thành toàn bộ workflow CP2 và flush traces lên Langfuse!")

if __name__ == "__main__":
    main()
