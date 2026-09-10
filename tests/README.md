# Kiểm tra

`unit/`, `integration/` và `e2e/` phân tách kiểm tra theo ranh giới thật. Phase 1 hiện có 22 unit test cho path, config/secret, logging/exceptions và component contracts. Các test fairness, explainability, integration và e2e vẫn là placeholder; 22 test này không phải bằng chứng cho G2–G8.

## Phạm vi test

| Tầng | Trách nhiệm |
| --- | --- |
| Unit | Function/class nhỏ: path, config, validation rule, ID/hash, metric, grouping và serialization |
| Integration | PostgreSQL/CSV snapshot, ba pipeline, model bundle, result repository và API parity |
| End-to-end | Luồng demo từ input hợp lệ tới response/bảng hiển thị trên môi trường đã chốt |

Data-quality tests cần fixture nhỏ có lỗi biết trước: schema/type, token NA/Exempt, target ngoài phạm vi, khóa trùng/mất, join sai số dòng và checksum mismatch. Fairness fixture phải kiểm chiều `Female − Male`, lớp OvR, denominator 0/undefined và EOD worst-case bằng phép tính tay.

Training/region tests phải chứng minh transformer fit chỉ trên train, test không dùng để chọn, model không refit ở region/API và unknown category có hành vi đã chốt. PostgreSQL integration cần kiểm transaction, rollback, retry và idempotency dưới hai yêu cầu cùng nguồn/config.

## Bằng chứng và cách viết test

Tên test mô tả hành vi và điều kiện; fixture nhỏ, xác định và không phụ thuộc dữ liệu cá nhân. Mock chỉ dùng ở ranh giới ngoài; không mock chính logic cần kiểm. Assert hỗ trợ test, nhưng đường production vẫn cần validation/exception.

Mỗi gate dẫn đúng lệnh, môi trường, số test và kết quả đã chạy. Không ghi `passed` từ tên file, output cũ hoặc test bị skip. Test có network/PostgreSQL phải tách marker và nêu prerequisite; không âm thầm dùng DB chung.

Viết test có ý nghĩa cùng phần triển khai tương ứng. Khi hợp đồng thay đổi, cập nhật test và tài liệu nguồn trong cùng phạm vi review.

Lệnh chuẩn tại project root là `uv run pytest`. Bằng chứng chạy ngày 2026-09-09 và phiên bản môi trường nằm tại [reproducibility](../docs/reproducibility.md).
