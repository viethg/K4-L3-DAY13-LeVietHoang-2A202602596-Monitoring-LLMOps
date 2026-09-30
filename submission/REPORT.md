# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lê Việt Hoàng
- **MSSV:** 2A202602596
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/viethg/K4-L3-DAY13-LeVietHoang-2A202602596-Monitoring-LLMOps
- **Commit SHA cuối:** `ac512c7`
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602596`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 (missing `correlation_id` & enrichment ở 20/21 bản ghi) | 100/100 | Đạt yêu cầu CP1 (yêu cầu ≥ 80/100), đầy đủ trường và enrichment, không leak PII |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel | HỢP LỆ: 6/6 panel | Đầy đủ 6 panel: Latency, Traffic, Errors, Cost, Tokens, Quality |
| `pytest` | 22 passed (1.88s) | 25 passed | Đầy đủ test suite, bao gồm PII test và observation trace test |
| Số traces hợp lệ | 0/10 (có 10 trace root `lab-agent-run`, thiếu child spans `retrieval`/`generation`, `correlation_id=MISSING`) | ≥ 10 traces đủ cây | Đầy đủ cây quan sát: root `lab-agent-run` và 2 child observations `retrieval`, `generation` |
| Số PII leak | 0 (trong `load_test.py`), nhưng `scrub_event` chưa bật trong `structlog` processor | 0 | Đã bật `scrub_event` processor trong `structlog.configure`, che dấu hoàn toàn Email, Phone VN, CCCD, Credit Card |
| Latency P95 / TTFT P95 | 3878.0 ms / 50.0 ms (P50: 1244.0 ms; steady-state ~435 ms) | 1247.7 ms / 50.0 ms | Đạt ngưỡng SLO (P95 ≤ 3000 ms, steady-state ổn định ~400 ms) |
| Retrieval success rate | 100% (10/10 requests `tool_success=true`) | 100.0% | Đạt guardrail (≥ 90%) |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  - Trong `CorrelationIdMiddleware` (`app/middleware.py`), trước mỗi request gọi `clear_contextvars()` để tránh rò rỉ context giữa các request.
  - Lấy correlation ID từ header `x-request-id` nếu client gửi lên; nếu không có, tự sinh ID ngẫu nhiên theo định dạng `req-<8-char-hex>` (ví dụ: `req-a1b2c3d4`).
  - Dùng `bind_contextvars(correlation_id=correlation_id)` của `structlog` để tự động đính kèm vào tất cả các log events trong request context.
  - Gắn vào `request.state.correlation_id` để router/handler và trace có thể truy cập.
  - Trả correlation ID về client trong response header `x-request-id`, kèm thời gian xử lý qua header `x-response-time-ms`.

- **Các metadata được ghi vào structured log:**
  - Context enrichment được bind tại `app/main.py`: `user_id_hash` (băm SHA-256 12 ký tự đầu), `session_id`, `feature`, `model`, `env`.
  - Các trường bắt buộc theo chuẩn: `ts` (ISO UTC timestamp), `level`, `service`, `event`, `correlation_id`.
  - Các sự kiện `request_received`, `response_sent` bổ sung thêm: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`, và `payload` chứa `message_preview`/`answer_preview`.

- **Cách bảo đảm PII được scrub trước khi ghi:**
  - Đăng ký processor `scrub_event` trong chuỗi `structlog.configure(...)` ngay trước `JsonlFileProcessor()` và `JSONRenderer()`.
  - Hàm `scrub_event` áp dụng `scrub_text()` lên nội dung `payload` (bao gồm `message_preview`, `answer_preview`, `detail`...) và `event`.
  - `scrub_text()` sử dụng regex pattern nhận diện và thay thế: `email` (`[REDACTED_EMAIL]`), `phone_vn` (`[REDACTED_PHONE_VN]`), `cccd` (`[REDACTED_CCCD]`), `credit_card` (`[REDACTED_CREDIT_CARD]`).

