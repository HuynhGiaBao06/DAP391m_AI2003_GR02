# Sổ quyết định

Phân biệt quyết định người dùng đã chốt với đề xuất/PENDING. Mỗi mục cần nguồn, ngày, trạng thái, phạm vi ảnh hưởng và liên kết evidence; không tự ghi người dùng đã duyệt.

## DEC-001 Kiến trúc được chấp nhận

Ngày 2026-09-09: người dùng chấp nhận Project Master v1.1. Agent dùng [Project Master context](PROJECT_MASTER_CONTEXT.md) để đọc nhanh; DOCX nguồn và hash được quản lý trong context. DOCX vẫn là nguồn chuẩn cho kiến trúc. Preprocessing giữ trạng thái chưa quyết định.

## DEC-002 Dựng cấu trúc và cô lập lịch sử

Ngày 2026-09-09: người dùng yêu cầu tạo cấu trúc theo Master và xóa hoặc cô lập file agent cũ. Đã chọn chuyển .tmp/ vào _archive/agent_generated/2026-09-09/legacy_tmp/ để giữ khả năng khôi phục. Chưa triển khai logic nghiệp vụ trong bước này.

## DEC-003 Hồ sơ agent và dữ liệu riêng tư chỉ lưu local

Ngày 2026-09-09: theo yêu cầu người dùng, .gitignore chặn CSV ở mọi thư mục, hồ sơ agent và file bí mật/cá nhân theo tên/vùng lưu trữ. Toàn bộ _archive/ và docs/ai_audit/ được loại khỏi Git. README là điểm vào dùng chung, không phụ thuộc file agent khi clone. Quyết định này thay cách giữ manifest/README archive trên Git trước đó; các file vẫn còn nguyên local. Chi tiết kiểm tra tại TASK-002.

Phạm vi chia sẻ hồ sơ agent của quyết định này được mở rộng bởi DEC-007; quy tắc chặn CSV, secret, dữ liệu cá nhân, archive và AI audit vẫn giữ nguyên.

## DEC-004 Hoàn thiện hồ sơ vận hành agent

- Ngày: 2026-09-09. Trạng thái: IMPLEMENTED trong phạm vi tài liệu được yêu cầu.
- Căn cứ: yêu cầu người dùng “Tiếp tục hoàn thành các file liên quan tới agent”.
- Thực hiện: rules/guideline/luồng vào phiên, state, issue, research log và task được hoàn thiện; bốn task gần hạn Phase 0 được phân rã.
- Giới hạn: không tự coi rules là quyền triển khai/train/ghi DB, không sửa kiến trúc Master hoặc chọn preprocessing. Các quy tắc vẫn có thể được người dùng sửa ở phiên sau.
- Bằng chứng: [TASK-003](tasks/TASK-003.md). Thay thế mô tả “rules chỉ là khung” trong trạng thái hiện tại; giữ lịch sử task cũ đúng thời điểm.

## DEC-005 Phân loại chế độ thao tác và báo cáo file theo phiên

- Ngày: 2026-09-09. Trạng thái: IMPLEMENTED trong phạm vi hồ sơ agent local.
- Căn cứ: yêu cầu người dùng bổ sung giới hạn làm việc cho đọc logic, xuất code, implement và review; đồng thời yêu cầu báo cáo file đã truy cập và chỉnh sửa trong mỗi phiên.
- Thực hiện: [AGENT_RULES](AGENT_RULES.md) định nghĩa bốn chế độ thao tác, các mức quyền từ chỉ đọc đến công bố/push, và nội dung tối thiểu của báo cáo file khi bàn giao.
- Giới hạn: không mở thêm quyền chạy notebook/pipeline, ghi dữ liệu/DB hoặc push/publish nếu yêu cầu phiên không giao rõ; hồ sơ agent tiếp tục chỉ lưu local theo DEC-003.

## DEC-006 Workflow và template Git dùng chung

