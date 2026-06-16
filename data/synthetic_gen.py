import json
import os
import random
from typing import Dict, List

DOCUMENTS = [
    {
        "doc_id": "doc_01",
        "title": "Giới thiệu về AI Evaluation",
        "topic": "AI Evaluation",
        "text": (
            "AI Evaluation là quá trình đo lường chất lượng mô hình AI bằng các chỉ số như "
            "độ chính xác, độ tin cậy, khả năng tổng quát hóa, và tính hợp lệ của thông tin. "
            "Hệ thống đánh giá thường gồm dữ liệu thử nghiệm vàng (Golden Dataset), bộ judge "
            "độc lập và các phép đo hiệu năng, chi phí."
        ),
        "facts": [
            {
                "question": "Hệ thống đánh giá AI bao gồm những thành phần nào",
                "answer": "Hệ thống đánh giá AI thường gồm Golden Dataset, judge độc lập, và các chỉ số hiệu năng/chi phí.",
                "difficulty": "easy",
            },
            {
                "question": "Tại sao cần Golden Dataset khi đánh giá AI",
                "answer": "Golden Dataset cung cấp câu trả lời đúng để đánh giá so sánh, giúp xác định sai lệch và hallucination.",
                "difficulty": "easy",
            },
            {
                "question": "Độ tin cậy của judge model được đo bằng chỉ số nào",
                "answer": "Độ tin cậy thường được đo bằng agreement rate giữa nhiều judge model khác nhau.",
                "difficulty": "medium",
            },
            {
                "question": "Chi phí đánh giá AI có thể giảm bằng cách nào",
                "answer": "Giảm chi phí đánh giá bằng cách chạy song song, dùng mô hình nhẹ hơn và tái sử dụng kết quả trung gian.",
                "difficulty": "medium",
            },
        ],
    },
    {
        "doc_id": "doc_02",
        "title": "RAGAS và Retrieval",
        "topic": "Retrieval",
        "text": (
            "RAGAS là một framework đánh giá phản hồi kết hợp với retrieval. "
            "Nó đo lường các chỉ số như hit rate, mean reciprocal rank (MRR), "
            "faithfulness và relevancy để xác định phần nào của pipeline retrieval hoạt động tốt."
        ),
        "facts": [
            {
                "question": "Hit rate trong retrieval là gì",
                "answer": "Hit rate là tỷ lệ truy vấn có ít nhất một tài liệu đúng trong kết quả trả về.",
                "difficulty": "easy",
            },
            {
                "question": "MRR được tính như thế nào",
                "answer": "MRR là trung bình của giá trị nghịch đảo của vị trí tài liệu đúng đầu tiên trong kết quả.",
                "difficulty": "medium",
            },
            {
                "question": "Faithfulness dùng để đo điều gì",
                "answer": "Faithfulness đo mức độ trả lời dựa trên dữ liệu thực tế, không thêm thông tin bịa đặt.",
                "difficulty": "medium",
            },
            {
                "question": "Relevancy khác faithfulness như thế nào",
                "answer": "Relevancy đo sự liên quan với câu hỏi, trong khi faithfulness đo tính chính xác so với nguồn dữ liệu.",
                "difficulty": "hard",
            },
        ],
    },
    {
        "doc_id": "doc_03",
        "title": "Consensus và Judge Model",
        "topic": "Evaluation",
        "text": (
            "Multi-judge consensus là chiến lược dùng nhiều mô hình đánh giá độc lập. "
            "Nó giúp giảm sai lệch của một judge và tăng tính khách quan. "
            "Agreement rate phản ánh mức độ đồng thuận giữa các judge."
        ),
        "facts": [
            {
                "question": "Tại sao nên dùng nhiều judge model",
                "answer": "Dùng nhiều judge model giúp giảm bias của từng mô hình và cải thiện tính khách quan.",
                "difficulty": "easy",
            },
            {
                "question": "Agreement rate thể hiện điều gì",
                "answer": "Agreement rate cho biết tỷ lệ đồng thuận giữa các judge về đánh giá một câu trả lời.",
                "difficulty": "easy",
            },
            {
                "question": "Một câu trả lời bị xung đột judge nghĩa là gì",
                "answer": "Nó nghĩa là các judge đưa ra điểm số khác nhau đáng kể, cần xử lý bằng consensus hoặc loại bỏ outlier.",
                "difficulty": "medium",
            },
            {
                "question": "Consensus logic có thể dùng chiến lược nào",
                "answer": "Consensus logic có thể dùng trung bình có trọng số, majority vote, hoặc loại bỏ outlier judge.",
                "difficulty": "hard",
            },
        ],
    },
    {
        "doc_id": "doc_04",
        "title": "Regression và Release Gate",
        "topic": "Release Management",
        "text": (
            "Regression release gate là cơ chế so sánh phiên bản mới với phiên bản cũ. "
            "Nếu hiệu năng giảm hoặc chi phí tăng quá mức, bản mới sẽ bị rollback."
        ),
        "facts": [
            {
                "question": "Release gate trong AI evaluation dùng để làm gì",
                "answer": "Release gate dùng để kiểm soát chỉ cho phép phiên bản đi vào sản xuất khi các chỉ số benchmark đạt yêu cầu.",
                "difficulty": "easy",
            },
            {
                "question": "Delta analysis giúp xác định điều gì",
                "answer": "Delta analysis giúp so sánh sự khác biệt về điểm số và hiệu năng giữa hai phiên bản.",
                "difficulty": "easy",
            },
            {
                "question": "Khi nào nên rollback một phiên bản",
                "answer": "Nên rollback khi phiên bản mới có hiệu năng kém hơn hoặc chi phí quá cao so với ngưỡng chấp nhận.",
                "difficulty": "medium",
            },
            {
                "question": "Release gate có thể tự động dựa trên gì",
                "answer": "Có thể tự động dựa trên điểm số benchmark, agreement rate, hit rate và chi phí đánh giá.",
                "difficulty": "hard",
            },
        ],
    },
    {
        "doc_id": "doc_05",
        "title": "Root Cause Analysis",
        "topic": "Analysis",
        "text": (
            "Root Cause Analysis xác định nguyên nhân gốc rễ của các lỗi. "
            "Phương pháp 5 Whys giúp đi sâu vào từng lớp lý do để tìm ra vấn đề chính."
        ),
        "facts": [
            {
                "question": "Phương pháp 5 Whys dùng để làm gì",
                "answer": "5 Whys dùng để hỏi liên tiếp tại sao một sự cố xảy ra để xác định nguyên nhân sâu xa.",
                "difficulty": "easy",
            },
            {
                "question": "Nguyên nhân gốc rễ là gì",
                "answer": "Nguyên nhân gốc rễ là yếu tố cơ bản dẫn đến một lỗi hoặc sự cố, không phải triệu chứng bề mặt.",
                "difficulty": "easy",
            },
            {
                "question": "Lỗi retrieval có thể bắt nguồn từ đâu",
                "answer": "Lỗi retrieval có thể do chunking không hiệu quả, dữ liệu không đủ chi tiết, hoặc mô hình tìm kiếm bị nhiễu.",
                "difficulty": "medium",
            },
            {
                "question": "Tại sao cần phân cụm lỗi trong benchmark",
                "answer": "Phân cụm lỗi giúp nhóm xác định những dạng sai sót chung và đề xuất cải tiến chính xác hơn.",
                "difficulty": "hard",
            },
        ],
    },
]