- **Cách kiểm chứng kết quả:**
  - Chạy `python -m pytest -q` đạt 25/25 passed (bao gồm các test PII mới).
  - Chạy `python scripts/load_test.py` và `python scripts/validate_logs.py` đạt điểm tuyệt đối 100/100 (không thiếu required fields, không thiếu context enrichment, đủ unique correlation IDs, không leak PII thô).
  - Gửi request mẫu và truy vấn log thực tế để xác nhận sự xuất hiện của `x-request-id`, `x-response-time-ms`, và nhãn REDACTED trong `data/logs.jsonl`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  - Project cá nhân: `day13-k4-l3b-2A202602596` trên Langfuse Cloud với API keys riêng biệt (`pk-lf-...`, `sk-lf-...`) trong file `.env`.
  - Các trace mang `user_id` băm từ `student-2A202602596`, tags định danh `['lab', 'qa', 'claude-sonnet-4-5']`, và `correlation_id` đồng nhất với hệ thống log.
- **Cấu trúc root/retrieval/generation observations:**
  - Root observation: `lab-agent-run` (as_type: `agent`) bao bọc toàn bộ chu trình xử lý của agent.
  - Child observation 1: `retrieval` (as_type: `retriever`) gắn decorator `@observe` trong `app/mock_rag.py`, đo thời gian truy xuất tài liệu context mà không lộ raw query/PII.
  - Child observation 2: `generation` (as_type: `generation`) gắn decorator `@observe` trong `app/mock_llm.py`, ghi nhận `model` (`claude-sonnet-4-5`), `usage_details` (`input`, `output`, `total`), và `cost_details` (`total`).
  - Cả `retrieval` và `generation` đều có `parent_observation_id` trỏ trực tiếp về ID của `lab-agent-run`.
- **Cách nối trace với log:**
  - `CorrelationIdMiddleware` sinh `correlation_id` cho request.
  - Tại `app/agent.py`, context manager `propagate_attributes(metadata={"correlation_id": correlation_id})` đưa ID này vào metadata của trace trên Langfuse.
  - Đồng thời, `structlog` bind contextvar `correlation_id` vào mọi bản ghi log (`request_received`, `response_sent`) trong `data/logs.jsonl`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 với labels `['baseline', 'production']` (template 3 biến: `{{feature}}`, `{{docs}}`, `{{message}}`).
- **Version/label candidate:** Version 2 với labels `['candidate', 'latest']` (thêm chỉ dẫn trả lời ngắn gọn).
- **Trace ID của mỗi version:**
  - Version 1 (baseline): `e30d7895aada1f36c6202c5611147730`
  - Version 2 (candidate): `bb16058f5db11d7b5bedf9fa88c3e7f7`
  - Version 2 (promoted to production): `a63b5bc54dec36dd8a1cc9d601efd064`
  - Version 1 (rollback to production): `a5252863efbab8d5a67080c8033f3a19`
- **Cách promote và rollback `production`:**
  - **Promote:** Gán label `production` cho Version 2 bằng Langfuse UI (hoặc `client.update_prompt(name='day13-chat', version=2, new_labels=['candidate', 'production'])`). Vì mỗi label trên Langfuse là độc nhất, Version 1 tự động mất label `production`. Ứng dụng đọc theo `LANGFUSE_PROMPT_LABEL=production` lập tức chuyển sang dùng Version 2 mà không cần sửa code.
  - **Rollback:** Khi cần hoàn tác về bản ổn định Version 1, gán lại label `production` cho Version 1 (`client.update_prompt(name='day13-chat', version=1, new_labels=['baseline', 'production'])`). Ứng dụng tự động tải lại Version 1 sau khi xóa cache / khởi động lại.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  - Xây dựng dashboard trực quan đọc trực tiếp từ `data/logs.jsonl` theo đúng contract `config/dashboard.yaml`:
    1. **Latency & TTFT:** Hiển thị P50, P95, P99 của `latency_ms` và `ttft_p95`; kèm ngưỡng threshold P95 ≤ 3000 ms.
    2. **Request Traffic:** Hiển thị tổng số requests và tốc độ `rate_per_minute` (req/phút); threshold rate ≥ 1 req/min.
    3. **Errors & Retrieval:** Tỉ lệ lỗi tổng thể `error_rate_pct` (≤ 2%) và tỉ lệ tìm kiếm thành công `retrieval_success_rate_pct` (≥ 90%).
    4. **Cost Over Time:** Tổng chi phí tích lũy theo USD; threshold total ≤ $2.50.
    5. **Tokens:** Tổng số token input và output; threshold sum ≤ 50,000 tokens.
    6. **Quality Proxy:** Điểm chất lượng trung bình `quality_score` (mean); threshold mean ≥ 0.75.
  - Dashboard có đầy đủ: Time range 60 phút, auto-refresh 30 giây, đơn vị rõ ràng và thanh trạng thái PASS/ALERT theo threshold.
