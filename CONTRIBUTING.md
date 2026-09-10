# Đóng góp cho dự án HMDA

Mỗi thay đổi cần có phạm vi rõ, nguồn dữ liệu hoặc căn cứ phù hợp và bằng chứng kiểm tra tương ứng. Bắt đầu từ [README](README.md), [chỉ mục tài liệu](docs/README.md), [protocol](docs/protocol.md) và [Git workflow](docs/git/WORKFLOW.md).

## Trước khi sửa

1. Xác định đầu ra cần thay đổi và nguồn sự thật liên quan.
2. Kiểm trạng thái Git và giữ nguyên phần việc đang dở của thành viên khác.
3. Xác định đầu vào, file sẽ sửa và phép kiểm cần chạy.
4. Không tự chốt preprocessing, ngưỡng fairness, hạ tầng triển khai hoặc thông tin kết nối PostgreSQL khi chưa có quyết định.

Một nhánh chỉ nên chứa một đầu ra có thể review. Quy tắc đặt tên nhánh, commit và pull request nằm trong [Git workflow](docs/git/WORKFLOW.md).

## Quy tắc theo loại file

- Logic tái sử dụng đặt trong `src/hmda/`; API import package, không import notebook.
- Notebook dùng cho EDA, train, nghiên cứu và trực quan; tuân theo [Notebook guidelines](docs/notebook_guidelines.md).
- Tham số dự án đặt trong `configs/`. Không hard-code đường dẫn máy cá nhân, secret hoặc tham số thí nghiệm trong nhiều file.
- Migration và kiểm tra phía PostgreSQL đặt trong `sql/`; không thay schema dùng chung trực tiếp từ notebook.
- CSV, snapshot, artifact, log và secret không đưa lên Git. Đọc [Security](SECURITY.md) trước khi chia sẻ notebook, DOCX hoặc output.
- Preprocessing chỉ được triển khai sau khi có phân tích, bằng chứng và quyết định tương ứng. Mọi biến đổi học từ dữ liệu phải fit trên train.

## Kiểm tra trước pull request

| Loại thay đổi | Kiểm tra tối thiểu |
| --- | --- |
| Markdown | Link nội bộ, trạng thái, thuật ngữ và xung đột với nguồn chính |
| DOCX/PPTX | Nội dung, link/citation và kiểm trực quan bản kết xuất |
| Config | Parse, trường bắt buộc, kiểu, tham chiếu chéo và không có secret |
| Python | Test liên quan, lỗi biên, logging và hợp đồng input/output |
| Data/SQL | Schema, số dòng, khóa, idempotency, transaction và quality report |
| Notebook | Cell chạy theo thứ tự, provenance, output/metadata và clean-kernel khi được yêu cầu |
| API/Web | Schema validation, model version, parity với offline và log đã che dữ liệu |

Chỉ ghi một kiểm tra là đạt khi đã thực sự chạy. Kiểm tra tĩnh hoặc output cũ phải được mô tả đúng loại bằng chứng.

## Nội dung pull request

Mô tả vấn đề, hành vi sau thay đổi, file chính, cách kiểm, ảnh hưởng và phần còn chưa xác minh. Dùng `snapshot_id`, `run_id`, `model_version` hoặc số liệu chỉ khi chúng tồn tại thật và reviewer truy cập được. Ít nhất một thành viên khác review trước khi merge vào `main`.

Không đưa vào PR dữ liệu cá nhân, credential, file local của agent hoặc đường dẫn chỉ tồn tại trên một máy làm bằng chứng duy nhất.
