# Sổ vấn đề

Cập nhật: 2026-09-09. Giữ 12 mã RQ-I01–RQ-I12 và 5 mã TECH-001–TECH-005 từ Master. TECH-004 đã `RESOLVED` bằng evidence Phase 1 và chờ review độc lập để `CLOSED`; các mục còn lại giữ `OPEN`.

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
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

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
- Lịch sử: 2026-09-09 kế thừa từ Master và bổ sung cách theo dõi; vẫn OPEN.

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
- Lịch sử: 2026-09-09 kế thừa từ Master; cấu trúc/rules đã có không đủ để đóng rủi ro này.

## TECH-002 CSV/DB khác kiểu, mất token hoặc mã FIPS

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 2.
- Owner/reviewer: chưa phân công; vai trò dự kiến Data/QA. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Round-trip thay đổi ý nghĩa hoặc khóa định danh.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có evidence triển khai hoặc đóng.
- Task triển khai: [TASK-017](tasks/TASK-017.md)–[TASK-019](tasks/TASK-019.md), [TASK-021](tasks/TASK-021.md)–[TASK-024](tasks/TASK-024.md).
- Điều kiện giải quyết: Kiểm export/readback theo khóa và nội dung; giữ schema/token/count, checksum và recovery.
- Lịch sử: 2026-09-09 kế thừa từ Master; cấu trúc/rules đã có không đủ để đóng rủi ro này.

## TECH-003 Artifact khác schema hoặc runtime

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 4, 7.
- Owner/reviewer: chưa phân công; vai trò dự kiến Model/API. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Nạp bundle hoặc suy luận không khớp đánh giá offline.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có evidence triển khai hoặc đóng.
- Task điều phối: [TASK-007](tasks/TASK-007.md); chưa tách task triển khai ở phase xa.
- Điều kiện giải quyết: Kiểm load, version/schema và xác suất offline/API trong tolerance đã khóa.
- Lịch sử: 2026-09-09 kế thừa từ Master; cấu trúc/rules đã có không đủ để đóng rủi ro này.

## TECH-004 Config hoặc secret rải rác

- Loại/trạng thái/severity: rủi ro thiết kế / RESOLVED / UNASSESSED. Phase liên quan: 1.
- Owner: Agent theo yêu cầu người dùng. Reviewer: chưa phân công; xác minh tại TASK-015.
- Ảnh hưởng: Tham số không nhất quán hoặc lộ secret, đường dẫn lệ thuộc máy.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; TASK-010–015, 22/22 unit test, import ngoài repo và kernel smoke ngày 2026-09-09.
- Task triển khai: [TASK-010](tasks/TASK-010.md)–[TASK-013](tasks/TASK-013.md) và DB config/security tại [TASK-022](tasks/TASK-022.md).
- Điều kiện giải quyết: Config tập trung, kiểm thiếu/sai, path độc lập cwd và test logger không lộ secret; .gitignore riêng không đủ đóng mục này.
- Lịch sử: 2026-09-09 triển khai config tập trung, path độc lập `cwd`, secret redaction và logger idempotent; chuyển `RESOLVED`, chưa `CLOSED` trước review độc lập.

## TECH-005 State/task ghi DONE nhưng thiếu bằng chứng

- Loại/trạng thái/severity: rủi ro thiết kế / OPEN / UNASSESSED. Phase liên quan: 0–8.
- Owner/reviewer: chưa phân công; vai trò dự kiến Điều phối/QA. Hạn: trước gate liên quan, chưa có ngày cụ thể.
- Ảnh hưởng: Nhóm tiếp tục dựa trên trạng thái sai.
- Nguồn/bằng chứng: mục 8 Project Master v1.1; chưa có evidence triển khai hoặc đóng.
- Task review gần hạn: [TASK-015](tasks/TASK-015.md) cho G1 và [TASK-024](tasks/TASK-024.md) cho G2; các phase sau tiếp tục liên kết khi được phân rã.
- Điều kiện giải quyết: Đối chiếu tiêu chí và bằng chứng của task/gate; sửa trạng thái lệch, review khi bàn giao và tái lập cuối dự án.
- Lịch sử: 2026-09-09 kế thừa từ Master; cấu trúc/rules đã có không đủ để đóng rủi ro này.

## Ghi vấn đề mới

Dùng mã mới không trùng (nhóm GOV cho vận hành, DATA cho dữ liệu, hoặc TECH cho kỹ thuật). Ghi ngày, phát hiện cụ thể, file/run bị ảnh hưởng, kỳ vọng và thực tế, cách tái hiện nếu có, mức độ có căn cứ, owner, task xử lý và kiểm tra đóng. Không dán dữ liệu cá nhân hoặc secret vào issue.
