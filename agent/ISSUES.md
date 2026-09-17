# Sổ vấn đề

Cập nhật: 2026-09-12. Giữ 12 mã RQ-I01–RQ-I12 và 5 mã TECH-001–TECH-005 từ Master; bổ sung 2 issue dữ liệu quan sát. TECH-004 đã `CLOSED` sau review độc lập Phase 1; các issue xuyên nhiều phase chỉ được cập nhật phần bằng chứng G1, không đóng thay cho gate sau.

## Cách ghi và đóng issue

Mỗi issue ghi loại (rủi ro/lỗi đã quan sát), trạng thái, ảnh hưởng, severity, owner/reviewer, nguồn, task và điều kiện đóng. Severity chỉ đánh giá sau khi biết tác động: CRITICAL (sai dữ liệu/kết quả hoặc lộ secret), MAJOR (chặn chức năng/gate), MINOR (phạm vi hạn chế). Các rủi ro hiện tại để UNASSESSED, không bịa mức độ từ một run chưa có.

OPEN → IN_PROGRESS khi có task xử lý → RESOLVED khi có evidence → CLOSED sau xác minh. Có thể REOPEN khi bằng chứng mới phủ định kết quả. Đầu ra mở rộng có thể NOT_APPLICABLE nếu có quyết định phạm vi, không dùng để bỏ gate bắt buộc.

Tên người thực hiện/reviewer và hạn hiện chưa phân công; vai trò dưới đây chỉ để điều phối. TASK-004–007 chuẩn bị Phase 0; TASK-009–024 phân rã Phase 1–2. Việc task tồn tại không thay test/runtime/data/DB evidence cần để đóng issue.

## RQ-I01 Thiết kế chưa là bằng chứng chạy; mỗi gate cần artifact/test thực.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 0–8.
- Owner/reviewer: chưa phân công; vai trò dự kiến Điều phối/QA. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Sai trạng thái nghiệm thu làm nhóm dùng kết quả chưa được kiểm.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-004](tasks/TASK-004.md), [TASK-005](tasks/TASK-005.md); review gate kỹ thuật gần hạn tại [TASK-015](tasks/TASK-015.md) và [TASK-024](tasks/TASK-024.md); phase sau tiếp tục tách khi đến lượt.
- Điều kiện giải quyết: Mỗi gate có checklist và bằng chứng thực cho đúng phạm vi; review trạng thái ở các phase liên quan.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I02 Thời điểm feature/missingness; loại hoặc đổi phạm vi khi không đủ căn cứ trước train.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 0, 3, 4.
- Owner/reviewer: chưa phân công; vai trò dự kiến Data/model. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Feature hoặc missingness sau quyết định gây leakage và sai mục tiêu dự đoán.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-004](tasks/TASK-004.md); task triển khai/kiểm thực tế sẽ tách khi đến phase.
- Điều kiện giải quyết: Danh mục thời điểm thông tin có nguồn; loại feature chưa đủ điều kiện hoặc điều chỉnh phạm vi trước train; kiểm schema/model tương ứng.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I03 Công thức GSV/SL, grouping, đa lớp; kiểm nhỏ trước chạy rộng.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 3, 5.
- Owner/reviewer: chưa phân công; vai trò dự kiến Research. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Áp dụng sai công thức hoặc grouping khiến RQ2 không có ý nghĩa đã nêu.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-006](tasks/TASK-006.md); task triển khai/kiểm thực tế sẽ tách khi đến phase.
- Điều kiện giải quyết: Đặc tả GSV/SL và kiểm bài toán nhỏ đối chiếu nghiệm đầy đủ đạt trước nghiên cứu rộng.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I04 Nhãn ba lớp, phê duyệt và denied; kiểm lại báo cáo/UI.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 4, 6–8.
- Owner/reviewer: chưa phân công; vai trò dự kiến Model/API. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Mapping hoặc diễn giải sai ba lớp làm sai metrics, giao diện và kết luận.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-004](tasks/TASK-004.md), [TASK-007](tasks/TASK-007.md); contract gần hạn tại [TASK-014](tasks/TASK-014.md) và data/schema thật tại [TASK-021](tasks/TASK-021.md); kiểm mapping model/API vẫn tách ở phase sau.
- Điều kiện giải quyết: Đối chiếu nhãn, thứ tự xác suất và báo cáo/UI; kiểm ví dụ và end-to-end tại phase triển khai.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi. Ngày 2026-09-11, TASK-021 quan sát file local dùng token nội bộ `0/1/2`; người dùng xác nhận đây là mapping chủ ý từ HMDA `1/2/3`. Contract dữ liệu đã đồng bộ nhưng kiểm model/API end-to-end chưa có, nên RQ-I04 vẫn OPEN; DATA-001 chuyển `RESOLVED`.