- **SLO và lý do chọn:**
  - Primary SLO: `fast_successful_requests` với mục tiêu `99.5%` trong chu kỳ 28 ngày.
  - SLI: Tỉ lệ các request thỏa mãn `event == "response_sent" and latency_ms <= 3000` trên tổng số `event == "request_received"`.
  - Lý do: Baseline đo được có steady-state P95 latency ~435 ms; ngưỡng 3000 ms tạo biên độ an toàn cần thiết khi vector retrieval gặp tải cao mà vẫn đảm bảo người dùng không bị timeout hoặc gián đoạn hội thoại.
- **Cách tính error budget:**
  - SLO 99.5% trong chu kỳ 28 ngày tương ứng Error Budget là `0.5%`.
  - Với giả định hệ thống phục vụ 10,000 requests trong chu kỳ 28 ngày, số lượng request lỗi hoặc phản hồi chậm vượt 3000 ms tối đa được phép là: `10,000 * 0.5% = 50 requests`. Khi ngân sách này cạn kiệt, toàn bộ thay đổi tính năng mới phải tạm dừng để ưu tiên ổn định hệ thống.
- **Ba alert và runbook tương ứng:**
  - **Alert 1:** `HighLatencyP95` (Severity: `warning`, Condition: `p95(latency_ms) > 3000ms` trong 5 phút, Channel: `#k4-l3b-alerts`). Runbook: `docs/alerts.md#alert-1`.
  - **Alert 2:** `HighErrorRate` (Severity: `critical`, Condition: `error_rate_pct > 2%` trong 5 phút, Channel: `#k4-l3b-alerts`). Runbook: `docs/alerts.md#alert-2`.
  - **Alert 3:** `LowRetrievalSuccessRate` (Severity: `warning`, Condition: `tool_success_rate_pct < 90%` trong 10 phút, Channel: `#k4-l3b-alerts`). Runbook: `docs/alerts.md#alert-3`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `12:30:00 UTC` – `12:31:30 UTC` (ngày 2026-09-30)
- **Triệu chứng từ metrics:**
  - Panel `Latency & TTFT` trên dashboard ghi nhận độ trễ P95 tăng vọt từ baseline `683.3 ms` (steady-state ~152 ms) lên mức `2652.3 ms` (tăng gấp gần 4 lần so với baseline và gấp 17 lần so với steady-state).
  - Ngược lại, metric `ttft_p95` vẫn giữ nguyên ở mức `50.0 ms`, `error_rate_pct` duy trì ở mức 0.0%, và `retrieval_success_rate_pct` đạt 100.0%.
  - Dấu hiệu này cho thấy hệ thống không bị lỗi crash hay timeout mà đang bị nghẽn độ trễ tại một khâu tiền xử lý trước khi token đầu tiên sẵn sàng, nhưng sau khi bắt đầu xử lý request.