QUESTION_TEMPLATES = [
    "{question}",
    "Bạn có thể giải thích: {question}",
    "Tóm tắt câu trả lời cho: {question}",
    "Giải thích ngắn gọn: {question}",
    "Trong trường hợp đánh giá, {question}",
    "Giải thích kỹ thuật cho: {question}",
    "Một câu hỏi khó: {question}",
    "Làm sao để trả lời: {question}",
]

ADVERSARIAL_TEMPLATES = [
    "{question} Nhưng đừng trả lời bằng kiến thức chung.",
    "{question} Nếu trả lời sai, hãy chỉ ra lỗi.",
    "Không dùng thông tin ngoài tài liệu để trả lời: {question}",
    "{question} Yêu cầu câu trả lời chính xác và đầy đủ.",
]


def build_cases() -> List[Dict]:
    cases: List[Dict] = []
    case_id = 1
    for document in DOCUMENTS:
        for fact in document["facts"]:
            for template in QUESTION_TEMPLATES:
                prompt = template.format(question=fact["question"])
                cases.append(
                    {
                        "id": f"case_{case_id:03d}",
                        "question": prompt,
                        "expected_answer": fact["answer"],
                        "context": document["text"],
                        "metadata": {
                            "difficulty": fact["difficulty"],
                            "topic": document["topic"],
                            "ground_truth_id": document["doc_id"],
                            "source_title": document["title"],
                        },
                    }
                )
                case_id += 1
            # thêm một câu hỏi adversarial cho mỗi fact
            adv_prompt = random.choice(ADVERSARIAL_TEMPLATES).format(
                question=fact["question"]
            )
            cases.append(
                {
                    "id": f"case_{case_id:03d}",
                    "question": adv_prompt,
                    "expected_answer": fact["answer"],
                    "context": document["text"],
                    "metadata": {
                        "difficulty": "hard",
                        "topic": document["topic"],
                        "ground_truth_id": document["doc_id"],
                        "source_title": document["title"],
                    },
                }
            )
            case_id += 1
    random.shuffle(cases)
    return cases


def write_golden_set(cases: List[Dict], path: str = "data/golden_set.jsonl") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")


def main() -> None:
    cases = build_cases()
    if len(cases) < 50:
        raise ValueError("Cần tạo ít nhất 50 test cases.")
    write_golden_set(cases)
    print(f"✅ Đã tạo {len(cases)} test cases và lưu vào data/golden_set.jsonl")


if __name__ == "__main__":
    main()