## RQ-I05 County thiếu mẫu; ngưỡng mẫu số, CI và metric không xác định.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 3, 6.
- Owner/reviewer: chưa phân công; vai trò dự kiến Research/fairness. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Nhóm ít mẫu hoặc mẫu số 0 làm gap/CI không đáng tin hoặc không xác định.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-006](tasks/TASK-006.md); task triển khai/kiểm thực tế sẽ tách khi đến phase.
- Điều kiện giải quyết: Chốt tiêu chí nhóm/mẫu số trước xem gap; lưu n, số dương/âm và trạng thái metric/CI đúng trên kết quả thật.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I06 Sex/geography/lei/year ngoài X; loại sex không bảo đảm fairness.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 2, 4.
- Owner/reviewer: chưa phân công; vai trò dự kiến Data/model. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Target/audit metadata vào X hoặc diễn giải loại sex là bảo đảm fairness.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-004](tasks/TASK-004.md), [TASK-007](tasks/TASK-007.md); contract gần hạn tại [TASK-014](tasks/TASK-014.md) và data/schema thật tại [TASK-021](tasks/TASK-021.md); kiểm X ở phase model/API vẫn tách sau.
- Điều kiện giải quyết: Kiểm X và schema API không chứa trường cấm; nối audit theo khóa, giữ đúng giới hạn diễn giải.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I07 Mất cân bằng và lớp 2; không gộp nhãn, không cân bằng test.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 3, 4.
- Owner/reviewer: chưa phân công; vai trò dự kiến Model. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Gộp nhãn hoặc cân bằng test làm thay đổi bài toán và phân bố đánh giá.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-004](tasks/TASK-004.md); TASK-021 kiểm target/cohort trên dữ liệu thật, còn split/balancing/model test sẽ tách ở Phase 3–4.
- Điều kiện giải quyết: Giữ ba lớp và phân bố validation/test theo protocol; kiểm split và báo cáo theo lớp.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I08 Nguồn, snapshot, split và join ID; đối soát end-to-end.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 2–8.
- Owner/reviewer: chưa phân công; vai trò dự kiến Data/QA. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Sai lineage hoặc join có thể mất/nhân dòng và ghép nhầm predictions.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-004](tasks/TASK-004.md); source identity/snapshot/data contract và integration gần hạn tại [TASK-017](tasks/TASK-017.md), [TASK-019](tasks/TASK-019.md), [TASK-021](tasks/TASK-021.md), [TASK-023](tasks/TASK-023.md) và [TASK-024](tasks/TASK-024.md); split/join ở phase sau tiếp tục tách khi đến lượt.
- Điều kiện giải quyết: Đối soát nguồn/snapshot/split và join theo khóa; manifests và integration test trên đầu ra thực.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi. Ngày 2026-09-11, TASK-017 triển khai source identity/hash/record ID; TASK-019 thêm manifest, atomic export và readback theo `record_id` bằng fixture. Split/join và đối soát end-to-end trên dữ liệu/DB thật chưa có nên issue vẫn OPEN.

