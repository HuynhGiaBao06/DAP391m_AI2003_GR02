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

## RL-002 — Đối chiếu source contract file HMDA New York dẫn xuất local

- **Ngày / phạm vi:** 2026-09-11; TASK-021; đọc-only toàn bộ `data/raw/state_NY_filter.csv`, không sửa raw, không chạy notebook hoặc DB.
- **Trạng thái / loại bằng chứng:** OBSERVED + OWNER ATTESTATION — đọc streaming ngày 2026-09-11 và integration registration→loader→validator chạy lại ngày 2026-09-13 trên đúng checksum local; BaoHG xác nhận quyền quản trị, ngày 2026-09-13, 18 cột và mapping target. Đây là internal derived asset, không suy thành upstream HMDA release.
- **Nguồn dữ liệu và tài liệu:** file local đã được kiểm checksum trong evidence nội bộ; [CFPB 2024 HMDA release](https://www.consumerfinance.gov/about-us/newsroom/2024-hmda-data-on-mortgage-lending-now-available/); [2024 HMDA Filing Instructions Guide](https://files.ffiec.cfpb.gov/documentation/2024-hmda-fig.pdf); [FFIEC 2024 dynamic dataset](https://ffiec.cfpb.gov/data-publication/dynamic-national-loan-level-dataset/2024).
- **Mẫu và phép kiểm:** 293.301 dòng, 18 cột; kiểm toàn bộ header/row width, token, missing, numeric parse, regex county/LEI và exact-row equality trên 18 cột.
- **Kết quả:** cấu trúc CSV hợp lệ; `activity_year=2024` và `state_code=NY` cho mọi dòng. Target nội bộ dùng `0/1/2`: `0=Loan originated/HMDA 1`, `1=Approved but not accepted/HMDA 2`, `2=Application denied/HMDA 3`; toàn bộ 293.301 dòng thuộc miền này. Sex ngoài cohort 1/2 có 26.238 dòng. Lần chạy 2026-09-13 đánh giá 25 rules và tái tạo đúng ba `WARNING`: county format 291.922, county missing 1.379, exact-row excess 699; 0 `ERROR`, transport guard đạt.
- **Kết luận được hỗ trợ:** mapping target là chủ ý và không phải lỗi dữ liệu; source identity local có thể được đăng ký bằng owner attestation, internal version và checksum mà không bịa URL/release bên ngoài. County vẫn chưa phù hợp cho phân tích; equality trên 18 cột không chứng minh duplicate application vì file không có application ID duy nhất.
- **Giới hạn:** không có file pre-filter để kiểm chứng độc lập 17 cột còn lại; chưa đánh giá feature timing/leakage hoặc kiểm mapping qua model/API. Block 3C ngày 2026-09-14 đã kiểm HMDA DB round-trip và sinh persisted quality/snapshot; đây là transport evidence, không biến county thành analysis-ready.
- **Issue / bước tiếp theo:** TASK-021/TASK-023/TASK-024 `DONE`; G2 tối giản đã nghiệm thu. DATA-001 `RESOLVED`; TECH-002 `CLOSED` cho transport; DATA-002/RQ-I02/RQ-I04 còn mở cho phase sau.

## RL-004 — Round-trip HMDA thật trên PostgreSQL và snapshot local

- **Ngày / phạm vi:** 2026-09-14; TASK-023 Block 3C; local → Neon `neondb` → local snapshot, không chạy notebook/EDA/preprocessing và không sửa raw.
- **Trạng thái / loại bằng chứng:** OBSERVED + REVIEWED — live ingestion/readback, persisted DB state, artifact filesystem và full regression; TASK-024 tính lại evidence và nghiệm thu PASS G2 ngày 2026-09-14.
- **Mẫu và phép kiểm:** 293.301 record; đúng 18 business columns lưu `TEXT` cộng 3 technical fields; đối soát số dòng, distinct `record_id`, source row range, ordered content checksum, snapshot file checksum, quality checksum và retry idempotency.
- **Kết quả:** 1 source, 1 ingestion `READY`, 1 snapshot `READY`, 1 quality result; raw/READY cùng 293.301 dòng, 293.301 `record_id` duy nhất, staging=0. Content checksum `452f389d5665d35ab50334a5f4e82a2ba2f003cb2671c944793febc57d6da2ea`; snapshot data checksum `a887fc75f75b66545bce7c7ff818302be2f63ee7bed92dcc6c85ec2aec505eea`. Quality tái tạo 0 ERROR và 3 WARNING: county format 291.922, county missing 1.379, exact-row excess 699.
- **Kết luận được hỗ trợ:** transport local↔DB↔snapshot bảo toàn số dòng, khóa, thứ tự cột và raw token cho source hiện tại; retry dùng lại đúng logical ingestion/snapshot và không nhân dữ liệu. TASK-024 xác nhận snapshot đủ evidence để đóng G2 tối giản.
- **Giới hạn:** chưa kiểm concurrency stress, restore drill, failure injection đúng khe DB-commit/filesystem-move hoặc phân phối artifact cho nhóm; county vẫn không sẵn sàng cho grouping/fairness. Các mục này được giữ ngoài G2 theo DEC-011 hoặc issue tương ứng, không bị mô tả là đã hoàn thành.
- **Artifact / bước tiếp theo:** `artifacts/runs/ing-ab0bb683a84aabbbbcc09afc/phase2_roundtrip.json`; `data/snapshots/eda/hmda-2024-ny-ab0bb683a84aabbbbcc09afc/`; Phase 3 chỉ bắt đầu sau khi chốt task/phạm vi và xử lý DATA-002 trước mọi phân tích county.

## RL-003 — Căn cứ business context của target ba lớp

- **Ngày / phạm vi:** 2026-09-12; TASK-025; rà soát ý nghĩa `action_taken` và business framing, không chạy dữ liệu, notebook hoặc mô hình.
- **Trạng thái / loại bằng chứng:** OBSERVED — đối chiếu văn bản chính thức; chưa phải bằng chứng định lượng trên cohort New York 2024.
- **Nguồn:** CFPB Regulation C official interpretations cho 12 CFR 1003.4(a)(8)(i); OCC Comptroller's Handbook, Mortgage Banking, Appendix B trang 164 và glossary trang 217; CFPB Intent to Proceed.
- **Kết quả được hỗ trợ:** `Approved but not accepted` dùng khi tổ chức đã đưa ra quyết định phê duyệt trước closing/account opening và chỉ còn điều kiện cam kết/closing thông thường, nhưng người nộp đơn/bên nhận không phản hồi hoặc khoản vay không được hoàn tất. Các khoản trong origination pipeline không đi đến closing được OCC mô tả là fallout; lịch sử fallout có liên quan đến dự báo và quản trị pipeline.
- **Cách áp dụng:** xem target ba lớp như kết quả của hai điểm trong mortgage application funnel: approval so với denial, rồi origination so với approved-but-not-accepted trong nhóm đã được phê duyệt. Cách hiểu này tạo business context cho RQ1–RQ3 mà không đổi target hay protocol.
- **Giới hạn:** HMDA không ghi nguyên nhân cụ thể của từng hồ sơ lớp 2. Không suy pricing, cạnh tranh, trải nghiệm khách hàng, sự cố closing, rate lock, chi phí, doanh thu hay hedging loss cho từng hồ sơ nếu không có dữ liệu bổ sung. Không đồng nhất mọi lớp 2 với rate-locked fallout.
- **Decision / artifact:** DEC-010; Project Master v1.2, Project Planning v1.2 và Research Plan v2.2.
