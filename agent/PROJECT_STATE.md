# Trạng thái hiện tại

Cập nhật: 2026-09-12. Kiến trúc: [Project Master context](PROJECT_MASTER_CONTEXT.md) vẫn là điểm đọc hiện hành. **Phase 1 đã hoàn tất review độc lập; TASK-009–TASK-015 `DONE` và G1 đã nghiệm thu ngày 2026-09-12. G0 và G2–G8 chưa nghiệm thu; kết luận G1 không mở rộng thành bằng chứng cho phase khác.**

## Điểm dừng và bước tiếp tục

- [TASK-025](tasks/TASK-025.md) đã `DONE`: Project Master v1.2, Project Planning v1.2 và Research Plan v2.2 cùng dùng mortgage application funnel để nối denial với post-approval fallout; đã đối chiếu nguồn chính thức, kiểm cấu trúc và render 52/52 trang. Không chạy notebook/model/data/DB.
- Công việc vừa thực hiện theo yêu cầu trực tiếp: [TASK-021](tasks/TASK-021.md) đọc toàn bộ file HMDA tạm, ghi hash/schema/token/quality rules và source-contract test; raw không bị sửa, chưa kết nối DB.
- [TASK-009](tasks/TASK-009.md) và [TASK-015](tasks/TASK-015.md) đã `DONE`: reviewer độc lập đọc code/config/contract, chạy 27/27 test G1, compile, lock/dependency, import/root từ ba vị trí và kernel smoke. Kernelspec `hmda-project` bị thiếu tại đầu review, đã được đăng ký lại đúng `.venv` và xác minh thành công.
- Phase 0 và [TASK-001](tasks/TASK-001.md) tiếp tục `BACKLOG` chờ phê duyệt; theo yêu cầu người dùng, không dùng trạng thái này để chặn phần hạ tầng ổn định của Phase 1–2.
- TASK-017–TASK-020 đang `REVIEW`; TASK-021 giữ `IN_PROGRESS` vì county dạng `NNNNN.0` và chưa có source URL/version. TASK-022 đã `DONE`: migration, permissions, PostgreSQL adapter và integration test đều đạt trên branch test, không để lại fixture. TASK-023–TASK-024 chưa bắt đầu.
- Phiên hiện tại dừng sau khi đóng G1. Bất kỳ công việc Phase 2/DB nào tiếp theo phải bắt đầu bằng yêu cầu và phạm vi riêng của người dùng; không tự tiếp tục từ trạng thái G1 đã đạt.

## Những gì thực sự đã có

| Thành phần | Trạng thái và bằng chứng |
| --- | --- |
| Ba DOCX nghiên cứu | Project Master v1.2 và Project Planning v1.2 đã đồng bộ; Research Plan v2.2 là tài liệu làm việc. Business context đã kiểm nguồn/cấu trúc và render 52/52 trang tại TASK-025; hash Master hiện hành ở `PROJECT_MASTER_CONTEXT.md` |
| Cấu trúc/package/test | Package `hmda-project` 0.1.0 theo `src` layout; Python 3.13.9, `uv` 0.10.6, `uv.lock`; review độc lập G1 đạt 27/27 test mục tiêu, compile, lock/dependency, import/root ba vị trí và kernel smoke ngày 2026-09-12 |
| Notebook | 11 file Markdown-only, chưa có code/output hoặc kết quả nghiên cứu |
| Config | Loader/redaction/hash đã triển khai; loader nạp `configs/local.env` khi caller không truyền environment và ưu tiên biến process; DB có SSL/channel binding contract nhưng giữ `pending_connection` vì chưa thử kết nối. Data config chấp nhận target nội bộ `0/1/2`; source provenance/county còn PENDING |
| Runtime | `.venv` đã đồng bộ bằng uv 0.10.6; editable import từ project root, `notebooks/` và thư mục ngoài repo cùng trả đúng package/root; kernel `hmda-project` trỏ tới `.venv` và smoke test đạt |
| PostgreSQL | Driver, raw-first schema, hai cặp migration up/down, quyền migrator/ingest/reader và repository/UoW adapter đã có; forward/down, READY view và ACL đạt trên Neon PostgreSQL 18.6 branch test. Transaction rollback, chưa upload HMDA hoặc lưu schema vào DB đích |
| Dữ liệu và model local | `data/raw/state_NY_filter.csv`: 293.301 dòng, 18 cột, 27.427.263 bytes, hash đã ghi; mapping target đã xác nhận, source vẫn chưa publishable vì provenance và DATA-002. Chưa có model |
| Path/logging/contracts | Root/path, config, logging/exceptions, source identity/hash/record ID, CSV bytes loader, quality framework, snapshot/atomic export, repository/idempotency contract và PostgreSQL adapter đã triển khai; DB migration runtime đã kiểm, pipeline ingestion nghiệp vụ chưa triển khai |
| Hồ sơ agent | Rules/guideline/entry, state, issue, decision, research log; task Phase 0 và bộ TASK-009–024 cho Phase 1–2 đã có nội dung vận hành |
| Git | Các thay đổi được tách theo branch công việc và chỉ push lên đúng branch để người dùng tự review/merge trên GitHub; thay đổi mới vào file G1 phải được kiểm lại |
| Tài liệu dùng chung | Có `docs/README.md`, CONTRIBUTING, SECURITY, notebook guideline; protocol/paper/API/config/data/reproducibility/artifact/test/SQL đã thành bản nền có trạng thái và mục PENDING; data/model/deployment card vẫn chờ bằng chứng |