## RQ-I09 Quy ước OvR/DPD/EOD và library version; kiểm ví dụ nhỏ.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 3, 6.
- Owner/reviewer: chưa phân công; vai trò dự kiến Research/fairness. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Quy ước OvR/gap khác nhau làm metrics không so sánh được.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-006](tasks/TASK-006.md); task triển khai/kiểm thực tế sẽ tách khi đến phase.
- Điều kiện giải quyết: Khóa định nghĩa/thứ tự nhóm/class và library version; kiểm ví dụ tính tay và đối chiếu implementation.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I10 Bất định và nhiều so sánh; không cherry-pick, bootstrap không đo retrain.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 4–6.
- Owner/reviewer: chưa phân công; vai trò dự kiến Research/model. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Cherry-pick hoặc CI bị diễn giải sai làm quá mức bằng chứng.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-004](tasks/TASK-004.md), [TASK-006](tasks/TASK-006.md); task triển khai/kiểm thực tế sẽ tách khi đến phase.
- Điều kiện giải quyết: Protocol chọn mẫu/so sánh và bootstrap rõ; báo giới hạn fixed-model, giữ kết quả bất lợi và kiểm nếu có nhiều giả thuyết.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I11 Bang đối chiếu là mở rộng; chọn trước, giữ model, không suy nhân quả kinh tế.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 6.
- Owner/reviewer: chưa phân công; vai trò dự kiến Research/data. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Dùng kết quả vùng khác sai phạm vi hoặc suy diễn nguyên nhân không có bằng chứng.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-004](tasks/TASK-004.md); task triển khai/kiểm thực tế sẽ tách khi đến phase.
- Điều kiện giải quyết: Kiểm hợp đồng region không refit; nếu không chạy thực ghi NOT RUN. Nếu chạy, có quyết định vùng, manifest và giới hạn kết luận.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## RQ-I12 Nguồn lực 10 tuần và SL; benchmark sớm, ưu tiên NY và dự phòng.

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 0, 3, 5, 8.
- Owner/reviewer: chưa phân công; vai trò dự kiến Điều phối/research. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Tính toán SL và mở rộng chiếm nguồn lực khiến phạm vi NY không hoàn thành.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có bằng chứng runtime hoặc evidence đóng issue.
- Task chuẩn bị: [TASK-005](tasks/TASK-005.md), [TASK-006](tasks/TASK-006.md); task triển khai/kiểm thực tế sẽ tách khi đến phase.
- Điều kiện giải quyết: Có benchmark/ước lượng có căn cứ khi triển khai và điều chỉnh phạm vi mở rộng được ghi nhận; giữ phần bắt buộc trong 10 tuần.
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

## TECH-001 Hai lần nạp ghi đè hoặc nhân bản dữ liệu

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 2.
- Owner/reviewer: chưa phân công; vai trò dự kiến Data/DB. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Trùng nguồn hoặc publish nửa chừng gây sai dữ liệu dùng chung.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có evidence triển khai hoặc đóng.
- Task triển khai: [TASK-020](tasks/TASK-020.md), [TASK-022](tasks/TASK-022.md), [TASK-023](tasks/TASK-023.md) và review [TASK-024](tasks/TASK-024.md).
- Điều kiện giải quyết: Kiểm concurrency, retry/idempotency và rollback trên DB; snapshot READY chỉ công bố toàn vẹn.
- Lịch sử: 2026-09-09 kế thừa từ Master. Ngày 2026-09-11, TASK-019 kiểm atomic publish/retry/identity collision, TASK-020 kiểm idempotency/rollback bằng fake và TASK-022 triển khai unique key, transaction, advisory lock cùng READY-only view; migration/recovery/ACL đã đạt trên Neon PostgreSQL 18.6 branch test. Chưa có concurrency ingestion thật nên issue vẫn OPEN.

