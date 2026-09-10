# Artifacts

Artifact là đầu ra có provenance của một lần chạy, đặt dưới `runs/<run_id>/`. Hiện chưa có run hoặc artifact thật. Nội dung sinh ra bị loại khỏi Git; `_archive/` không phải kho artifact đang dùng.

## Cấu trúc một run

Một run có thể chứa `manifest`, resolved config đã che secret, quality summary, model bundle, predictions, metrics, explanations, fairness tables, figures và log/evidence liên quan. Chỉ tạo thư mục con thực sự cần cho loại run; không tạo file rỗng để giả hoàn thiện.

Manifest tối thiểu ghi `run_id`, loại pipeline/RQ, trạng thái, thời gian, `snapshot_id`, code/config/protocol version, seed/split, input/output checksum và danh sách artifact. Model artifact thêm `model_version`, label order, feature contract, preprocessing state và thư viện cần nạp.

## Trạng thái và tính bất biến

- `RUNNING`: output chưa được reader khác sử dụng như kết quả.
- `FAILED`: giữ log/report để điều tra; không công bố model/result.
- `READY`: mọi file bắt buộc, checksum và kiểm tra liên quan đã đạt.

Artifact `READY` không được ghi đè. Chạy lại tạo `run_id` hoặc version mới và tham chiếu run cha khi cần. Việc đổi file trên filesystem nên dùng ghi tạm rồi publish nguyên tử; registry/DB chỉ trỏ tới artifact đã hoàn tất.

## Chia sẻ và bảo mật

Không lưu secret, connection URI, payload hồ sơ đầy đủ hoặc đường dẫn home cá nhân. Predictions chi tiết chỉ chia sẻ tại nơi nhóm phê duyệt; báo cáo/PR dùng bảng tổng hợp và ID/version có thể truy cập. Nơi lưu trữ artifact chung và retention policy hiện chưa được quyết định.
