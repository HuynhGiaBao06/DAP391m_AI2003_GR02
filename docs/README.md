# Chỉ mục tài liệu dự án HMDA

File này giúp thành viên tìm đúng nguồn thông tin và biết tài liệu nào đã đủ dùng. Không dùng một tài liệu ở trạng thái `DRAFT` hoặc `PENDING EVIDENCE` làm bằng chứng rằng pipeline, dữ liệu hay mô hình đã được nghiệm thu.

## Trạng thái tài liệu

- `APPROVED`: nội dung nền đã được người dùng chấp nhận; thay đổi phạm vi phải được ghi nhận.
- `DRAFT`: đủ để review và tiếp tục hoàn thiện, nhưng vẫn chứa mục chưa chốt.
- `PENDING EVIDENCE`: cấu trúc đã có; nội dung kết quả chỉ được điền từ lần chạy hoặc artifact thật.
- `REFERENCE`: hướng dẫn dùng chung, không phải bằng chứng thực thi.

## Nguồn sự thật chính

| Tài liệu | Vai trò | Trạng thái hiện tại |
| --- | --- | --- |
| [Project Master](HMDA_Project_Master_Main.docx) | Kiến trúc, phase, phạm vi và điều kiện nghiệm thu toàn dự án | APPROVED, v1.1 |
| [Project Planning](HMDA_New_York_Project_Planning.docx) | Ba RQ, cohort, thiết kế nghiên cứu và căn cứ phương pháp | APPROVED, v1.1 |
| [Protocol](protocol.md) | Quyết định thực nghiệm có hiệu lực và các mục đang chờ | DRAFT |
| [Paper review](paper_review.md) | Bằng chứng từ paper, phần kế thừa và giới hạn áp dụng | DRAFT |
| [API contract](api_contract.md) | Hợp đồng Web API độc lập với implementation | DRAFT v0 |
| [Notebook guidelines](notebook_guidelines.md) | Chuẩn tổ chức, chạy và review notebook | REFERENCE |
| [Reproducibility](reproducibility.md) | Hợp đồng tái lập và ma trận bằng chứng | DRAFT |
| [Data card](data_card.md) | Dữ liệu thực tế, lineage, chất lượng và giới hạn | PENDING EVIDENCE |
| [Model card](model_card.md) | Model đã chọn, metric, fairness và giới hạn | PENDING EVIDENCE |
| [Deployment](deployment.md) | Môi trường demo, vận hành và rollback đã kiểm chứng | PENDING EVIDENCE |

## Tài liệu vận hành theo khu vực

- [README dự án](../README.md): điểm vào cho thành viên và mô tả kiến trúc tổng quan.
- [Cấu hình](../configs/README.md): trách nhiệm từng file cấu hình và quy tắc nạp tham số.
- [Dữ liệu local](../data/README.md): PostgreSQL, CSV nguồn, snapshot và manifest.
- [SQL](../sql/README.md): migration và truy vấn kiểm tra chất lượng.
- [Artifacts](../artifacts/README.md): cấu trúc output theo `run_id`.
- [Tests](../tests/README.md): phạm vi test và loại bằng chứng.
- [Git workflow](git/WORKFLOW.md): nhánh, commit, pull request, review và conflict.
- [Contributing](../CONTRIBUTING.md) và [Security](../SECURITY.md): quy trình đóng góp và bảo vệ dữ liệu/secret.

## Quy tắc cập nhật

Mỗi loại thông tin có một nguồn chính. Master không chứa kết quả chạy; protocol không chứa tham số runtime thay cho `configs/`; data card và model card không chứa số liệu chưa tạo. Khi một quyết định thay đổi, cập nhật nguồn chính trước rồi sửa các link hoặc mô tả bị ảnh hưởng.

Trước khi đổi trạng thái thành `APPROVED` hoặc `PENDING EVIDENCE` thành hoàn tất, kiểm link, đối chiếu Master/Planning và dẫn tới bằng chứng mà thành viên khác có thể truy cập. Với DOCX hoặc tài liệu có bố cục trang, phải kết xuất và kiểm trực quan sau lần sửa cuối.
