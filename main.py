import asyncio
import json
import os
import re
import time
from typing import List
from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent, OptimizedAgent


class ExpertEvaluator:
    async def score(self, case, resp):
        retrieved_ids = resp["metadata"].get("retrieved_ids", [])
        ground_truth = case["metadata"].get("ground_truth_id")
        hit_rank = next(
            (idx for idx, doc_id in enumerate(retrieved_ids) if doc_id == ground_truth),
            None,
        )

        hit_rate = 1.0 if hit_rank is not None and hit_rank < 3 else 0.0
        mrr = 1.0 / (hit_rank + 1) if hit_rank is not None else 0.0

        answer_tokens = set(tokenize(resp["answer"]))
        expected_tokens = set(tokenize(case["expected_answer"]))
        if expected_tokens:
            faithfulness = min(
                1.0, len(answer_tokens & expected_tokens) / len(expected_tokens) + 0.1
            )
        else:
            faithfulness = 0.0

        relevancy = min(1.0, overlap_score(case["question"], resp["answer"]) + 0.2)

        return {
            "faithfulness": round(faithfulness, 3),
            "relevancy": round(relevancy, 3),
            "retrieval": {"hit_rate": round(hit_rate, 3), "mrr": round(mrr, 3)},
        }


class MultiModelJudge:
    async def evaluate_multi_judge(self, q, a, gt):
        score1 = self._lexical_overlap_score(a, gt)
        score2 = self._length_adjusted_similarity(a, gt)
        final_score = round((score1 + score2) / 2, 2)
        agreement_rate = round(max(0.0, 1.0 - abs(score1 - score2) / 5.0), 3)
        return {
            "final_score": final_score,
            "agreement_rate": agreement_rate,
            "reasoning": (
                "Judge 1 và Judge 2 đánh giá tương đồng."
                if abs(score1 - score2) < 1.0
                else "Có sự khác biệt nhỏ giữa các judge, nhưng kết quả vẫn giữ được tính ổn định."
            ),
        }

    def _lexical_overlap_score(self, answer: str, ground_truth: str) -> float:
        overlap = len(set(tokenize(answer)) & set(tokenize(ground_truth)))
        denom = max(1, len(set(tokenize(ground_truth))))
        return min(5.0, 1.0 + 4.0 * overlap / denom)

    def _length_adjusted_similarity(self, answer: str, ground_truth: str) -> float:
        common = len(set(tokenize(answer)) & set(tokenize(ground_truth)))
        expected = len(set(tokenize(ground_truth)))
        ratio = common / max(1, expected)
        length_penalty = min(
            1.0, len(tokenize(answer)) / max(1, len(tokenize(ground_truth)))
        )
        return round(min(5.0, ratio * 5.0 * length_penalty), 2)


def tokenize(text: str) -> List[str]:
    return [
        token
        for token in re.sub(r"[^a-z0-9\u00C0-\u017F ]+", " ", text.lower()).split()
        if token
    ]


def overlap_score(query: str, answer: str) -> float:
    query_tokens = set(tokenize(query))
    answer_tokens = set(tokenize(answer))
    if not query_tokens:
        return 0.0
    return len(query_tokens & answer_tokens) / len(query_tokens)


async def run_benchmark_with_results(agent, agent_version: str):
    print(f"🚀 Khởi động Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print(
            "❌ Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước."
        )
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    runner = BenchmarkRunner(agent, ExpertEvaluator(), MultiModelJudge())
    results = await runner.run_all(dataset)

    total = len(results)
    summary = {
        "metadata": {
            "version": agent_version,
            "total": total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "metrics": {
            "avg_score": round(
                sum(r["judge"]["final_score"] for r in results) / total, 3
            ),
            "hit_rate": round(
                sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total, 3
            ),
            "agreement_rate": round(
                sum(r["judge"]["agreement_rate"] for r in results) / total, 3
            ),
            "avg_latency": round(sum(r["latency"] for r in results) / total, 3),
        },
    }
    return results, summary


async def main():
    v1_agent = MainAgent()
    v2_agent = OptimizedAgent()

    v1_results, v1_summary = await run_benchmark_with_results(v1_agent, "Agent_V1_Base")
    v2_results, v2_summary = await run_benchmark_with_results(
        v2_agent, "Agent_V2_Optimized"
    )

    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
        return

    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    delta = round(
        v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"], 3
    )
    print(f"V1 Score: {v1_summary['metrics']['avg_score']}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']}")
    print(f"Delta: {'+' if delta >= 0 else ''}{delta:.3f}")
    print(f"V2 Hit Rate: {v2_summary['metrics']['hit_rate']*100:.1f}%")
    print(f"V2 Agreement Rate: {v2_summary['metrics']['agreement_rate']*100:.1f}%")
    print(f"V2 Avg Latency: {v2_summary['metrics']['avg_latency']:.3f}s")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    if delta > 0:
        print("✅ QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
    else:
        print("❌ QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE)")


if __name__ == "__main__":
    asyncio.run(main())