## TECH-002 CSV/DB khác kiểu, mất token hoặc mã FIPS

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 2.
- Owner/reviewer: chưa phân công; vai trò dự kiến Data/QA. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Round-trip thay đổi ý nghĩa hoặc khóa định danh.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có evidence triển khai hoặc đóng.
- Task triển khai: [TASK-017](tasks/TASK-017.md)–[TASK-019](tasks/TASK-019.md), [TASK-021](tasks/TASK-021.md)–[TASK-024](tasks/TASK-024.md).
- Điều kiện giải quyết: Kiểm export/readback theo khóa và nội dung; giữ schema/token/count, checksum và recovery.
- Lịch sử: 2026-09-09 kế thừa từ Master. Ngày 2026-09-11, TASK-017 kiểm token/blank, source checksum và technical ID; TASK-018 thêm quality rule generic; TASK-019 kiểm serialization cấu hình được và readback theo khóa bằng fixture. TASK-021 đã đối chiếu schema/token file local và phát hiện `county_code` bị biểu diễn dạng số thực; TASK-022 giữ toàn bộ 18 cột raw bằng `TEXT` và migration đạt trên PostgreSQL 18.6. Chưa có DB round-trip nên issue vẫn OPEN và liên kết DATA-002.

## TECH-003 Artifact khác schema hoặc runtime

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 4, 7.
- Owner/reviewer: chưa phân công; vai trò dự kiến Model/API. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Nạp bundle hoặc suy luận không khớp đánh giá offline.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có evidence triển khai hoặc đóng.
- Task điều phối: [TASK-007](tasks/TASK-007.md); chưa tách task triển khai ở phase xa.
- Điều kiện giải quyết: Kiểm load, version/schema và xác suất offline/API trong tolerance đã khóa.
- Lịch sử: 2026-09-09 kế thừa từ Master; cấu trúc/rules đã có không đủ để đóng rủi ro này.

## TECH-004 Config hoặc secret rải rác

- Loại/trạng thái/severity: rủi ro thiết kế / CLOSED / UNASSESSED. Phase liên quan: 1.
- Owner: Agent theo yêu cầu người dùng. Reviewer: Agent độc lập theo yêu cầu người dùng; xác minh tại TASK-015 ngày 2026-09-12.
- Ảnh hưởng: Tham số không nhất quán hoặc lộ secret, đường dẫn lệ thuộc máy.
- Nguồn/bằng chứng: Project Master hiện hành; TASK-010–015; 27/27 test G1, import/root ba vị trí, compile, lock/dependency và kernel smoke ngày 2026-09-12.
- Task triển khai: [TASK-010](tasks/TASK-010.md)–[TASK-013](tasks/TASK-013.md); review gate tại [TASK-015](tasks/TASK-015.md).
- Điều kiện giải quyết: Config tập trung, kiểm thiếu/sai, path độc lập cwd và test logger không lộ secret; .gitignore riêng không đủ đóng mục này.
- Lịch sử: 2026-09-09 triển khai config tập trung, path độc lập `cwd`, secret redaction và logger idempotent; chuyển `RESOLVED`. Ngày 2026-09-11 bổ sung regression test redaction sau một lỗi ở tầng kết nối. Ngày 2026-09-12, review độc lập chạy lại bằng fixture không chứa secret thật, xác nhận config/logging/path và kernel đạt; chuyển `CLOSED` trong phạm vi Phase 1.

