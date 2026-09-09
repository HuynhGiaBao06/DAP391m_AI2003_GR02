# Sổ quyết định

Phân biệt quyết định người dùng đã chốt với đề xuất/PENDING. Mỗi mục cần nguồn, ngày, trạng thái, phạm vi ảnh hưởng và liên kết evidence; không tự ghi người dùng đã duyệt.

## DEC-001 Kiến trúc được chấp nhận

Ngày 2026-09-09: người dùng chấp nhận [Project Master v1.1](../docs/HMDA_Project_Master_Main.docx). Dùng tài liệu này làm nguồn kiến trúc; không sao chép toàn bộ đặc tả vào đây. Preprocessing giữ trạng thái chưa quyết định.

## DEC-002 Dựng cấu trúc và cô lập lịch sử

Ngày 2026-09-09: người dùng yêu cầu tạo cấu trúc theo Master và xóa hoặc cô lập file agent cũ. Đã chọn chuyển .tmp/ vào _archive/agent_generated/2026-09-09/legacy_tmp/ để giữ khả năng khôi phục. Chưa triển khai logic nghiệp vụ trong bước này.

## DEC-003 Hồ sơ agent và dữ liệu riêng tư chỉ lưu local

Ngày 2026-09-09: theo yêu cầu người dùng, .gitignore chặn CSV ở mọi thư mục, hồ sơ agent và file bí mật/cá nhân theo tên/vùng lưu trữ. Toàn bộ _archive/ và docs/ai_audit/ được loại khỏi Git. README là điểm vào dùng chung, không phụ thuộc file agent khi clone. Quyết định này thay cách giữ manifest/README archive trên Git trước đó; các file vẫn còn nguyên local. Chi tiết kiểm tra tại TASK-002.

## DEC-004 Hoàn thiện hồ sơ vận hành agent

- Ngày: 2026-09-09. Trạng thái: IMPLEMENTED trong phạm vi tài liệu được yêu cầu.
- Căn cứ: yêu cầu người dùng “Tiếp tục hoàn thành các file liên quan tới agent”.
- Thực hiện: rules/guideline/luồng vào phiên, state, issue, research log và task được hoàn thiện; bốn task gần hạn Phase 0 được phân rã.
- Giới hạn: không tự coi rules là quyền triển khai/train/ghi DB, không sửa kiến trúc Master hoặc chọn preprocessing. Các quy tắc vẫn có thể được người dùng sửa ở phiên sau.
- Bằng chứng: [TASK-003](tasks/TASK-003.md). Thay thế mô tả “rules chỉ là khung” trong trạng thái hiện tại; giữ lịch sử task cũ đúng thời điểm.

## DEC-005 Phân loại chế độ thao tác và báo cáo file theo phiên

- Ngày: 2026-09-09. Trạng thái: IMPLEMENTED trong phạm vi hồ sơ agent local.
- Căn cứ: yêu cầu người dùng bổ sung giới hạn làm việc cho đọc logic, xuất code, implement và review; đồng thời yêu cầu báo cáo file đã truy cập và chỉnh sửa trong mỗi phiên.
- Thực hiện: [AGENT_RULES](AGENT_RULES.md) định nghĩa bốn chế độ thao tác, các mức quyền từ chỉ đọc đến công bố/push, và nội dung tối thiểu của báo cáo file khi bàn giao.
- Giới hạn: không mở thêm quyền chạy notebook/pipeline, ghi dữ liệu/DB hoặc push/publish nếu yêu cầu phiên không giao rõ; hồ sơ agent tiếp tục chỉ lưu local theo DEC-003.

## Các quyết định còn chờ

Đây là câu hỏi điều phối, không phải thông số hoặc phương án đã chọn. Tên owner và ngày cụ thể chưa phân công; TASK-005 thu thập xác nhận thật, không tự điền.

| Mã | Nội dung đang chờ | Trạng thái | Cần chốt khi nào | Task chuẩn bị |
| --- | --- | --- | --- | --- |
| PEND-01 | Tên owner/reviewer và hạn cho các đầu việc | PENDING | G0 | TASK-005 |
| PEND-02 | Lịch học phần, AI services và yêu cầu RQ mới | PENDING | Phạm vi sản phẩm trước G0; xác nhận với nhóm/giảng viên qua người dùng | TASK-005, TASK-007 |
| PEND-03 | Python, runtime/dependency lock và cách thiết lập môi trường | PENDING | Phase 1/G1 | TASK-005 điều phối; chưa tách task kỹ thuật |
| PEND-04 | Nguồn/PostgreSQL, quyền truy cập và nơi phân phối snapshot/artifact | PENDING | Trước nhập dữ liệu Phase 2/G2 | TASK-005 điều phối |
| PEND-05 | Phương án preprocessing và feature đủ điều kiện | PENDING | Sau phân tích/kiểm tra, trước train chính thức G4 | TASK-004 chỉ chuẩn bị câu hỏi |
| PEND-06 | Chi tiết công thức SL, mẫu, seed và ngưỡng fairness còn mở | PENDING | Trước thực nghiệm tương ứng | TASK-006 chuẩn bị đặc tả |
| PEND-07 | Frontend/hosting và mục tiêu hiệu năng đo được | PENDING | Trước tích hợp/nghiệm thu Phase 7 | TASK-007 chuẩn bị hợp đồng |
| PEND-08 | Có chạy bang đối chiếu thực và chọn vùng nào | PENDING | Sau điều kiện NY và trước chạy mở rộng | TASK-004 ghi ranh giới; chưa có quyết định chạy |

Các chi tiết đã chốt trong Planning không bị đưa về chưa chốt bởi bảng này; chỉ ghi phần còn mở. Tham số khi được chọn vẫn lưu duy nhất trong configs/.

## Ghi quyết định tiếp theo

Dùng DEC-xxx mới. Ghi câu hỏi, trạng thái PROPOSED/ACCEPTED/IMPLEMENTED/SUPERSEDED, căn cứ người chốt và ngày, lý do, phạm vi/file bị ảnh hưởng, evidence/issue và điều kiện xem xét lại. Một đề xuất của agent chưa có xác nhận phải giữ PROPOSED khi cần người dùng quyết định. Khi thay thế, dẫn tới quyết định mới và giữ lịch sử cũ.
