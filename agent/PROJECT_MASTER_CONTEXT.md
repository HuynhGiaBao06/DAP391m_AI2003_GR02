# Project Master context dành cho agent

**Loại tài liệu:** bản tóm tắt dẫn xuất để đọc nhanh; không phải nguồn kiến trúc độc lập.

**Nguồn chuẩn:** [HMDA Project Master Main](../docs/HMDA_Project_Master_Main.docx), phiên bản 1.2 ngày 11/09/2026.

**Checksum nguồn:** được quản lý trong evidence nội bộ của lần đồng bộ, không ghi giá trị định danh trực tiếp trong tài liệu dùng chung.

**Đồng bộ:** 12/09/2026.

**Chia sẻ:** được phép theo dõi trong Git để thành viên và agent dùng cùng bản context; phải rà soát lại khi phiên bản hoặc nội dung nguồn thay đổi.

Nếu hash DOCX khác giá trị trên, coi file này đã cũ. Agent phải đọc lại DOCX, xác định phần thay đổi và cập nhật context trước khi dùng nó để quyết định kiến trúc hoặc nghiệm thu. Không tự sửa DOCX để khớp bản tóm tắt.

## 1. Thứ tự áp dụng

1. Yêu cầu rõ ràng mới nhất của người dùng quyết định phạm vi và quyền thao tác.
2. DOCX Project Master là nguồn chuẩn cho kiến trúc, phase, đầu ra và gate.
3. [Project Planning](../docs/HMDA_New_York_Project_Planning.docx) giữ căn cứ RQ và thiết kế nghiên cứu.
4. [Protocol](../docs/protocol.md) vận hành các quyết định thực nghiệm đã khóa và đánh dấu phần `PENDING`.
5. `PROJECT_STATE`, task, issue, decision và research log giữ trạng thái thực tế; chúng không tự thay đổi kiến trúc.

Khi context này mâu thuẫn với DOCX cùng hash, dùng DOCX và báo lỗi tóm tắt. Khi hai nguồn chuẩn hoặc quyết định người dùng chưa rõ, không tự chọn phương án; xử lý phần độc lập và báo điểm cần chốt.

## 2. Mục tiêu và phạm vi

Dự án xây dựng một quy trình Data Science tái lập trên HMDA New York 2024: chuẩn bị dữ liệu, so sánh năm model phân loại ba lớp, nghiên cứu GSV/Shapley–Lorenz, đánh giá fairness theo giới tính/county và triển khai kết quả qua Web API.

Bài toán nghiên cứu tách hai điểm khác nhau trong mortgage application funnel: quyết định tín dụng giữa phê duyệt và từ chối, rồi conversion sau phê duyệt giữa khoản vay được phát sinh và `Approved but not accepted`. Trạng thái thứ hai giúp quan sát post-approval fallout có liên quan đến quản trị pipeline, nhưng HMDA không ghi nguyên nhân cụ thể của từng hồ sơ và không cho phép định lượng trực tiếp chi phí, doanh thu hay tổn thất hedging. New York và năm 2024 là phạm vi thực nghiệm; county chỉ là chiều địa lý của RQ3, không phải lý do kinh doanh của nghiên cứu.

Ba RQ:

- **RQ1:** so sánh Logistic Regression, Decision Tree, Random Forest, XGBoost và MLP; macro-F1 validation là metric chọn model chính.
- **RQ2:** so GSV và Shapley–Lorenz theo từng lớp trên Logistic Regression và model phi tuyến được chọn từ RQ1.
- **RQ3:** đánh giá chênh lệch Male/Female toàn New York và trong từng county đủ điều kiện, rồi so mức gap giữa county.

Phần bắt buộc: New York 2024, năm model và baseline, ba RQ, Web API/giao diện, mã nguồn, báo cáo, slide, AI Audit Log và hướng dẫn tái lập. Bang đối chiếu, tuning/CV sâu, SL theo nhóm và mitigation là mở rộng có điều kiện.

Web API/giao diện là đầu ra triển khai của toàn dự án trong Master, không thuộc nội dung nghiên cứu RQ1–RQ3 của Research Plan.

Output phản ánh trạng thái xử lý hồ sơ lịch sử. Không gọi nó là xác suất vỡ nợ, credit score hoặc quyết định cấp tín dụng thực tế.

## 3. Hợp đồng dữ liệu và nhãn

Cohort nền: `activity_year = 2024`, `state_code = NY`, `action_taken ∈ {1,2,3}`, `applicant_sex ∈ {1,2}`. Chưa lọc thêm theo sản phẩm/tài sản; mọi thu hẹp phải được quyết định trước train.

Target danh nghĩa:

- `1`: Loan originated.
- `2`: Approved but not accepted.
- `3`: Application denied.

Không coi các mã là thứ tự liên tục và không gộp lớp 2 vào lớp 3.

Mười hai feature dự kiến: `income`, `loan_amount`, `combined_loan_to_value_ratio`, `property_value`, `loan_term`, `debt_to_income_ratio`, `loan_type`, `loan_purpose`, `lien_status`, `occupancy_type`, `construction_method`, `total_units`.

