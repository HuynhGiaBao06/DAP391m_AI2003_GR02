# Protocol nghiên cứu HMDA New York 2024

**Phiên bản:** 0.1

**Trạng thái:** DRAFT — khóa phần đã được Project Planning v1.1 xác định; preprocessing và các ngưỡng phụ thuộc dữ liệu vẫn `PENDING`.

Protocol này là nguồn vận hành cho thực nghiệm. [Project Master](HMDA_Project_Master_Main.docx) giữ kiến trúc/gate; [Project Planning](HMDA_New_York_Project_Planning.docx) giữ căn cứ đầy đủ của ba RQ.

## 1. Phạm vi đã khóa

- Dữ liệu chính: HMDA 2024 One Year Public Loan/Application Records, bang New York.
- Cohort: `activity_year = 2024`, `state_code = NY`, `action_taken ∈ {1,2,3}`, `applicant_sex ∈ {1,2}`.
- Target danh nghĩa ba lớp: `1 = Loan originated`, `2 = Approved but not accepted`, `3 = Application denied`.
- Không xem ba mã target là thang số; không gộp lớp 2 vào lớp 3.
- Đầu ra phản ánh trạng thái xử lý hồ sơ lịch sử, không phải xác suất vỡ nợ, credit score hoặc quyết định cấp tín dụng thực tế.
- Phần bắt buộc là NY. Chạy một bang khác là mở rộng có điều kiện và không thay thế RQ3 tại New York.

Chưa lọc thêm theo `loan_type`, `loan_purpose`, `occupancy_type` hoặc `total_units`. Nếu dữ liệu buộc phải thu hẹp cohort, thay đổi phải được duyệt và tạo phiên bản protocol trước khi train chính thức.

## 2. Câu hỏi nghiên cứu

**RQ1.** So sánh Logistic Regression, Decision Tree, Random Forest, XGBoost và MLP cho ba trạng thái; macro-F1 là metric chọn model chính.

**RQ2.** So sánh GSV và Shapley–Lorenz theo từng lớp trên Logistic Regression và model phi tuyến được chọn từ RQ1; đánh giá mức nhất quán thứ hạng, độ ổn định và chi phí tính.

**RQ3.** Đánh giá chênh lệch Male/Female toàn New York và trong từng county đủ điều kiện theo từng lớp one-vs-rest; county là vị trí tài sản bảo đảm, không mặc định là nơi cư trú.

## 3. Vai trò biến và ranh giới leakage

Mười hai feature dự kiến đưa vào quá trình xác minh trước train:

- Số: `income`, `loan_amount`, `combined_loan_to_value_ratio`, `property_value`, `loan_term`.
- Phân loại/khoảng: `debt_to_income_ratio`, `loan_type`, `loan_purpose`, `lien_status`, `occupancy_type`, `construction_method`, `total_units`.

Các biến sau không nằm trong `X`: `action_taken` là target; `applicant_sex` là thuộc tính audit; `state_code`, `county_code`, `lei`, `activity_year` là metadata/phạm vi. `record_id`, `snapshot_id`, `split` và `run_id` là khóa kỹ thuật.

Mốc dự đoán dự kiến là trước khi kết quả xử lý hồ sơ được xác lập. Danh sách 12 feature chưa được chứng nhận sạch leakage cho tới khi có bằng chứng về thời điểm sẵn có của từng trường và missingness. Feature không qua kiểm tra phải bị loại hoặc đưa về `PENDING`; không giữ chỉ để đủ số lượng.

## 4. Ba pipeline dữ liệu

1. **EDADataPipeline:** snapshot raw đã công bố → validation/lọc cohort → biểu diễn gần raw. Không split, imputation, scaling hoặc OHE cho model.
2. **TrainingDataPipeline:** raw snapshot → chuẩn hóa cố định → cohort → `X/y/metadata` → `split_manifest`. Các biến đổi học dữ liệu được fit trong luồng train.
3. **RegionDataPipeline:** snapshot miền mới + schema/protocol + model NY đã khóa → transform/predict. Không refit trên miền mới.

Join bằng `record_id` trong đúng `snapshot_id/run_id`, kiểm một-một và đối soát số dòng. Không nối bằng vị trí sau sort hoặc reset index.

## 5. Thiết kế RQ1