- **Log line và correlation ID liên quan:**
  - Correlation ID đại diện: `req-1482a893` (các ID cùng đợt ảnh hưởng: `req-74a28ba4`, `req-9bda1e79`, `req-52cbb69d`, `req-401f118b`).
  - Bản ghi log mẫu (`response_sent`):
    ```json
    {
      "ts": "2026-09-30T12:30:55.930554Z",
      "level": "info",
      "service": "api",
      "event": "response_sent",
      "correlation_id": "req-1482a893",
      "session_id": "k4-l3b-challenge-s01",
      "feature": "monitoring",
      "latency_ms": 2652,
      "ttft_ms": 50,
      "tokens_in": 35,
      "tokens_out": 128,
      "cost_usd": 0.002025,
      "quality_score": 0.8,
      "tool_name": "retrieval",
      "tool_success": true
    }
    ```
  - Đối chiếu log: Tất cả các request có `latency_ms > 2000` đều có chung trường `feature = "monitoring"`. Latency thực tế đo tại server là ~2652 ms (không dùng thời gian phía client load test do ảnh hưởng của việc xếp hàng concurrency).
- **Trace ID và span gây ảnh hưởng:**
  - Trace ID đối ứng trên Langfuse: `a67b649f7394f8a4770a3be2b380e73f` (mang cùng `correlation_id = req-1482a893`).
  - So sánh thời gian thực thi các span trong trace:
    - Root span `lab-agent-run`: tổng thời gian `2.653s`.
    - Child span `generation`: thời gian thực thi chỉ mất `0.151s` (hoàn toàn bình thường).
    - Child span `retrieval`: thời gian thực thi lên tới `2.501s` (chiếm hơn 94% tổng thời gian request).
- **Root cause:**
  - Điểm nghẽn nằm ở thao tác truy xuất dữ liệu ngữ cảnh (span `retrieval`) trong cơ chế RAG đối với chủ đề `monitoring` (mô phỏng qua sự cố `rag_slow` gây sleep 2.5s trong `app/mock_rag.py`). Tầng LLM generation hoạt động hoàn toàn bình thường (`ttft_ms = 50ms`, `generation = 0.151s`). Cả ba lớp bằng chứng Metrics (P95 spike), Logs (latency_ms ~2652ms trên feature monitoring), và Traces (span retrieval kéo dài 2.501s) đồng nhất chỉ về một nguyên nhân duy nhất là tắc nghẽn tại Vector Retrieval / Knowledge Base.
- **Fix action:**
  - Khôi phục hoạt động ngay lập tức: Gọi API `/incidents/rag_slow/disable` (thực thi `python scripts/inject_incident.py --disable`) để tắt cờ làm chậm retrieval.
  - Kiểm tra trạng thái tài nguyên CPU, RAM và kết nối mạng của Vector Store / Database; khởi động lại cluster hoặc replica retriever nếu có dấu hiệu treo connection pool.
  - Áp dụng bộ nhớ đệm (caching) cho các kết quả retrieval đối với các câu hỏi hoặc chủ đề thường gặp (`feature = monitoring`) để giảm tải cho vector search.
- **Preventive measure:**
  - Cấu hình Timeout nghiêm ngặt cho thao tác retrieval (ví dụ: `timeout = 1.5s`) kèm Fallback strategy (nếu retriever timeout, lập tức trả về tập tài liệu fallback đã cache hoặc trả lời trực tiếp mà không chặn đứng request).
  - Kích hoạt alert `HighLatencyP95` đã cấu hình trong `config/alert_rules.yaml` kết hợp runbook tại `docs/alerts.md#alert-1` để tự động thông báo qua Slack `#k4-l3b-alerts` ngay khi P95 vượt ngưỡng 3000ms trong 5 phút.
  - Thiết lập synthetic monitoring / health check định kỳ đo độ trễ riêng của thao tác vector search để phát hiện sớm hiện tượng suy giảm hiệu năng trước khi ảnh hưởng đến người dùng cuối.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  - Quyết định chuẩn hóa việc quản lý `correlation_id` tại `CorrelationIdMiddleware` bằng `structlog.contextvars.bind_contextvars` và đồng bộ vào Langfuse trace metadata qua `propagate_attributes`.
  - Lý do: Đảm bảo correlation ID luôn tồn tại duy nhất trên toàn bộ vòng đời của một request, tự động xuất hiện trong mọi bản ghi log và trace mà không cần truyền thủ công qua từng tham số hàm, tạo sợi dây liên kết bất biến giữa Logs và Traces.
