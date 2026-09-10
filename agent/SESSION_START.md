# Bắt đầu và tiếp tục phiên làm việc

## Đọc để xác định việc cần làm

1. Đọc yêu cầu mới nhất của người dùng và [AGENT_RULES](AGENT_RULES.md).
2. Đọc [PROJECT_MASTER_CONTEXT](PROJECT_MASTER_CONTEXT.md) thay cho việc nạp toàn bộ DOCX. Kiểm hash/mở DOCX nguồn khi context yêu cầu hoặc công việc liên quan kiến trúc, gate hay nghiệm thu.
3. Đọc [GUIDELINES](GUIDELINES.md), rồi [PROJECT_STATE](PROJECT_STATE.md) để biết điểm dừng và điều chưa xác minh.
4. Đọc [tasks/INDEX](tasks/INDEX.md) và file task được giao. Nếu chưa có task khớp, tạo task có phạm vi từ chính yêu cầu hiện tại; không tự mở rộng sang cả phase.
5. Mở đúng mục liên quan trong [ISSUES](ISSUES.md), [DECISIONS](DECISIONS.md), [RESEARCH_LOG](RESEARCH_LOG.md), [Project Planning](../docs/HMDA_New_York_Project_Planning.docx) và [protocol](../docs/protocol.md). Không đọc lại toàn bộ lịch sử khi không cần.
6. Kiểm tra file thực tế, thay đổi Git và đầu vào cần dùng. Khi state khác thực tế, ghi nhận sai lệch, xác minh rồi sửa state; không ghi đè file để ép khớp mô tả cũ.

## Chốt phạm vi trước khi hành động

Trong task, ghi mục tiêu, file sẽ sửa, đầu vào/đầu ra, kiểm tra cần chạy và căn cứ cho quyền thao tác. Tách quyền sửa code, thực thi notebook, đọc/ghi DB hoặc công bố ra bên ngoài khi chúng khác nhau.

Nếu yêu cầu đã rõ, thông báo ngắn rồi thực hiện. Chỉ hỏi khi thiếu thông tin ảnh hưởng quyết định hoặc hành động vượt phạm vi; tiếp tục phần độc lập có thể làm được. Không tự coi một mục BACKLOG/READY là yêu cầu bắt đầu.

Khi nhiều người đang làm, kiểm tra owner/file liên quan và giữ thay đổi của họ. Khóa logic trong Markdown không thay thế cơ chế đồng thời của DB hoặc filesystem.

## Khi phiên bị ngắt

Đọc lại state → task đang dở → bằng chứng đã lưu. Xác minh output đã tồn tại trước khi chạy lại để tránh nạp trùng, ghi đè hoặc tạo run mới vô tình. Không coi một lệnh bị ngắt là chắc chắn chưa có tác động.

Trước khi rời phiên, cập nhật task và PROJECT_STATE với phần đã xong, lỗi/chưa kiểm, file/output liên quan và đúng một bước tiếp tục. Cập nhật issue/decision/research chỉ khi có thông tin mới tương ứng.

## Điều hướng nhanh

- Học hoặc giải thích: dùng file hiện có làm ví dụ; không sửa/chạy chỉ để minh họa nếu người dùng chỉ hỏi giải thích.
- Review: nêu nguồn bằng chứng; phân biệt đọc code/output đã lưu với chạy lại thực tế.
- Triển khai: sửa trong phạm vi được giao, kiểm đúng phần bị ảnh hưởng, cập nhật bằng chứng.
- Thực nghiệm: chỉ bắt đầu khi task, dữ liệu và môi trường đủ điều kiện; không tạo kết luận từ output giả hoặc chưa chạy.

Các mô tả trên là cách xử lý yêu cầu, không phải chế độ cấp quyền tự động.
