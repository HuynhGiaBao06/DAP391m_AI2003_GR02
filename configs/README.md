# Cấu hình tập trung

`configs/` là nơi duy nhất chỉnh tham số dùng chung của dự án. `database.yaml` ghi database Neon thực tế `neondb` và snapshot root theo DEC-012; host/user/password vẫn lấy từ môi trường. Kết nối, quyền DDL, migration `001`/`002` và Block 3C round-trip 293.301 record đã được TASK-024 xác minh trên database đích; G2 tối giản đóng ngày 2026-09-14. TASK-021 đã ghi schema quan sát, hash và 25 quality rules cho file local `state_NY_filter.csv`; owner-attested source đạt transport contract còn `county_code` giữ `analysis_ready=false`. Các giá trị training và evaluation vẫn `PENDING`. Kiến trúc gốc nằm trong [Project Master](../docs/HMDA_Project_Master_Main.docx); quyết định thực nghiệm nằm trong [protocol](../docs/protocol.md).

## Trách nhiệm từng file

| File | Nội dung được phép chứa | Không được chứa |
| --- | --- | --- |
| `project.yaml` | Tên dự án, marker root, đường dẫn tương đối, quy ước ID/version | Đường dẫn home của một thành viên |
| `database.yaml` | Host/port/database/schema theo biến môi trường, pool/timeout không bí mật | Password, token hoặc connection URI thật |
| `data.yaml` | Nguồn, năm/bang, cohort filter, vị trí raw/snapshot | Quy tắc preprocessing học từ dữ liệu |
| `schema.yaml` | Tên cột, kiểu, nullable, unit, role, allowed token/category | Giá trị quan sát bịa hoặc schema chưa đối chiếu nhưng ghi như đã xác minh |
| `quality.yaml` | `rule_id`, severity, tolerance và tầng áp dụng | Quy tắc tự sửa/xóa dữ liệu để vượt gate |
| `preprocessing.yaml` | Phương án đã được duyệt sau phân tích | Giá trị mặc định tạm, secret hoặc quyết định chưa duyệt |
| `training.yaml` | Split, seed, model candidates, search budget | Metric fairness hoặc kết quả chạy |
| `evaluation.yaml` | Metric RQ1, GSV/SL, fairness, region và ngưỡng đã khóa | Số liệu kết quả hoặc lựa chọn sửa sau khi xem test |
| `logging.yaml` | Level, handler, format, redaction và trường context | Payload/hồ sơ đầy đủ hoặc đường dẫn log cá nhân cố định |
| `local.env.example` | Tên biến môi trường và giá trị minh họa an toàn | Secret thật |

## Nạp và kiểm cấu hình

`ConfigLoader` đọc các YAML bắt buộc thành một `ConfigBundle`. Khi caller không truyền mapping môi trường tường minh, loader nạp `configs/local.env` nếu file tồn tại rồi để biến môi trường của process ghi đè; test có thể truyền `environment={}` để không chạm secret local. Override chỉ được thay đường dẫn trường đã tồn tại; sau đó tham chiếu môi trường được resolve cho secret/địa chỉ triển khai. Không đọc tham số từ `cwd`, cell notebook hoặc một file YAML thứ hai trong artifact như nguồn chỉnh sửa.

Loader cấu hình dừng sớm khi thiếu file bắt buộc, root YAML không phải mapping, root marker/path project sai, logging level không hợp lệ, override không tồn tại hoặc preprocessing còn pending nhưng có method. Quality validator kiểm 25 rule HMDA hiện hành, gồm checksum, exact column order, row count, token, định dạng chuỗi, khả năng parse số và exact-row excess. `observed_evidence` là profiling snapshot, không phải `ValidationSummary`; summary phải được sinh trong lần chạy. Source registration guard hỗ trợ hai mode có kiểm soát: external URL đã xác minh hoặc local derived asset có owner attestation đầy đủ; cả hai vẫn yêu cầu version, checksum, `publishable=true` và không còn transport blocker. Mapping target đã xác nhận; feature timing, county normalization và split chưa được chốt.

Validation trả lỗi có `field_path` và thông điệp có thể xử lý, nhưng không in secret. Resolved config có bản redacted, serialization chuẩn hóa và SHA-256 `config_hash`; hash này là hạ tầng, chưa phải ID của một run/snapshot thật.

## Đường dẫn và môi trường

Đường dẫn tương đối được giải từ project root do `src/hmda/core/path.py` tìm bằng `__file__` và marker `pyproject.toml` cùng `src/hmda`; không dùng hoặc fallback về `cwd`. Đường dẫn dữ liệu/artifact ngoài repository phải được khai báo tường minh cho môi trường đó.

`configs/local.env` là file local bị Git loại trừ. Môi trường triển khai nên cấp secret bằng cơ chế của nền tảng, không đóng gói file secret vào image/artifact.

## Đóng băng cấu hình cho snapshot và run

Khi pipeline hoạt động, mỗi snapshot/run lưu bản cấu hình đã resolve và che secret, cùng `config_hash`, `code_version` và schema/protocol version. Hash dùng trên dạng serialization chuẩn hóa đã được định nghĩa; không coi hai file có thứ tự key khác là hai cấu hình nghiệp vụ khác nếu loader chuẩn hóa chúng giống nhau.

Bản cấu hình trong artifact là bằng chứng đã dùng, không phải nguồn để chỉnh tham số. Chạy lại từ artifact phải kiểm version và từ chối secret bị thiếu bằng lỗi rõ.

## Trạng thái chưa chốt

Preprocessing tiếp tục để trống đến khi hoàn tất data quality, EDA gần raw và thử nghiệm train/validation. Python/dependency lock đã chốt ở Phase 1; database đích hiện hành là `neondb`, nơi schema PostgreSQL raw-first, READY views và ba role runtime đã được deploy bằng migration `001`/`002`. Record transport thật đạt tại TASK-023 với 293.301 raw/READY record, persisted quality và snapshot local; TASK-024 đã nghiệm thu G2 tối giản. Ngưỡng fairness, region, frontend/hosting và latency chưa được điền cho tới khi có quyết định/bằng chứng tương ứng.
