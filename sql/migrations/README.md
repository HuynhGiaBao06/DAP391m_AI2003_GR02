# PostgreSQL migrations Phase 2

Migration chạy theo thứ tự tên file `*.up.sql`. Mỗi file forward là bất biến sau khi đã áp dụng trên database dùng chung; thay đổi tiếp theo phải tạo version mới. File `*.down.sql` là recovery có chủ đích, không được runner tự gọi và không dùng trên DB có dữ liệu cần giữ nếu chưa backup/xác nhận phạm vi.

- `001_hmda_phase2_schema.up.sql`: tạo schema/tables/views theo 18 cột thật trong `data/raw/state_NY_filter.csv`; tầng staging/raw giữ source token bằng `TEXT`.
- `002_hmda_phase2_permissions.up.sql`: tạo ba group role NOLOGIN và cấp quyền tối thiểu. Tài khoản đăng nhập thật được người quản trị Neon gán membership ngoài migration, không lưu username/password trong SQL.
- Reader chỉ được `SELECT` hai view lọc snapshot `READY`; không có quyền trên bảng staging/raw nền.

Chỉ áp dụng bằng tài khoản/branch test được phép DDL. Trước retry, đọc `hmda_audit.schema_migration`; không chạy file down như cách retry. TASK-022 đã xác minh quyền `CREATE ROLE`, forward/down, READY-only và reader ACL trên Neon PostgreSQL 18.6 branch test ngày 2026-09-11; test rollback toàn bộ và không phải lần deploy schema vào DB đích.
