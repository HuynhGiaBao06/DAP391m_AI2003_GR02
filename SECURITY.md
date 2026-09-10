# Bảo mật, dữ liệu và quyền riêng tư

Tài liệu này áp dụng cho mã nguồn, PostgreSQL, CSV, notebook, log, artifact, Web API và tài liệu chia sẻ của dự án HMDA.

## Secret và thông tin kết nối

Không commit mật khẩu, token, khóa, chuỗi kết nối hoặc file môi trường thật. Chỉ giữ tên biến và giá trị minh họa không bí mật trong `configs/local.env.example`; giá trị thật lấy từ biến môi trường hoặc kho secret của môi trường triển khai.

Không truyền secret qua tham số dòng lệnh, notebook output, ảnh chụp, log hoặc nội dung pull request. `.gitignore` chỉ lọc theo tên/đường dẫn và không phát hiện secret nằm trong nội dung file.

Nếu credential có thể đã bị lộ, dừng chia sẻ, thu hồi hoặc thay credential trước, xác định phạm vi ảnh hưởng rồi mới làm sạch file và lịch sử theo quyền của nhóm. Không đăng giá trị bị lộ vào issue để minh họa.

## Dữ liệu HMDA và dữ liệu người dùng API

HMDA là dữ liệu công khai nhưng vẫn phải giữ nguyên phạm vi nghiên cứu và tránh phát tán hồ sơ đầy đủ không cần thiết. CSV nguồn, snapshot và bản xuất nằm ngoài Git; chia sẻ qua nơi lưu trữ được nhóm phê duyệt và kèm manifest/checksum.

API chỉ nhận các feature cần cho dự đoán và ngữ cảnh kiểm phạm vi. Không yêu cầu `action_taken`; `applicant_sex`, `state_code`, `county_code`, `lei` và `activity_year` không được tự đưa vào feature model. Không lưu toàn bộ payload dự đoán trong log.

## Logging, notebook và artifact

Log được phép chứa `request_id`, `run_id`, `snapshot_id`, `model_version`, bước xử lý, số dòng tổng hợp, cảnh báo và traceback đã rà soát. Log không chứa secret, chuỗi kết nối, toàn bộ hồ sơ hoặc dữ liệu định danh trực tiếp.

Trước khi commit notebook hoặc tài liệu, kiểm cả output, metadata, đường dẫn local, tên người dùng và ảnh chụp. Artifact chia sẻ phải che secret trong config, dùng ID/version thật và chỉ chứa dữ liệu chi tiết khi quyền truy cập đã được xác định.

## PostgreSQL và triển khai

Tách quyền đọc, nạp dữ liệu, migration và đọc kết quả theo vai trò. Pipeline không dùng `replace`, `drop` hoặc `truncate` bảng chung như cách chạy mặc định. Snapshot chỉ được đọc khi trạng thái `READY`; công bố metadata và dữ liệu phải nhất quán.

Cấu hình production không nằm trong repository. Endpoint health/model-info không được trả secret, đường dẫn nội bộ hoặc stack trace. Lỗi gửi cho client dùng mã ổn định và thông điệp an toàn; chi tiết kỹ thuật chỉ nằm trong log bảo vệ.

## Báo cáo vấn đề

Kênh và người nhận báo cáo bảo mật chưa được nhóm phân công. Cho đến khi có quyết định, báo trực tiếp cho người quản lý dự án qua kênh nội bộ đã được nhóm sử dụng; không mở issue công khai chứa dữ liệu nhạy cảm. Ghi thời điểm, thành phần ảnh hưởng và hành động cô lập, nhưng không sao chép secret vào báo cáo.