- Ngày: 2026-09-09. Trạng thái: IMPLEMENTED trong phạm vi file tài liệu/template.
- Căn cứ: người dùng yêu cầu triển khai đề xuất gồm docs/git/WORKFLOW.md, docs/git/COMMIT_TEMPLATE.txt và .github/pull_request_template.md.
- Thực hiện: quy tắc nhánh/commit/review/merge/conflict và cách xem git log nằm trong workflow; agent và README tham chiếu cùng nguồn. Mẫu commit dùng qua --template, không cần đổi Git config; PR template phải được đưa lên nhánh mặc định để GitHub tự dùng.
- Kiểm trạng thái tại thời điểm TASK-008: đã có commit 7ad9dd4, nhánh feature/update_docs, và `.gitignore` khi đó có bốn ngoại lệ agent được theo dõi: GUIDELINES.md, DECISIONS.md, ISSUES.md, RESEARCH_LOG.md. Phạm vi này là bằng chứng lịch sử và đã được DEC-007 mở rộng.
- Giới hạn: không commit/push, không đổi branch/config, không cấu hình GitHub protections hoặc tạo GIT_LOG/CHANGELOG giả. Không chạy notebook/model/DB.
- Bằng chứng: TASK-008 local; ba file dùng chung có thể được review trực tiếp qua Git.

## DEC-007 Chia sẻ context, cấu hình vận hành và tiến độ agent

- Ngày: 2026-09-09. Trạng thái: ACCEPTED/IMPLEMENTED.
- Căn cứ: người dùng xác nhận chính mình đã mở rộng `.gitignore` vì các thành viên nên biết cấu hình và tiến độ dự án.
- Thực hiện: cho phép theo dõi Project Master context, rules, session start, project state, guidelines, decisions, issues và research log theo cấu hình hiện hành; task chi tiết, `AGENTS.md`, cấu hình trợ lý, archive và AI audit cá nhân vẫn local.
- Lý do: thành viên và agent dùng chung kiến trúc rút gọn, cách làm việc và điểm tiếp tục; tránh mỗi máy có trạng thái vận hành khác nhau.
- Điều kiện: rà soát secret, dữ liệu cá nhân, đường dẫn local và bằng chứng chỉ tồn tại trên một máy trước commit. Trạng thái Markdown không thay cơ chế đồng thời hoặc quyền chạy/ghi DB.

## DEC-008 Tách triển khai hạ tầng Phase 1–2 khỏi phê duyệt Phase 0

- Ngày: 2026-09-09. Trạng thái: ACCEPTED và đã phản ánh trong task backlog.
- Căn cứ: người dùng xác nhận Phase 0 tiếp tục chờ phê duyệt, nhưng phần hạ tầng ổn định của Phase 1 và framework Phase 2 có thể triển khai độc lập, không phải chờ Project Master thay đổi.
- Thực hiện: [TASK-009](tasks/TASK-009.md)–[TASK-015](tasks/TASK-015.md) phân rã Phase 1; [TASK-016](tasks/TASK-016.md)–[TASK-020](tasks/TASK-020.md) giữ phần Phase 2 có thể phát triển bằng config/fixture; [TASK-021](tasks/TASK-021.md)–[TASK-024](tasks/TASK-024.md) giữ phần cần HMDA/PostgreSQL thật.
- Ranh giới: core không hard-code cohort, năm, bang, danh sách cột, quality threshold hoặc preprocessing. Thay đổi phạm vi nghiên cứu được hấp thụ qua config/contract đã review; thay đổi phá vỡ interface vẫn phải review.
- Giới hạn quyền: quyết định này thay dependency tổ chức, không tự cấp quyền sửa code, cài/chạy, tải dữ liệu, kết nối/ghi DB hoặc công bố snapshot. G0–G2 vẫn chỉ đạt khi có đúng bằng chứng nghiệm thu.

## DEC-009 Runtime và dependency nền Phase 1

- Ngày: 2026-09-09 / xác minh 2026-09-12. Trạng thái: ACCEPTED/VERIFIED tại G1.
- Chọn Python 3.13.x, máy thử dùng 3.13.9; quản lý môi trường/lock bằng `uv` và `uv.lock`; package `hmda-project` dùng `src` layout và editable install.
- Runtime dependency hiện chỉ có PyYAML 6.x. Nhóm dev/test/notebook hiện chỉ có pytest 8.x và ipykernel 6.x; thư viện dữ liệu/model/API chỉ thêm khi task tương ứng thực sự cần.
- Kernel dùng tên `hmda-project`, display name `Python (HMDA Project)`, trỏ tới interpreter của `.venv`; không sửa `sys.path` trong notebook.
- Bằng chứng: TASK-010 và review độc lập TASK-015; 27/27 test G1, compile, lock/dependency, import/root ba vị trí và kernel smoke đạt ngày 2026-09-12. Quyết định đóng PEND-03 và G1; không chốt DB, data, preprocessing hoặc stack Phase 2–7.

