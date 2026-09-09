# Cấu hình tập trung

Đây là nơi duy nhất chỉnh tham số dự án. Các YAML hiện chỉ có mô tả, chưa phải cấu hình chạy được.
Vai trò từng file nằm ở mục 5 của [Project Master](../docs/HMDA_Project_Master_Main.docx).

Preprocessing chưa có lựa chọn mặc định. Sau khi có bằng chứng phân tích và quyết định, mới điền preprocessing.yaml.
Không điền secret vào YAML. local.env.example là mẫu; local.env thật được loại khỏi Git.
ConfigLoader phải kiểm cấu hình thiếu/sai trước khi chạy; chưa triển khai kiểm tra này.
