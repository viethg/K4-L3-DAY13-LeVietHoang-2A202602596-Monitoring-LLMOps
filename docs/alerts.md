# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms` (ngưỡng SLO <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` duy trì liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ lâu hơn để nhận câu trả lời, trải nghiệm hội thoại bị gián đoạn, nguy cơ client timeout
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Mở dashboard panel `Latency`, kiểm tra P50/P95/P99 và `ttft_p95` xem độ trễ tăng đột biến ở bước nào và bắt đầu từ thời điểm nào.
  2. **Logs:** Lọc `data/logs.jsonl` tìm các event `response_sent` có `latency_ms > 3000` trong khung giờ đó, trích xuất `correlation_id` đại diện.
  3. **Traces:** Mở trace cùng `correlation_id` trên Langfuse, so sánh thời gian thực thi của span `retrieval` và span `generation` để xác định điểm nghẽn (do vector DB chậm hay do LLM generation kéo dài).
- Mitigation tạm thời: Nếu do LLM generation (prompt quá dài hoặc model chậm), thực hiện rollback prompt label về version ổn định; nếu do vector store quá tải, kích hoạt cache hoặc giảm số lượng top_k tài liệu retrieval.
- Owner: `student-2A202602596`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Tỉ lệ lỗi tổng thể của request (`count(request_failed) / count(request_received) * 100`, guardrail <= 2%)
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` duy trì trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận lỗi HTTP 500 hoặc thông báo gián đoạn dịch vụ, không thể hoàn thành tác vụ
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Mở dashboard panel `Errors`, kiểm tra `error_rate_pct` và phân bố số lượng lỗi theo từng `error_type`.
  2. **Logs:** Lọc các sự kiện `request_failed` trong `data/logs.jsonl`, kiểm tra thông điệp lỗi, mã lỗi và trích xuất `correlation_id` của request lỗi gần nhất.
  3. **Traces:** Mở trace trên Langfuse theo `correlation_id`, kiểm tra span nào bị đánh dấu Error (lỗi tại middleware, vector store hay LLM provider).
- Mitigation tạm thời: Chuyển hướng traffic sang instance dự phòng; nếu lỗi do provider bên ngoài (LLM/Vector store timeout), kích hoạt circuit breaker và trả graceful fallback response cho người dùng.
- Owner: `student-2A202602596`

## Alert 3

- Tên: `LowRetrievalSuccessRate`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Tỉ lệ thành công của Retrieval tool (`count(tool_success == true) / count(tool_success != null) * 100`, guardrail >= 90%)
- Điều kiện và thời gian duy trì: `tool_success_rate_pct < 90%` duy trì trong 10 phút
- Ảnh hưởng tới người dùng: Câu trả lời của trợ lý thiếu ngữ cảnh tài liệu cần thiết, dẫn đến chất lượng giảm hoặc rơi vào câu trả lời chung chung
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** Mở panel `Errors` trên dashboard để xem đường xu hướng của `tool_success_rate_pct`, đồng thời kiểm tra panel `Quality` xem điểm `quality_score` có sụt giảm tương ứng không.
  2. **Logs:** Lọc các bản ghi log có `tool_success: false` trong `data/logs.jsonl`, kiểm tra `tool_name` và chi tiết lỗi được ghi nhận.
  3. **Traces:** Vào Langfuse mở trace của request có tool failure, kiểm tra chi tiết span `retrieval` để xác định lỗi kết nối, index thiếu hay parse lỗi.
- Mitigation tạm thời: Khởi động lại service retrieval hoặc switch sang dùng từ khóa tìm kiếm cơ bản (keyword fallback); kiểm tra kết nối mạng và tài nguyên của vector DB.
- Owner: `student-2A202602596`