Không nằm trong `X`: `action_taken`, `applicant_sex`, `state_code`, `county_code`, `lei`, `activity_year` và các ID kỹ thuật. Danh sách feature vẫn phải qua kiểm tra thời điểm có thông tin/leakage; không giữ feature hoặc missing indicator hậu quyết định chỉ để đủ số lượng.

Giữ token gốc, phân biệt NA/Exempt/blank trước parse. Không tự xóa IQR outlier, hồ sơ giống nhau hoặc sửa dữ liệu để vượt quality gate. `record_id` bắt nguồn từ source version và dòng gốc, giữ ổn định; join theo khóa trong cùng snapshot/run, không theo vị trí DataFrame.

## 4. Kiến trúc và ba pipeline

Logic tái sử dụng nằm trong `src/hmda/`. Notebook điều khiển phân tích/train/nghiên cứu và trực quan; API import package/service và nạp artifact đã fit. Không import notebook từ API. Dùng class cho thành phần có trạng thái/cấu hình, function cho phép tính thuần.

- **EDADataPipeline:** raw snapshot `READY` → validate/lọc → dữ liệu gần raw. Không split, imputation, scaling hoặc OHE cho model.
- **TrainingDataPipeline:** raw snapshot → chuẩn hóa cố định → cohort → `X/y/metadata` → `split_manifest`; preprocessing và estimator fit trên train.
- **RegionDataPipeline:** snapshot miền mới + schema/protocol + model NY đã khóa → transform/predict; không refit.

EDA toàn bộ dữ liệu chỉ phục vụ nguồn, quality và mô tả. Quyết định dựa vào quan hệ với target được phát triển trên train. Test không dùng để chọn feature, preprocessing, model hoặc threshold.

## 5. Preprocessing, cấu hình, path và logging

**Preprocessing chưa được quyết định.** Không đặt phương pháp mặc định. Chỉ chọn sau data quality, EDA gần raw và thử nghiệm train/validation; mọi transformer học dữ liệu chỉ fit trên train. API và region dùng lại trạng thái đã lưu.

`configs/` là nơi duy nhất chỉnh tham số. `preprocessing.yaml` để trống phương án cho tới khi có bằng chứng/quyết định. Secret lấy từ môi trường; config lưu trong artifact phải được che secret và chỉ là bằng chứng run.

`src/hmda/core/path.py` tìm project root từ `__file__`, duyệt đến marker `pyproject.toml` và `src/hmda`; không dùng hoặc fallback về `cwd`. Notebook/API import package đã cài, không sửa `sys.path`.

Logging tập trung theo module/run. Ghi `run_id`, `snapshot_id`, pipeline, bước, thời gian, số dòng, warning/error; API có `request_id` và `model_version`. Không tạo handler lặp hoặc log secret/toàn bộ hồ sơ.

## 6. PostgreSQL, CSV, snapshot và quality

PostgreSQL là nguồn chung; CSV trong `data/` giữ raw và bản xuất snapshot. Không đồng bộ hai chiều tự động và không sửa CSV bằng tay như nguồn hiện hành.

Vòng đời: nhận raw/hash → staging → schema/quality/reconciliation → snapshot/export → công bố `READY`. Run lỗi là `FAILED`; reader chỉ chọn snapshot ID cụ thể ở trạng thái `READY`. Snapshot đã công bố là bất biến.

Manifest giữ source/hash, parent snapshot, schema/config/code/protocol version, số dòng/cột, thời gian và trạng thái. Training snapshot thêm `split_manifest`. Export dùng file tạm, checksum, serialization ổn định và đối soát DB theo khóa.

`ERROR` chặn publish/bước phụ thuộc; `WARNING` được ghi và xử lý theo protocol. `is_valid` chỉ nghĩa không còn lỗi chặn. Validation/exception bảo vệ production; assert chỉ hỗ trợ invariant trong notebook/test. Phải kiểm idempotency, transaction, rollback/retry và chạy đồng thời trước nghiệm thu dữ liệu.

Ngoại lệ vận hành hiện hành cho G2 tối giản được người dùng chốt ngày 2026-09-13 tại [DEC-011](DECISIONS.md): vẫn bắt buộc transaction/rollback khi lỗi, duplicate/idempotency cơ bản, round-trip thật, quality, reconciliation và snapshot `READY`; concurrency stress, restore drill và reviewer độc lập được hoãn khỏi G2 hiện tại. Đây là ghi chú phạm vi thực thi, không sửa DOCX nguồn và không phải bằng chứng rằng các bước đã chạy.

## 7. Thiết kế thực nghiệm cốt lõi

RQ1 dùng split đề xuất 70/15/15, stratified theo `action_taken`, seed 42 nếu dữ liệu cho phép. Dùng cùng split cho năm model và baseline lớp phổ biến nhất. Chọn theo macro-F1 validation; báo per-class precision/recall/F1, confusion matrix 3×3, log loss và runtime. Khóa model trước test.

