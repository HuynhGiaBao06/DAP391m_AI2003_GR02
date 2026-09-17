# Trạng thái hiện tại

Cập nhật: 2026-09-14. Kiến trúc: [Project Master context](PROJECT_MASTER_CONTEXT.md) vẫn là điểm đọc hiện hành. **Phase 1/G1 đã nghiệm thu ngày 2026-09-12; Phase 2/G2 tối giản đã nghiệm thu ngày 2026-09-14. G0 và G3–G8 chưa nghiệm thu; kết luận G1/G2 không mở rộng thành bằng chứng cho phase khác.**

## Điểm dừng và bước tiếp tục

- [TASK-025](tasks/TASK-025.md) đã `DONE`: Project Master v1.2, Project Planning v1.2 và Research Plan v2.2 cùng dùng mortgage application funnel để nối denial với post-approval fallout; đã đối chiếu nguồn chính thức, kiểm cấu trúc và render 52/52 trang. Không chạy notebook/model/data/DB.
- Công việc vừa thực hiện theo yêu cầu trực tiếp: TASK-024 đã đọc lại source/config/code/evidence, tính lại checksum local↔READY DB trên đủ 293.301 dòng, chạy lại quality, hash snapshot, kiểm status/count/type/ACL và full regression. Kết luận PASS G2 tối giản; 116 test đạt, 1 DB-DDL test tách biệt skipped đúng điều kiện môi trường.
- [TASK-009](tasks/TASK-009.md) và [TASK-015](tasks/TASK-015.md) đã `DONE`: reviewer độc lập đọc code/config/contract, chạy 27/27 test G1, compile, lock/dependency, import/root từ ba vị trí và kernel smoke. Kernelspec `hmda-project` bị thiếu tại đầu review, đã được đăng ký lại đúng `.venv` và xác minh thành công.
- Phase 0 và [TASK-001](tasks/TASK-001.md) tiếp tục `BACKLOG` chờ phê duyệt; theo yêu cầu người dùng, không dùng trạng thái này để chặn phần hạ tầng ổn định của Phase 1–2.
- TASK-016–TASK-024 đều `DONE`; G2 đóng theo phạm vi tối giản của DEC-011. Snapshot `hmda-2024-ny-ab0bb683a84aabbbbcc09afc` là READY transport input cho Phase 3.
- Bước tiếp theo duy nhất là chốt task/phạm vi Phase 3 trước khi chạy: EDA gần raw có thể dùng snapshot READY, nhưng mọi phân tích county phải chờ xử lý DATA-002 bằng transformation có version. Chưa có quyền tự chạy notebook, EDA, preprocessing hoặc model trong lượt này.

## Những gì thực sự đã có

| Thành phần | Trạng thái và bằng chứng |
| --- | --- |
| Ba DOCX nghiên cứu | Project Master v1.2 và Project Planning v1.2 đã đồng bộ; Research Plan v2.2 là tài liệu làm việc. Business context đã kiểm nguồn/cấu trúc và render 52/52 trang tại TASK-025; hash Master hiện hành ở `PROJECT_MASTER_CONTEXT.md` |
| Cấu trúc/package/test | Package `hmda-project` 0.1.0 theo `src` layout; Python 3.13.9, `uv` 0.10.6, `uv.lock`; review độc lập G1 đạt 27/27 test mục tiêu, compile, lock/dependency, import/root ba vị trí và kernel smoke ngày 2026-09-12 |
| Notebook | 11 file Markdown-only, chưa có code/output hoặc kết quả nghiên cứu |
| Config | Loader/redaction/hash đã triển khai; `database.yaml` và local environment cùng dùng database `neondb`. PostgreSQL 18.6, kết nối, quyền DDL, migrations và round-trip thật đã được xác minh. Data config chấp nhận target nội bộ `0/1/2`; source dùng owner-attested internal version; county là analytical warning, không phải transport error |
| Runtime | `.venv` đã đồng bộ bằng uv 0.10.6; editable import từ project root, `notebooks/` và thư mục ngoài repo cùng trả đúng package/root; kernel `hmda-project` trỏ tới `.venv` và smoke test đạt |
| PostgreSQL | Driver, raw-first schema, migration forward, quyền migrator/ingest/reader và repository/UoW adapter đã có. `neondb` giữ 1 source, 1 ingestion READY, 1 snapshot READY, 1 quality result và 293.301 raw/READY records; staging=0. Migration down không chạy trong Block 3C |
| Dữ liệu và model local | `data/raw/state_NY_filter.csv`: 293.301 dòng, 18 cột, 27.427.263 bytes, hash đã ghi; mapping target và owner attestation của BaoHG đã được xác nhận. Source đủ điều kiện transport theo local contract; DATA-002 vẫn chặn dùng county trực tiếp cho phân tích. Chưa có model |
| Path/logging/contracts | Root/path, config, logging/exceptions, source identity/hash/record ID, CSV bytes loader, source registration guard, 25 HMDA quality rules, record-level COPY/promote/readback/reconciliation và snapshot atomic ba file đã triển khai, chạy trên toàn bộ HMDA và được TASK-024 nghiệm thu |
| Hồ sơ agent | Rules/guideline/entry, state, issue, decision, research log; task Phase 0 và bộ TASK-009–024 cho Phase 1–2 đã có nội dung vận hành |
| Git | Các thay đổi được tách theo branch công việc và chỉ push lên đúng branch để người dùng tự review/merge trên GitHub; thay đổi mới vào file G1 phải được kiểm lại |
| Tài liệu dùng chung | Có `docs/README.md`, CONTRIBUTING, SECURITY, notebook guideline; protocol/paper/API/config/data/reproducibility/artifact/test/SQL đã thành bản nền có trạng thái và mục PENDING; data/model/deployment card vẫn chờ bằng chứng |