## Điều còn cần giải quyết

Trong 17 rủi ro kế thừa Master, TECH-004 đã `CLOSED` sau evidence và review độc lập Phase 1; 16 mục kế thừa còn lại giữ trạng thái riêng và không được đóng từ kết luận G1. TECH-005 ghi nhận control evidence/status đã đạt cho G1 nhưng vẫn `OPEN` vì áp dụng xuyên toàn dự án. Các issue ngoài Phase 1 không được xử lý trong phiên này.

Không đóng G0 chỉ vì bộ tài liệu nền đã có: protocol vẫn DRAFT; công thức paper/SL, bằng chứng thời điểm feature, xác nhận phân công/đầu việc và các quyết định PENDING còn thiếu. Không chốt preprocessing trước phân tích dữ liệu.

## Nơi tìm bằng chứng

- [TASK-000](tasks/TASK-000.md): scaffold, 17 file archive và hash hai DOCX.
- [TASK-002](tasks/TASK-002.md): README/Git ignore, 83 trường hợp kiểm tra.
- [TASK-003](tasks/TASK-003.md): hồ sơ agent, kiểm liên kết/trạng thái/ignore và giới hạn thay đổi.
- [TASK-008](tasks/TASK-008.md): workflow và template Git, quy tắc chia sẻ hiện hành, kiểm cấu trúc và nhật ký file của phiên.
- [TASK-009](tasks/TASK-009.md): task cha Phase 1 đã `DONE`; G1 đã nghiệm thu độc lập.
- [TASK-015](tasks/TASK-015.md): review độc lập 27/27 test G1, compile, lock/dependency, import/root ba vị trí và kernel smoke; kết luận `PASS` ngày 2026-09-12.
- [TASK-016](tasks/TASK-016.md): task cha Phase 2/G2, tách framework độc lập TASK-017–020 khỏi phần cần data/DB TASK-021–024.
- [TASK-017](tasks/TASK-017.md): source identity, SHA-256, deterministic `record_id` và CSV bytes loader; 13 targeted test đạt.
- [TASK-018](tasks/TASK-018.md): quality rule/result, ERROR/WARNING và publish guard; 5 targeted test đạt.
- [TASK-019](tasks/TASK-019.md): manifest/lifecycle, atomic CSV export, checksum và readback theo khóa; 16 targeted test đạt.
- [TASK-020](tasks/TASK-020.md): repository/UoW/idempotency contract bằng fake; 9 targeted test đạt.
- [TASK-021](tasks/TASK-021.md): profile đầy đủ source local, schema/token/quality rules và integration source-contract; mapping target đã xác nhận, còn chờ provenance/county trước review.
- [TASK-022](tasks/TASK-022.md): raw-first migrations, permission roles, PostgreSQL repository/UoW; 79 test offline đạt và targeted Neon PostgreSQL 18.6 integration 1/1 đạt.
- [TASK-025](tasks/TASK-025.md): business context có căn cứ, giới hạn diễn giải, hash ba DOCX và visual QA 52/52 trang.
- [_archive](../_archive/agent_generated/2026-09-09/README.md): lịch sử local đã cô lập; không phải nguồn chạy hoặc chỉ dẫn hiện hành.

Sau mỗi task có thay đổi, cập nhật điểm dừng/bước tiếp tục và dẫn tới evidence. Giữ chi tiết công việc ở task, không biến state thành nhật ký dài.
