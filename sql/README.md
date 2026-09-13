# SQL

Migrations có phiên bản nằm trong `migrations/`; truy vấn đối soát/quality nằm trong `quality/`. Migration Phase 2 và PostgreSQL adapter đã được chuẩn bị offline nhưng chưa áp dụng vào Neon hoặc bất kỳ DB thật nào.

## Ranh giới trách nhiệm

- `staging`: dữ liệu ingestion tạm và trạng thái run.
- `raw`: nguồn đã đăng ký, token gốc và lineage.
- `processed`: analysis/snapshot cùng manifest và split mapping khi phù hợp.
- `audit`: quality result, sự kiện công bố và metadata truy vết.
- `results`: model/run/predictions/metrics/explanation/fairness đã công bố cho read service.

Schema hiện hành là `hmda_staging`, `hmda_raw` và `hmda_audit`; các bảng raw giữ nguyên 18 token nguồn dưới dạng `TEXT`. Python phụ trách preprocessing/model; SQL phụ trách lưu trữ, constraint, transaction, truy vấn và đối soát. Không duy trì hai phiên bản logic nghiệp vụ mâu thuẫn.

## Migration

`001_hmda_phase2_schema` tạo schema, bảng, constraint và view READY; `002_hmda_phase2_permissions` tạo group role và quyền tối thiểu. Mỗi migration có cặp `.up.sql`/`.down.sql`; file đã áp dụng trên DB không được sửa mà phải tạo version mới. Các file down là recovery cho DB test hoặc tình huống đã đánh giá tác động, không phải lệnh rollback mặc định trên DB dùng chung.

Notebook không chạy `drop`, `truncate`, `replace` hoặc migration. Tài khoản runtime tách quyền đọc, ingest và migration; connection detail lấy từ môi trường, không nằm trong SQL hay log. Migration dùng cú pháp tương thích PostgreSQL 14 trở lên; phiên bản Neon thực tế vẫn phải được xác minh khi có quyền DB.

## Ingestion và snapshot

Đăng ký source/config/schema bằng unique key đủ để chạy lại không nhân bản dữ liệu. Ingestion và công bố snapshot phải dùng transaction/advisory lock hoặc cơ chế tương đương đã kiểm dưới chạy đồng thời. Reader chỉ chọn `READY`; run `FAILED` không được xuất hiện như dữ liệu sẵn dùng.

Primary key/foreign key bảo vệ `source_id`, `record_id`, `snapshot_id`, `run_id` và `model_version`. Join predictions với analysis/split trong đúng snapshot/run, có kiểm một-một và row count.

## Quality SQL

Mỗi query quality có `rule_id`, tầng dữ liệu, severity, kỳ vọng và cách giới hạn sample ID. SQL và Python validator phải đối chiếu cùng định nghĩa; sai khác là lỗi hợp đồng cần điều tra, không chọn kết quả thuận lợi hơn.

Query phải xác định rõ NULL, token NA/Exempt, kiểu cast và denominator. Kiểm migration/query bằng fixture hoặc database tách biệt; không dùng DB chung làm môi trường test mặc định.
