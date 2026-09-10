# Paper review nền tảng

**Trạng thái:** DRAFT — metadata và phạm vi chính đã đối chiếu ngày 09/09/2026; chưa tuyên bố đã tái lập công thức hoặc kết quả paper.

Tài liệu này ghi paper nói gì, dự án kế thừa phần nào và bằng chứng còn phải tạo. Đây không phải systematic literature review và không dùng để tuyên bố chủ đề chưa từng được nghiên cứu.

## Bảng đối chiếu

| Mã | Nguồn | Dữ liệu/phạm vi paper | Vai trò trong dự án | Trạng thái |
| --- | --- | --- | --- | --- |
| B1 | Hurlin, Pérignon & Saurin, *The Fairness of Credit Scoring Models*, DOI `10.1287/mnsc.2022.03888` | Credit scoring; kiểm fairness và biến đóng góp vào thiếu fairness | Nền cho việc gắn hiệu năng với audit ở RQ1/RQ3 | Metadata và abstract đã xác minh; full-method reproduction chưa thực hiện |
| B2 | Agarwal, Muckley & Neelakantan, *Countering racial discrimination in algorithmic lending*, DOI `10.1016/j.econlet.2023.111117` | 157,269 HMDA loan applications, New York 2017; race; GSV/SL | Nền gần nhất cho RQ2 trên HMDA | Metadata, abstract và bản PDF kho tác giả đã xác minh; công thức/code chưa kiểm chứng |
| B3 | Chen, Giudici, Liu & Raffinetti, *Measuring fairness in credit ratings*, DOI `10.1016/j.eswa.2024.125184` | SME credit ratings; so Shapley–Lorenz giữa các nhóm | Nối explainability với fairness; phần SL theo nhóm là mở rộng | Metadata và abstract nhà xuất bản đã xác minh; không phải phương pháp bắt buộc của RQ3 |
| M1 | Giudici & Raffinetti, *Shapley–Lorenz eXplainable Artificial Intelligence*, DOI `10.1016/j.eswa.2020.114104` | Phương pháp global XAI dựa trên Lorenz Zonoid và Shapley | Nguồn phương pháp để xác minh định nghĩa SL | Metadata và abstract đã xác minh; công thức multiclass phải kiểm riêng |

## B1 — Fairness of Credit Scoring Models

Nguồn chính: [INFORMS/Management Science](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.2022.03888). Trang nhà xuất bản ghi công bố online ngày 14/11/2024 và bản in Volume 72(1), 406–425 năm 2026.

Paper trình bày khung kiểm fairness của scoring algorithms, nhận diện biến liên quan và xem xét trade-off fairness–performance. Dự án chỉ kế thừa tư duy đánh giá hiệu năng cùng audit, không mặc định tái hiện toàn bộ kiểm định hoặc tối ưu fairness của paper.

Bằng chứng dự án phải tạo: bảng năm model trên cùng split; sai số/tỷ lệ theo nhóm; metric, mẫu số và độ bất định; mô tả giới hạn. Nếu chỉ có descriptive gaps và khoảng tin cậy, báo đúng như vậy.

## B2 — Countering racial discrimination in algorithmic lending

Nguồn chính: [Maynooth University Research Archive](https://mural.maynoothuniversity.ie/id/eprint/17130/). Kho tác giả ghi đúng DOI, Economics Letters 226, article 111117 và cung cấp bản PDF.

Paper dùng HMDA New York 2017, target/race và thiết kế khác dự án HMDA New York 2024 ba lớp. Dự án dùng paper làm nền đối chiếu GSV và SL, nhưng quy ước GSV của dự án là mean absolute Shapley theo từng xác suất lớp. Không gọi kết quả dự án là tái lập nguyên mẫu.

Phần cần kiểm chứng trước implementation: action code và diễn giải nhãn trong paper; công thức GSV/SL; baseline; value function; normalization; coalition; code hoặc ví dụ số. Mapping `action_taken` của dự án phải dựa trên định nghĩa CFPB, không suy từ paper.

## B3 — Measuring fairness in credit ratings

Nguồn chính: [Elsevier/ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0957417424020517). Trang nhà xuất bản ghi Expert Systems with Applications 258, article 125184, ngày 15/12/2024.

Paper so sánh Shapley–Lorenz values giữa các nhóm trên dữ liệu xếp hạng SME. Điều đó khác HMDA loan-application classification và protected group của dự án. Dự án có thể học cách liên kết explainability với so sánh nhóm, nhưng RQ3 bắt buộc vẫn dùng selection rate, TPR, FPR, DPD và EOD theo lớp/county.

SL theo nhóm chỉ được mở rộng sau khi RQ2 đã kiểm chứng công thức và tài nguyên. Không dùng nó thay bộ fairness metrics hoặc suy kết quả của paper sang HMDA.

## M1 — Shapley–Lorenz XAI

Nguồn chính: [Elsevier/ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0957417420308575). Paper đề xuất global XAI kết hợp Lorenz Zonoid với Shapley value và minh họa bằng dữ liệu giá bitcoin.

Dự án phải xác minh công thức gốc trước khi viết `shapley_lorenz.py`. Với ba lớp, cần nêu rõ output class, nhãn quan sát, xác suất dự đoán và hàm giá trị; không giả định code nhị phân áp dụng nguyên trạng.

## Khoảng cách giữa paper và dự án

- Target dự án là `action_taken` ba lớp danh nghĩa; không paper nào ở trên tự động xác nhận thiết kế multiclass của dự án.
- RQ2 là applied comparison để học và kiểm chứng; không phải phát minh GSV/SL mới.
- RQ3 so Male/Female trong từng county New York. B2 tập trung race; B3 dùng SME/country/industry; B1 là credit scoring tổng quát.
- Điểm số trong paper khác dataset/target/năm không phải baseline phải vượt. Baseline trực tiếp của dự án được train trên cùng snapshot và split.

## Checklist trước khi đánh dấu đã đọc/đã áp dụng

- Lưu citation, DOI/link và phiên bản tài liệu đã đọc.
- Ghi dataset, target, protected group, model, metric và đơn vị phân tích.
- Trích công thức bằng ký hiệu nhất quán; kiểm ví dụ nhỏ độc lập trước dùng rộng.
- Phân biệt nội dung paper, lựa chọn của dự án và kết quả thực nghiệm của dự án.
- Chỉ ghi `VERIFIED` khi đã nêu phép kiểm và bằng chứng; metadata đúng không đồng nghĩa phương pháp đã được tái lập.
