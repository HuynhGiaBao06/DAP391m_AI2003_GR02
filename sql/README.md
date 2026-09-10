# SQL

Migrations có phiên bản nằm trong `migrations/`; truy vấn đối soát/quality nằm trong `quality/`. Hiện chưa có migration, kết nối PostgreSQL hoặc schema đã tạo; tên bên dưới là hợp đồng dự kiến của Phase 2.

## Ranh giới trách nhiệm

- `staging`: dữ liệu ingestion tạm và trạng thái run.
- `raw`: nguồn đã đăng ký, token gốc và lineage.
- `processed`: analysis/snapshot cùng manifest và split mapping khi phù hợp.
- `audit`: quality result, sự kiện công bố và metadata truy vết.
- `results`: model/run/predictions/metrics/explanation/fairness đã công bố cho read service.

Tên schema/bảng cuối cùng phải được khóa trước migration đầu tiên. Python phụ trách preprocessing/model; SQL phụ trách lưu trữ, constraint, transaction, truy vấn và đối soát. Không duy trì hai phiên bản logic nghiệp vụ mâu thuẫn.

## Migration

Mỗi migration có version, mục đích, forward change, kiểm tra sau áp dụng và rollback hoặc recovery plan. Không sửa migration đã dùng trên DB chung; tạo migration mới. Thay đổi destructive cần backup/đánh giá tác động và quyền rõ trước khi chạy.

Notebook không chạy `drop`, `truncate`, `replace` hoặc migration. Tài khoản runtime tách quyền đọc, ingest và migration; connection detail lấy từ môi trường, không nằm trong SQL hay log.

## Ingestion và snapshot

Đăng ký source/config/schema bằng unique key đủ để chạy lại không nhân bản dữ liệu. Ingestion và công bố snapshot phải dùng transaction/advisory lock hoặc cơ chế tương đương đã kiểm dưới chạy đồng thời. Reader chỉ chọn `READY`; run `FAILED` không được xuất hiện như dữ liệu sẵn dùng.

Primary key/foreign key bảo vệ `source_id`, `record_id`, `snapshot_id`, `run_id` và `model_version`. Join predictions với analysis/split trong đúng snapshot/run, có kiểm một-một và row count.

## Quality SQL

Mỗi query quality có `rule_id`, tầng dữ liệu, severity, kỳ vọng và cách giới hạn sample ID. SQL và Python validator phải đối chiếu cùng định nghĩa; sai khác là lỗi hợp đồng cần điều tra, không chọn kết quả thuận lợi hơn.

Query phải xác định rõ NULL, token NA/Exempt, kiểu cast và denominator. Kiểm migration/query bằng fixture hoặc database tách biệt; không dùng DB chung làm môi trường test mặc định.
