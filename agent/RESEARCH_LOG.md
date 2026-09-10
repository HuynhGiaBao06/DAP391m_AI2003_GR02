# Nhật ký nghiên cứu

**Hiện chưa có kết quả thực nghiệm hoặc paper được xác minh mới trong tác vụ hoàn thiện hồ sơ agent.** Không chuyển nội dung thiết kế trong Planning thành kết luận đã kiểm chứng.

## Cách ghi

Mỗi mục dùng mã RL-xxx, câu hỏi rõ và ngày. Phân loại bằng chứng: nguồn đã đọc, kiểm tra tĩnh, output đã lưu, lần chạy mới hoặc kiểm chứng độc lập. Kết quả và mức độ tin cậy phải đúng với loại bằng chứng.

Không đặt một phát hiện là VERIFIED nếu chỉ có tên file hoặc thiết kế. Trạng thái dùng: HYPOTHESIS (giả thuyết), OBSERVED (đã quan sát, còn giới hạn), VERIFIED (đạt phép kiểm nêu rõ), SUPERSEDED hoặc REJECTED (giữ lịch sử và lý do). VERIFIED chỉ có giá trị trong phạm vi đã kiểm, không đồng nghĩa nhân quả hay tổng quát ngoài dữ liệu.

Kết luận làm thay đổi cách triển khai phải được liên kết sang DECISIONS; lỗi hoặc điều chưa giải quyết chuyển ISSUES. Log không thay artifact chứa số liệu chi tiết.

## Mẫu mục nghiên cứu

```text
RL-xxx — Câu hỏi hoặc phát hiện
Ngày / người thực hiện / task / RQ:
Trạng thái / loại bằng chứng:
Nguồn paper (trang/mục/DOI/URL) hoặc nguồn dữ liệu và phiên bản:
Snapshot / run / model / code-config version (chỉ ghi khi có thật):
Mẫu, nhóm, lớp, đơn vị phân tích và điều kiện loại trừ:
Phương pháp và phép kiểm:
Kết quả (số liệu + link artifact/notebook):
Kết luận được bằng chứng hỗ trợ:
Giới hạn và điều chưa được chứng minh:
Reviewer hoặc cách xác minh độc lập, nếu có:
Issue / decision liên quan:
Bước tiếp theo:
```

## Điểm cần chú ý theo RQ

- RQ1: phân biệt chọn trên validation và test sau khóa; ghi split và model version, không chọn lại bằng test.
- RQ2: ghi output class, background/mẫu, đơn vị feature gốc và công thức đã kiểm; không thay SL bằng một phép tính khác mà giữ nguyên tên.
- RQ3: ghi nhóm/chiều gap, lớp OvR, county, n và mẫu số từng rate; metric không xác định phải hiển thị đúng. Cross-region chưa chạy ghi NOT RUN.
- Phân tích chất lượng: bất thường mô tả chưa là lý do tự xóa/sửa dữ liệu; preprocessing giữ chưa quyết định đến khi có đủ bằng chứng và quyết định liên quan.

## RL-001 — Đối chiếu nguồn paper nền tảng

- **Ngày / phạm vi:** 09/09/2026; source review phục vụ `docs/paper_review.md`; không chạy notebook hoặc code phương pháp.
- **Trạng thái / loại bằng chứng:** OBSERVED — metadata/abstract trên trang nhà xuất bản hoặc kho học thuật; chưa phải reproduction.
- **Nguồn:** INFORMS cho Hurlin, Pérignon & Saurin (`10.1287/mnsc.2022.03888`); Maynooth University Research Archive cho Agarwal, Muckley & Neelakantan (`10.1016/j.econlet.2023.111117`); ScienceDirect cho Chen et al. (`10.1016/j.eswa.2024.125184`) và Giudici & Raffinetti (`10.1016/j.eswa.2020.114104`). Link trực tiếp nằm trong [paper review](../docs/paper_review.md).
- **Kết quả được hỗ trợ:** tiêu đề, tác giả, DOI, venue/phạm vi chính và vai trò nền tảng khớp Planning. B2 dùng HMDA New York 2017 với race; B3 dùng SME credit ratings; M1 là nguồn phương pháp SL tổng quát; B1 là khung fairness credit scoring.
- **Giới hạn:** chưa xác minh toàn bộ công thức, code, action-code interpretation hoặc khả năng áp dụng SL nguyên trạng cho target ba lớp. Không ghi các paper là đã tái lập và không suy kết quả sang HMDA 2024 của dự án.
- **Bước tiếp theo:** đọc full method/appendix và kiểm ví dụ 3–4 feature trước implementation RQ2.

Các câu hỏi cần đọc/kiểm tiếp theo vẫn được quản lý theo kế hoạch gần hạn; không tạo kết quả giả để lấp log.