## DEC-010 Business context cho bài toán HMDA ba lớp

- Ngày: 2026-09-12. Trạng thái: ACCEPTED/IMPLEMENTED theo yêu cầu trực tiếp của người dùng.
- Vấn đề kinh doanh: mortgage application funnel có hai điểm cần phân biệt — credit decision giữa phê duyệt/từ chối và post-approval conversion giữa khoản vay được phát sinh/`Approved but not accepted`.
- Cách nối RQ: RQ1 kiểm tra khả năng phân biệt cả denial và post-approval fallout; RQ2 mô tả đặc trưng quan sát được gắn với dự đoán từng lớp; RQ3 audit tỷ lệ nhãn, tỷ lệ dự đoán và error rate giữa Male/Female toàn bang và trong county đủ điều kiện.
- Giới hạn: New York và năm 2024 là phạm vi thực nghiệm; county là chiều địa lý của RQ3. HMDA không ghi nguyên nhân cụ thể của từng hồ sơ lớp 2, không đo trực tiếp chi phí/doanh thu/tổn thất hedging và không cho phép kết luận nhân quả, creditworthiness hoặc discrimination từ mô hình và group gaps.
- Phạm vi tài liệu: Project Master v1.2, Project Planning v1.2 và Research Plan v2.2. API/Web vẫn là deliverable triển khai trong Master nhưng nằm ngoài nội dung nghiên cứu RQ1–RQ3.
- Bằng chứng: CFPB Regulation C official interpretations; OCC Comptroller's Handbook, Mortgage Banking, Appendix B; CFPB Intent to Proceed; TASK-025.

## DEC-011 Phạm vi nghiệm thu Phase 2/G2 tối giản

- Ngày: 2026-09-13. Trạng thái: ACCEPTED/IMPLEMENTED trong đặc tả Phase 2 theo yêu cầu trực tiếp của người dùng.
- Mục tiêu bắt buộc của G2: thực hiện một round-trip thật local → PostgreSQL → local; đối soát số dòng, 18 business columns, kiểu/token raw, `record_id` và nội dung/checksum; lưu quality artifact và manifest; chỉ công bố snapshot `READY` khi transport integrity đạt.
- Source boundary: TASK-021 được phép `DONE` độc lập khi owner-attested local source identity, checksum, loader và transport-quality contract đạt. Trạng thái này không chứng minh ingestion, DB reconciliation, quality artifact, snapshot thật hoặc G2 đã đạt.
- Control giữ lại: transaction và rollback giao dịch khi upload lỗi; duplicate/idempotency protection cơ bản; run lỗi không được reader thấy như `READY`.
- Phần hoãn khỏi G2 hiện tại: concurrency stress giữa nhiều ingestion, restore drill, reviewer độc lập và generic pipeline cho nhiều bảng. Các phần này không được mô tả là đã kiểm và issue vận hành rộng hơn vẫn có thể giữ `OPEN`.
- Quan hệ với Project Master: đây là ngoại lệ vận hành có chủ đích cho G2 tối giản, không sửa hoặc ghi đè DOCX nguồn. Các yêu cầu cốt lõi về source, quality, reconciliation và snapshot `READY` vẫn giữ nguyên.
- Giới hạn quyền: quyết định này chỉ đồng bộ phạm vi và trạng thái; không tự cấp quyền sửa pipeline/SQL, kết nối hoặc ghi DB, chạy ingestion, tạo/công bố snapshot, commit hoặc push.
- Áp dụng: TASK-016–TASK-024 liên quan, `PROJECT_MASTER_CONTEXT.md`, `PROJECT_STATE.md`, task index, TECH-001 và PEND-04.

## DEC-012 PostgreSQL đích và snapshot root cho TASK-023