## Điều còn cần giải quyết

Trong 17 rủi ro kế thừa Master, TECH-004 đã `CLOSED` sau G1 và TECH-002 đã `CLOSED` cho transport sau G2; 15 mục kế thừa còn lại giữ trạng thái riêng và không được đóng từ kết luận G1/G2. TECH-005 ghi nhận control evidence/status đã đạt cho G1/G2 nhưng vẫn `OPEN` vì áp dụng xuyên toàn dự án. DATA-002 và các issue phase sau không được đóng từ G2 transport.

Không đóng G0 chỉ vì bộ tài liệu nền đã có: protocol vẫn DRAFT; công thức paper/SL, bằng chứng thời điểm feature, xác nhận phân công/đầu việc và các quyết định PENDING còn thiếu. Không chốt preprocessing trước phân tích dữ liệu.

## Nơi tìm bằng chứng

- [TASK-000](tasks/TASK-000.md): scaffold, 17 file archive và hash hai DOCX.
- [TASK-002](tasks/TASK-002.md): README/Git ignore, 83 trường hợp kiểm tra.
- [TASK-003](tasks/TASK-003.md): hồ sơ agent, kiểm liên kết/trạng thái/ignore và giới hạn thay đổi.
- [TASK-008](tasks/TASK-008.md): workflow và template Git, quy tắc chia sẻ hiện hành, kiểm cấu trúc và nhật ký file của phiên.
- [TASK-009](tasks/TASK-009.md): task cha Phase 1 đã `DONE`; G1 đã nghiệm thu độc lập.
- [TASK-015](tasks/TASK-015.md): review độc lập 27/27 test G1, compile, lock/dependency, import/root ba vị trí và kernel smoke; kết luận `PASS` ngày 2026-09-12.
- [TASK-016](tasks/TASK-016.md): task cha Phase 2/G2, tách framework độc lập TASK-017–020 khỏi phần cần data/DB TASK-021–024.
- [TASK-017](tasks/TASK-017.md): source identity, SHA-256, deterministic `record_id`, CSV bytes loader và source registration guard; source/loader regression hiện tại 28/28 đạt.
- [TASK-018](tasks/TASK-018.md): quality rule/result, ERROR/WARNING, publish guard và rule shape/exact-row; validator regression hiện tại 8/8 đạt.
- [TASK-019](tasks/TASK-019.md): manifest/lifecycle, atomic CSV export, checksum và readback theo khóa; 16 targeted test đạt.
- [TASK-020](tasks/TASK-020.md): repository/UoW/idempotency contract bằng fake; 9 targeted test đạt.
- [TASK-021](tasks/TASK-021.md): `DONE`; owner-attested identity và integration config→registration→loader→validator→transport guard đạt; TASK-024 xác minh contract được bảo toàn qua DB/snapshot.
- [TASK-023](tasks/TASK-023.md): `DONE`; round-trip thật `ing-ab0bb683a84aabbbbcc09afc` / `hmda-2024-ny-ab0bb683a84aabbbbcc09afc`, 293.301 record, 0 ERROR, 3 WARNING, snapshot và checksum đã được TASK-024 nghiệm thu.
- [TASK-024](tasks/TASK-024.md): `DONE`; review gate PASS G2 tối giản ngày 2026-09-14.
- [TASK-022](tasks/TASK-022.md): raw-first migrations, permission roles, PostgreSQL repository/UoW; 79 test offline đạt và targeted Neon PostgreSQL 18.6 integration 1/1 đạt.
- [TASK-025](tasks/TASK-025.md): business context có căn cứ, giới hạn diễn giải, hash ba DOCX và visual QA 52/52 trang.
- [_archive](../_archive/agent_generated/2026-09-09/README.md): lịch sử local đã cô lập; không phải nguồn chạy hoặc chỉ dẫn hiện hành.

Sau mỗi task có thay đổi, cập nhật điểm dừng/bước tiếp tục và dẫn tới evidence. Giữ chi tiết công việc ở task, không biến state thành nhật ký dài.
