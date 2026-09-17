# Kiểm tra

`unit/`, `integration/` và `e2e/` phân tách kiểm tra theo ranh giới thật. Phase 1 có test cho path, config/secret, logging/exceptions và component contracts; số test lịch sử nằm trong task/evidence của lần chạy tương ứng. Phase 2 đã có unit test framework, record reconciliation/snapshot artifact và integration source-contract/DB migration; các test fairness, explainability, pipeline model và e2e vẫn là placeholder. Không dùng số test hoặc fixture để suy G2–G8 đã đạt.

## Phạm vi test

| Tầng | Trách nhiệm |
| --- | --- |
| Unit | Function/class nhỏ: path, config, validation rule, ID/hash, metric, grouping và serialization |
| Integration | PostgreSQL/CSV snapshot, ba pipeline, model bundle, result repository và API parity |
| End-to-end | Luồng demo từ input hợp lệ tới response/bảng hiển thị trên môi trường đã chốt |

Data-quality tests cần fixture nhỏ có lỗi biết trước: schema/type, token NA/Exempt, target ngoài phạm vi, khóa trùng/mất, join sai số dòng và checksum mismatch. Fairness fixture phải kiểm chiều `Female − Male`, lớp OvR, denominator 0/undefined và EOD worst-case bằng phép tính tay.

TASK-021 có integration test local đi qua `ConfigLoader`, owner-attested source registration, `CSVBytesLoader`, `ConfigurableDataValidator`, record fingerprint/reconciliation summary và transport publish guard. Test xác minh đúng internal version/checksum, 18 business columns cộng 3 technical fields, 293.301 dòng, `record_id` duy nhất và ba cảnh báo đã ghi; riêng test này không tạo quality artifact, ingestion run, DB round-trip hoặc snapshot `READY`.

Block 3B có unit test cho fingerprint/reconciliation, staging COPY/retry/promote, READY reader, row-count publish guard và atomic snapshot gồm `data.csv`, `manifest.json`, `quality_report.json`. Block 3C bổ sung runner thật, streaming snapshot reconciliation, staging cleanup và retry evidence. TASK-024 chạy lại full regression: 116 test đạt, 1 DB-DDL test tách biệt skipped vì không cấu hình biến test/DDL opt-in; đồng thời kiểm live DB/snapshot và đóng G2 tối giản.

Training/region tests phải chứng minh transformer fit chỉ trên train, test không dùng để chọn, model không refit ở region/API và unknown category có hành vi đã chốt. PostgreSQL integration cần kiểm transaction, rollback, retry và idempotency dưới hai yêu cầu cùng nguồn/config.

## Bằng chứng và cách viết test

Tên test mô tả hành vi và điều kiện; fixture nhỏ, xác định và không phụ thuộc dữ liệu cá nhân. Mock chỉ dùng ở ranh giới ngoài; không mock chính logic cần kiểm. Assert hỗ trợ test, nhưng đường production vẫn cần validation/exception.

Mỗi gate dẫn đúng lệnh, môi trường, số test và kết quả đã chạy. Không ghi `passed` từ tên file, output cũ hoặc test bị skip. Test có network/PostgreSQL phải tách marker và nêu prerequisite; không âm thầm dùng DB chung.

Viết test có ý nghĩa cùng phần triển khai tương ứng. Khi hợp đồng thay đổi, cập nhật test và tài liệu nguồn trong cùng phạm vi review.

Lệnh chuẩn tại project root là `uv run pytest`. Bằng chứng chạy ngày 2026-09-09 và phiên bản môi trường nằm tại [reproducibility](../docs/reproducibility.md).