- Ngày: 2026-09-13. Trạng thái: ACCEPTED/IMPLEMENTED; target đã deploy và round-trip được TASK-024 nghiệm thu ngày 2026-09-14.
- Database đích: `neondb`, là tên database thực tế được cấp trên endpoint Neon. Tên nhận diện dự kiến trước đó được thay thế bởi xác nhận người dùng ngày 2026-09-13.
- Cấu trúc dùng lại từ migration TASK-022, không tạo contract table mới: staging `hmda_staging.hmda_record`, raw `hmda_raw.hmda_record`, audit trong `hmda_audit`, reader dùng `hmda_raw.ready_hmda_record` và `hmda_audit.ready_snapshot`.
- Snapshot local: `data/snapshots/eda/<snapshot_id>/`, gồm `data.csv`, manifest và quality report theo hợp đồng snapshot hiện hành.
- Quyền dự kiến: BaoHG là data admin/writer; tài khoản thành viên được phép đọc thông qua role/view `hmda_reader`. “Cho phép tất cả đọc” nghĩa là mọi tài khoản dự án được cấp quyền, không cấp quyền cho PostgreSQL `PUBLIC` hoặc truy cập ẩn danh.
- Trạng thái kết nối: đã xác minh read-only ngày 2026-09-13 bằng config local đã che secret; kết nối thành công tới `neondb` với PostgreSQL 18.6 và đúng user cấu hình. Lỗi `ENOTFOUND base`, password cũ và hai tên database dự kiến không còn là trạng thái hiện hành.
- DDL boundary và triển khai: tài khoản hiện hành có database `CREATE` và `CREATEROLE`. Theo quyền người dùng giao cho Bước 3A ngày 2026-09-13, migration forward `001`/`002` đã được áp dụng trong một transaction trên `neondb`; ba schema, các table/view và role HMDA đã được kiểm bằng truy vấn read-only. Chạy lại migration runner không áp dụng thêm version nào. Block 3B ghi fixture 2 dòng trong transaction rồi rollback; Block 3C ngày 2026-09-14 persist một ingestion/snapshot READY đủ 293.301 dòng và snapshot local theo đúng contract này. TASK-024 đã review và đóng G2 tối giản cùng ngày.
- Áp dụng: `configs/database.yaml`, TASK-016/023, `PROJECT_STATE.md`, task index, PEND-04, `configs/README.md`, `data/README.md` và `sql/README.md`.

## Các quyết định còn chờ

Đây là câu hỏi điều phối, không phải thông số hoặc phương án đã chọn. Tên owner và ngày cụ thể chưa phân công; TASK-005 thu thập xác nhận thật, không tự điền.

| Mã | Nội dung đang chờ | Trạng thái | Cần chốt khi nào | Task chuẩn bị |
| --- | --- | --- | --- | --- |
| PEND-01 | Tên owner/reviewer và hạn cho các đầu việc | PENDING | G0 | TASK-005 |
| PEND-02 | Lịch học phần, AI services và yêu cầu RQ mới | PENDING | Phạm vi sản phẩm trước G0; xác nhận với nhóm/giảng viên qua người dùng | TASK-005, TASK-007 |
| PEND-04 | Nơi phân phối snapshot/artifact cho nhóm; source local, database `neondb`, local snapshot root, kết nối, quyền DDL, migrations và G2 local round-trip đã giải quyết | PENDING | Trước khi phân phối cho nhóm; không phủ định G2 local đã nghiệm thu | TASK-005 điều phối nơi phân phối; snapshot local hiện hành theo DEC-012 |
| PEND-05 | Phương án preprocessing và feature đủ điều kiện | PENDING | Sau phân tích/kiểm tra, trước train chính thức G4 | TASK-004 chỉ chuẩn bị câu hỏi |
| PEND-06 | Chi tiết công thức SL, mẫu, seed và ngưỡng fairness còn mở | PENDING | Trước thực nghiệm tương ứng | TASK-006 chuẩn bị đặc tả |
| PEND-07 | Frontend/hosting và mục tiêu hiệu năng đo được | PENDING | Trước tích hợp/nghiệm thu Phase 7 | TASK-007 chuẩn bị hợp đồng |
| PEND-08 | Có chạy bang đối chiếu thực và chọn vùng nào | PENDING | Sau điều kiện NY và trước chạy mở rộng | TASK-004 ghi ranh giới; chưa có quyết định chạy |

Các chi tiết đã chốt trong Planning không bị đưa về chưa chốt bởi bảng này; chỉ ghi phần còn mở. Tham số khi được chọn vẫn lưu duy nhất trong configs/.

## Ghi quyết định tiếp theo

Dùng DEC-xxx mới. Ghi câu hỏi, trạng thái PROPOSED/ACCEPTED/IMPLEMENTED/SUPERSEDED, căn cứ người chốt và ngày, lý do, phạm vi/file bị ảnh hưởng, evidence/issue và điều kiện xem xét lại. Một đề xuất của agent chưa có xác nhận phải giữ PROPOSED khi cần người dùng quyết định. Khi thay thế, dẫn tới quyết định mới và giữ lịch sử cũ.