- **Một lỗi/blocker đã gặp:**
  - Khi thiết lập child observation cho `FakeLLM.generate` bằng Langfuse SDK v4, việc truyền tham số `prompt` trực tiếp vào `update_current_generation` gây ra lỗi `AttributeError: 'ManagedPrompt' object has no attribute 'is_fallback'` trong test suite `test_agent_prompt_trace.py`.
- **Cách tìm nguyên nhân và xử lý:**
  - Truy vết traceback vào file `langfuse/_client/attributes.py` và `test_agent_prompt_trace.py`, phát hiện test mock không mô phỏng đầy đủ mọi thuộc tính nội bộ của `PromptClient`.
  - Đồng thời nghiên cứu cơ chế propagation của Langfuse v4 và nhận thấy context manager `propagate_attributes(prompt=prompt.managed_prompt)` ở tầng ngoài đã tự động đưa metadata prompt vào OpenTelemetry context.
  - Giải pháp: Để `propagate_attributes` tự động quản lý prompt linking mà không truyền đè tham số `prompt` vào `update_current_generation`. Cách này vừa giữ mã nguồn tinh gọn, tương thích hoàn toàn với unit test (25/25 passed), vừa bảo đảm trên Langfuse Cloud có đầy đủ liên kết tới prompt version.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - **Metrics (Phát hiện - Detection):** Cung cấp góc nhìn toàn cảnh về sức khỏe hệ thống. Cho biết *hiện tượng gì đang xảy ra* và *ở thời điểm nào* (ví dụ: Panel Latency báo động P95 tăng vọt từ ~152ms lên 2652ms lúc 12:30 UTC).
  - **Logs (Khoanh vùng - Localization):** Cung cấp ngữ cảnh cụ thể của sự cố. Cho biết *request nào bị ảnh hưởng* và *thuộc nghiệp vụ gì* (lọc log phát hiện các request có `feature = "monitoring"` với correlation_id `req-1482a893`).
  - **Traces (Chẩn đoán - Root Cause Analysis):** Mổ xẻ chi tiết luồng thực thi bên trong request. Cho biết *bước xử lý nào là thủ phạm* (mở trace ID `a67b649f...` thấy span `retrieval` mất 2.501s còn span `generation` chỉ mất 0.151s -> kết luận chính xác nghẽn tại vector search).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - **Prompt version & Rollback:** Tách biệt chu trình phát triển prompt khỏi chu kỳ release mã nguồn. Cho phép kỹ sư prompt thử nghiệm version mới và lập tức rollback về version cũ thông qua di chuyển label (`production` -> `v1`) khi phát hiện chất lượng suy giảm mà không cần build hay redeploy ứng dụng.
  - **Token & Cost:** LLM tiêu tốn chi phí trên từng token. Việc giám sát token input/output và cost giúp phát hiện sớm các hiện tượng prompt injection, context bloat hoặc mô hình bị loop lặp từ gây bùng nổ chi phí.
  - **SLO & Error Budget:** Đặt ra giới hạn định lượng rõ ràng cho trải nghiệm người dùng, giúp đội ngũ kỹ thuật cân bằng giữa tốc độ cập nhật tính năng mới và việc đầu tư ổn định hạ tầng.
- **Điều quan trọng nhất đã học:**
  - Nắm vững kiến trúc và phương pháp luận Observability cho hệ thống LLM: không chỉ giám sát tài nguyên máy chủ truyền thống mà phải đo lường các chỉ số đặc thù của AI (TTFT, token usage, retrieval latency, quality proxy).
  - Thành thạo quy trình điều tra sự cố chuẩn hóa 3 bước (Metrics → Logs → Traces), loại bỏ hoàn toàn việc đoán mò nguyên nhân.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  - Hiện tại metrics dashboard mới được trực quan hóa cục bộ và qua endpoint tích hợp của ứng dụng, chưa dựng pipeline chuyển tiếp tự động sang Prometheus/Grafana tập trung.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