RQ2 dùng riêng `p1/p2/p3`. GSV của dự án là mean absolute Shapley theo feature gốc và lớp. Hai phương pháp dùng cùng sample/background/seed; one-hot của cùng feature được nhóm theo quy tắc đã xác minh. SL phải được kiểm công thức, baseline, normalization, coalition và value function trên bài toán 3–4 feature trước chạy rộng. Không gọi ranking là quan hệ nhân quả.

RQ3 giữ model ba lớp và đánh giá từng lớp one-vs-rest sau `argmax`. Báo label/prediction rate, selection rate, TPR, FPR, DPD, EOD và gap có dấu `Female − Male`; EOD worst-case là chênh lệch lớn hơn giữa TPR/FPR. Báo mẫu số sex × county × class; denominator 0 là undefined. `n ≥ 150` toàn county chỉ là lọc sơ bộ, không phải ngưỡng cuối.

API dự kiến có `POST /predict`; `GET /health`, `/model-info`, `/metrics`, `/explanations/global`, `/fairness`. `/predict` không yêu cầu target/sex; GSV/SL/fairness được tính offline và đọc theo model/run version, không tính lại theo request hoặc trình bày như lý do cá nhân.

## 8. Phase và gate

| Phase | Đầu ra chính | Gate |
| --- | --- | --- |
| 0 — Phạm vi và tổ chức | Protocol nền, paper table, API sơ bộ, phân công và vấn đề | G0: phạm vi/owner/dependency đủ rõ |
| 1 — Hạ tầng | Runtime lock, path/config/logging, package, contract/test nền | G1: môi trường và core chạy có bằng chứng |
| 2 — Data/quality | PostgreSQL, raw lineage, schema, validator, snapshot | G2: snapshot `READY`, reconciliation/quality đạt |
| 3 — EDA | EDA gần raw, quality findings, thiết kế train/fairness khóa | G3: không leakage do EDA, quyết định có bằng chứng |
| 4 — Training/RQ1 | Năm model + baseline, selection, test, artifact | G4: model/predictions/metrics có provenance |
| 5 — GSV/SL | Kiểm chứng nhỏ, GSV/SL, ranking/resource report | G5: công thức và output đúng phạm vi |
| 6 — Fairness/region | Audit NY/county, region contract và mở rộng nếu đủ điều kiện | G6: metric/mẫu số/undefined đúng; model không refit |
| 7 — Web API | API/Web, model loading, dashboard, parity và vận hành | G7: demo chạy, version/parity/security đạt |
| 8 — Tái lập/bàn giao | Clean reproduction, report, slide, audit log, release docs | G8: bằng chứng cuối được review |

Đường phụ thuộc chính: `G0 → G1 → G2 → G3 → G4 → G5/G6 → G7 → G8`. Tổng thời lượng dự kiến 10 tuần. Nếu trễ, giảm tuning/quy mô SL hoặc hoãn bang đối chiếu; không bỏ năm model, baseline, kiểm chứng SL, fairness NY hoặc tái lập.

## 9. Nguồn thông tin theo trách nhiệm

- Kiến trúc/gate đầy đủ: DOCX nguồn ghi ở đầu file.
- RQ và căn cứ nghiên cứu: Project Planning.
- Quyết định thực nghiệm: `docs/protocol.md`.
- Tham số: `configs/`.
- Điểm dừng: `agent/PROJECT_STATE.md`.
- Công việc: `agent/tasks/`; vấn đề: `agent/ISSUES.md`; quyết định: `agent/DECISIONS.md`; phát hiện: `agent/RESEARCH_LOG.md`.
- Dữ liệu: `data/README.md`; artifact: `artifacts/README.md`; tái lập: `docs/reproducibility.md`; API: `docs/api_contract.md`.

Không chép số liệu, task hoặc trạng thái run vào context này. Các file đó thay đổi thường xuyên và phải được đọc từ nguồn riêng.

## 10. Mục đang chờ

Owner/reviewer và mốc học phần; phạm vi AI services; runtime/dependency lock; PostgreSQL/quyền và nơi phân phối snapshot/artifact; preprocessing/feature eligibility; công thức SL đầy đủ; ngưỡng fairness và multiple testing; bang đối chiếu; frontend/hosting/authentication và mục tiêu latency.

Không tự điền các mục trên. Tài liệu/scaffold hoàn chỉnh không tự đóng gate.

## 11. Khi phải mở lại DOCX

Agent phải đọc Project Master DOCX khi:

- sửa kiến trúc, phạm vi bắt buộc, phase, đầu ra hoặc gate;
- nghiệm thu/đóng một phase;
- chỉnh chính Project Master hoặc tạo báo cáo tổng thể dựa trên nó;
- context/hash không khớp, nội dung mơ hồ hoặc có conflict giữa nguồn;
- cần trích dẫn, bảng file/trách nhiệm hoặc câu chữ chính xác không có trong context.

Các công việc cục bộ đã có hợp đồng rõ có thể dùng context này, protocol và tài liệu chuyên trách mà không nạp toàn bộ DOCX.