## TECH-005 State/task ghi DONE nhưng thiếu bằng chứng

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 0–8.
- Owner/reviewer: chưa phân công; vai trò dự kiến Điều phối/QA. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Nhóm tiếp tục dựa trên trạng thái sai.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có evidence triển khai hoặc đóng.
- Task review gần hạn: [TASK-015](tasks/TASK-015.md) cho G1 và [TASK-024](tasks/TASK-024.md) cho G2; các phase sau tiếp tục liên kết khi được phân rã.
- Điều kiện giải quyết: Đối chiếu tiêu chí và bằng chứng của task/gate; sửa trạng thái lệch, review khi bàn giao và tái lập cuối dự án.
- Lịch sử: 2026-09-09 kế thừa từ Master. Ngày 2026-09-12, tiêu chí và evidence G1 được review độc lập; TASK-009/TASK-015 chỉ chuyển `DONE` sau khi 27/27 test G1, compile, lock/dependency, import ba vị trí và kernel smoke đạt. Control này đạt cho G1 nhưng issue vẫn `OPEN` vì còn áp dụng cho các gate khác.

## Vấn đề mới từ dữ liệu thật

## DATA-001 Mapping `action_taken` chưa được ghi đúng vào contract

- Loại/trạng thái/severity: sai lệch contract / RESOLVED / CRITICAL trước xử lý. Phase liên quan: 2–8.
- Owner: Agent xử lý tại TASK-021. Reviewer: chưa phân công; cần xác minh khi review G2.
- Ảnh hưởng trước xử lý: quality rule coi 208.818/293.301 dòng có token `0` là lỗi và chặn snapshot, dù file filtered chủ ý dùng target zero-based.
- Nguồn/bằng chứng: người dùng xác nhận ngày 2026-09-11; mapping `0→HMDA 1 Loan originated`, `1→HMDA 2 Approved but not accepted`, `2→HMDA 3 Application denied`; phân bố `0=208.818`, `1=9.942`, `2=74.541` trên file hash `27f6dd99a55e07b9c95b943491c919ee0822d36790e900c999e35e884a095eee`.
- Task xử lý: [TASK-021](tasks/TASK-021.md); data/schema/quality config, protocol và source-contract test đã đồng bộ.
- Điều kiện đóng: reviewer xác nhận mapping được giữ đúng qua ingestion, model probability và API/report; trước đó giữ `RESOLVED`, không quay lại coi `0` là lỗi raw.
- Lịch sử: 2026-09-11 OPEN vì chưa biết mapping; cùng ngày người dùng xác nhận mapping chủ ý và implementation/test được sửa, chuyển RESOLVED.

## DATA-002 `county_code` bị xuất thành chuỗi số thực

- Loại/trạng thái/severity: lỗi dữ liệu quan sát / OPEN / MAJOR. Phase liên quan: 2, 3, 6.
- Owner: Agent ghi nhận tại TASK-021; người tạo/export dữ liệu cần cung cấp nguồn đúng kiểu. Reviewer: chưa phân công.
- Ảnh hưởng: 291.922/293.301 dòng nonblank có dạng như `36001.0`, không khớp FIPS 5 chữ số; có thể phá join, county grouping và fairness denominator. 1.379 dòng county blank được giữ riêng, không tự sửa.
- Nguồn/bằng chứng: đọc streaming toàn bộ cùng file/hash DATA-001; regex `^[0-9]{5}$` thất bại cho toàn bộ county nonblank; LEI 20 ký tự không có lỗi định dạng trong phép kiểm này.
- Task xử lý: [TASK-021](tasks/TASK-021.md) khóa source; TASK-023 kiểm round-trip sau khi có nguồn sửa đúng.
- Điều kiện giải quyết: tái xuất `county_code` dưới dạng string từ nguồn có provenance, bảo toàn token thiếu; không sửa file raw tại chỗ; chạy lại quality/source-contract test và review.

## Ghi vấn đề mới

Dùng mã mới không trùng (nhóm GOV cho vận hành, DATA cho dữ liệu, hoặc TECH cho kỹ thuật). Ghi ngày, phát hiện cụ thể, file/run bị ảnh hưởng, kỳ vọng và thực tế, cách tái hiện nếu có, mức độ có căn cứ, owner, task xử lý và kiểm tra đóng. Không dán dữ liệu cá nhân hoặc secret vào issue.
