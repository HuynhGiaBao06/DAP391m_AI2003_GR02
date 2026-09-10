# Hợp đồng Web API HMDA

**Phiên bản hợp đồng:** 0.1-draft

**Trạng thái:** DRAFT — đủ để thiết kế schema/routes; kiểu, miền giá trị chi tiết, authentication, hosting và latency còn chờ.

API nạp một model bundle đã công bố và dùng cùng normalizer/preprocessing/model với luồng offline. API không train, fit lại, chạy full GSV/SL hoặc tính lại fairness theo request.

## Nguyên tắc chung

- Base path và versioning transport chưa chốt; endpoint logic trong tài liệu này là hợp đồng sơ bộ.
- Phản hồi JSON dùng tên trường ổn định; thay đổi phá vỡ tương thích phải tăng API version.
- Mọi phản hồi dự đoán có `request_id` và `model_version`; kết quả nghiên cứu có thêm `run_id`/`snapshot_id` khi đã công bố.
- Không trả đường dẫn nội bộ, secret, stack trace hoặc toàn bộ cấu hình model.
- API trả kết quả lịch sử ba lớp; không mô tả output là credit score, xác suất vỡ nợ hoặc quyết định cấp tín dụng.

## Endpoint dự kiến

| Method và path | Mục đích | Điều kiện dữ liệu |
| --- | --- | --- |
| `GET /health` | Trạng thái tiến trình và khả năng phục vụ | Không tiết lộ cấu hình nội bộ |
| `GET /model-info` | Model version, label mapping, phạm vi và thời điểm công bố | Chỉ model `READY` |
| `POST /predict` | Kiểm input và trả ba xác suất cùng lớp argmax | Model bundle `READY` |
| `GET /metrics` | Đọc metric RQ1 đã công bố | Lọc theo model/run/split được cho phép |
| `GET /explanations/global` | Đọc GSV/SL toàn cục đã tính offline | Lọc model/run/class; ghi rõ global |
| `GET /fairness` | Đọc bảng audit đã công bố | Lọc model/run/class/county; có mẫu số |

## `POST /predict`

### Request

`features` chứa đúng 12 feature nghiệp vụ dự kiến: `income`, `loan_amount`, `combined_loan_to_value_ratio`, `property_value`, `loan_term`, `debt_to_income_ratio`, `loan_type`, `loan_purpose`, `lien_status`, `occupancy_type`, `construction_method`, `total_units`.

`context` có thể chứa `state_code` và `county_code` để kiểm phạm vi/hiển thị cảnh báo sau khi schema được duyệt. Context không được truyền vào estimator. `applicant_sex`, `action_taken`, `lei`, `activity_year`, `record_id`, `snapshot_id`, `split` và `run_id` không phải feature đầu vào dự đoán.

Kiểu dữ liệu, nullable, đơn vị, category hợp lệ và quy tắc NA/Exempt sẽ tham chiếu `configs/schema.yaml` sau khi đối chiếu dữ liệu thực. API không tự đổi missing thành 0 hoặc áp preprocessing chưa được duyệt.

### Response thành công

| Trường | Nội dung |
| --- | --- |
| `request_id` | ID truy vết request, không chứa dữ liệu hồ sơ |
| `model_version` | Phiên bản model bundle đang phục vụ |
| `prediction.code` | Một trong `1`, `2`, `3` |
| `prediction.label` | Tên lớp theo mapping protocol |
| `probabilities.p1/p2/p3` | Xác suất theo đúng thứ tự lớp; tổng nằm trong tolerance đã kiểm |
| `scope.status` | `in_scope`, `out_of_scope` hoặc `unknown` theo context có sẵn |
| `warnings` | Cảnh báo domain/category/missingness không chặn request |

Không trả GSV/SL toàn cục như lý do cá nhân. Nếu sau này bổ sung local explanation, phải có hợp đồng, phép kiểm và giới hạn riêng.

## Endpoint kết quả nghiên cứu

`/metrics`, `/explanations/global` và `/fairness` chỉ đọc artifact/results đã công bố; không kích hoạt notebook hoặc job tính toán. Filter không hợp lệ bị từ chối thay vì âm thầm trả tập khác.

Fairness response phải mang class OvR, group labels, chiều gap, selection rate/TPR/FPR, DPD/EOD, `n`, mẫu số dương/âm và trạng thái `undefined` khi không đủ mẫu. Không gọi một county là công bằng chỉ từ một metric.

## Lỗi và trạng thái dịch vụ

| Trường hợp | Hành vi dự kiến |
| --- | --- |
| JSON hoặc schema sai | `422`, chỉ rõ trường và loại lỗi an toàn |
| Request đúng schema nhưng ngoài phạm vi | Chính sách reject hay warning còn `PENDING`; phải chốt trước implementation |
| Model/artifact chưa sẵn sàng | `503`, không fallback sang model khác không công bố |
| Kết quả/filter không tồn tại | `404` |
| Lỗi nội bộ | `500` với `request_id`; chi tiết nằm trong log bảo vệ |

Mã lỗi ứng dụng và cấu trúc error body sẽ được khóa cùng implementation schema. Không dùng thông báo lỗi để lộ category nội bộ, filesystem hoặc connection details.

## Logging và bảo mật

Log API gồm timestamp, `request_id`, route, status, latency, `model_version` và lỗi đã làm sạch. Không log toàn bộ payload, secret hoặc hồ sơ người dùng. DB của API dùng quyền đọc trên model/results đã công bố; quyền migration/nạp dữ liệu không thuộc service runtime.

## Điều kiện nghiệm thu hợp đồng

- Schema khớp model bundle và label mapping; `action_taken`/sex/metadata không lọt vào `X`.
- Cùng hồ sơ cho xác suất offline và API trong tolerance đã khóa.
- Model version và artifact được nạp nguyên tử; lỗi nạp không làm service trả model không rõ phiên bản.
- Validation, unknown category, missingness, model unavailable và filter sai có test.
- Response nghiên cứu đối chiếu được với artifact; fairness có mẫu số và explanation ghi đúng phạm vi global.
- Latency chỉ được đặt thành tiêu chí sau benchmark; hiện chưa có SLA.

## Mục đang chờ quyết định

Kiểu/constraint trường; chính sách request ngoài NY; authentication; pagination; cache; giới hạn request; API version path; frontend/hosting; mục tiêu latency và cơ chế triển khai/rollback. Các mục này không được tự điền bằng giả định của implementation.