- Split đề xuất: 70% train, 15% validation, 15% test; stratified theo `action_taken`; seed 42.
- Chỉ điều chỉnh tỷ lệ trước train nếu kiểm tra dữ liệu cho thấy lớp/nhóm không đủ; phải tạo phiên bản protocol mới.
- Dùng cùng `record_id` split cho năm model và baseline dự đoán lớp phổ biến nhất từ train.
- Chọn model theo macro-F1 validation. Multiclass log loss là tiêu chí phụ khi kết quả chính bằng nhau theo quy tắc đã ghi trước.
- Báo precision, recall và F1 từng lớp, confusion matrix 3×3, log loss, thời gian fit preprocessing, fit model và predict.
- Tuning chỉ dùng train/validation hoặc CV nội bộ trên tập phát triển. Khóa model/cấu hình trước khi mở test; không dùng test để đổi model.
- Nếu ước lượng chênh lệch model bằng paired bootstrap, dùng cùng dòng test trong mỗi replicate và ghi rõ không bao phủ biến thiên do train lại.

## 6. Thiết kế RQ2

- Phân tích Logistic Regression và model phi tuyến tốt nhất theo macro-F1 validation. Nếu Logistic Regression đứng đầu, model phi tuyến vẫn chỉ được gọi là model phi tuyến được chọn.
- Đầu ra theo riêng `p1`, `p2`, `p3` trên thang xác suất.
- GSV của dự án là mean absolute Shapley values theo feature gốc và lớp; GSV đo độ lớn đóng góp, không cho biết chiều tác động.
- Hai phương pháp dùng cùng hồ sơ giải thích, background từ train, seed và đơn vị feature gốc. Các dummy của cùng một feature được quản lý như một coalition theo quy tắc được kiểm chứng.
- So thứ hạng bằng Spearman và mô tả feature bất đồng; không so trị số thô khi hai thang đo khác nhau.
- Trước chạy rộng, kiểm SL trên bài toán 3–4 feature có thể liệt kê tập con. Phải xác minh hàm giá trị, baseline, chuẩn hóa, xử lý feature vắng mặt, nhãn quan sát và dự đoán đi vào phép đo như thế nào.
- GSV/SL là giải thích toàn cục theo model/tập dữ liệu, không phải tác động nhân quả hoặc lý do cho một hồ sơ cá nhân.

## 7. Thiết kế RQ3

- Audit toàn bang cho năm model; phân tích county chính dùng model được chọn từ RQ1.
- Giữ model ba lớp và dự đoán `argmax`. Với mỗi lớp `k`, tạo bài toán đánh giá one-vs-rest từ `y = k` và `ŷ = k`; không train lại ba model nhị phân.
- Trong từng lớp/county, báo tỷ lệ nhãn thật, selection rate, TPR, FPR cho Male và Female; chênh lệch có dấu dùng `Female − Male`.
- Báo demographic parity difference và equalized odds difference; `worst-case EOD` là giá trị lớn hơn giữa khoảng chênh TPR và FPR.
- Ghi tổng `n`, số `y = k` và số `y ≠ k` theo sex × county × lớp. Mẫu số 0 là `undefined`, không đổi thành 0.
- `n ≥ 150` toàn county chỉ là bộ lọc sơ bộ. Ngưỡng cuối theo mẫu số, phương pháp khoảng tin cậy và multiple-testing policy phải được khóa trước khi xem gap.
- Không diễn giải dự đoán lớp 3 là một trường hợp “từ chối oan”; metric mô tả chênh lệch, không chứng minh phân biệt đối xử hay quan hệ nhân quả.

## 8. Preprocessing và quyết định đang chờ

Không có phương pháp preprocessing mặc định. Imputation, encoding, scaling, xử lý giá trị bất thường, missing indicator và feature engineering chỉ được chọn sau data quality, EDA gần raw và thí nghiệm trên train/validation. Mọi transformer có trạng thái chỉ fit trên train và được đóng gói cùng model để API/region tái sử dụng.

Các mục `PENDING` khác: bằng chứng thời điểm feature; runtime/dependency lock; nguồn và quyền PostgreSQL; công thức SL đầy đủ; ngưỡng fairness; bang đối chiếu; frontend/hosting và mục tiêu latency.

## 9. Version và điều kiện khóa protocol

Một thay đổi ảnh hưởng cohort, target, feature, split, model selection, RQ2/RQ3 metric hoặc quy tắc loại nhóm phải tăng phiên bản và ghi lý do trước thực nghiệm liên quan. Không sửa protocol sau khi thấy test hoặc fairness gap để cải thiện kết quả mà không công bố thay đổi và ảnh hưởng.

Protocol nền đủ để review khi: phần đã khóa khớp Planning; mọi mục chưa biết được đánh dấu; không có preprocessing ngầm; đầu ra và metric có chiều/mẫu số rõ; mỗi thay đổi có người duyệt và phiên bản. Trạng thái này không đồng nghĩa G0 hoặc pipeline đã nghiệm thu.
