# Cấu hình tập trung

`configs/` là nơi duy nhất chỉnh tham số dùng chung của dự án. `project.yaml`, `database.yaml`, `logging.yaml` và trạng thái `preprocessing.yaml` đã được `ConfigLoader` nạp/kiểm ở Phase 1. TASK-021 đã ghi schema quan sát, hash và quality rules cho file local `state_NY_filter.csv`; mapping nội bộ `action_taken 0/1/2` đã được người dùng xác nhận và map về mã HMDA `1/2/3`. Source provenance/version và định dạng `county_code` vẫn chưa đạt, nên nguồn chưa được phép publish. Các giá trị training và evaluation vẫn `PENDING`. Kiến trúc gốc nằm trong [Project Master](../docs/HMDA_Project_Master_Main.docx); quyết định thực nghiệm nằm trong [protocol](../docs/protocol.md).

## Trách nhiệm từng file

| File | Nội dung được phép chứa | Không được chứa |
| --- | --- | --- |
| `project.yaml` | Tên dự án, marker root, đường dẫn tương đối, quy ước ID/version | Đường dẫn home của một thành viên |
| `database.yaml` | Host/port/database/schema theo biến môi trường, pool/timeout không bí mật | Password, token hoặc connection URI thật |
| `data.yaml` | Nguồn, năm/bang, cohort filter, vị trí raw/snapshot | Quy tắc preprocessing học từ dữ liệu |
| `schema.yaml` | Tên cột, kiểu, nullable, unit, role, allowed token/category | Giá trị quan sát bịa hoặc schema chưa đối chiếu nhưng ghi như đã xác minh |
| `quality.yaml` | `rule_id`, severity, tolerance và tầng áp dụng | Quy tắc tự sửa/xóa dữ liệu để vượt gate |
| `preprocessing.yaml` | Phương án đã được duyệt sau phân tích | Giá trị mặc định tạm, secret hoặc quyết định chưa duyệt |
| `training.yaml` | Split, seed, model candidates, search budget | Metric fairness hoặc kết quả chạy |
| `evaluation.yaml` | Metric RQ1, GSV/SL, fairness, region và ngưỡng đã khóa | Số liệu kết quả hoặc lựa chọn sửa sau khi xem test |
| `logging.yaml` | Level, handler, format, redaction và trường context | Payload/hồ sơ đầy đủ hoặc đường dẫn log cá nhân cố định |
| `local.env.example` | Tên biến môi trường và giá trị minh họa an toàn | Secret thật |

## Nạp và kiểm cấu hình

`ConfigLoader` đọc các YAML bắt buộc thành một `ConfigBundle`. Khi caller không truyền mapping môi trường tường minh, loader nạp `configs/local.env` nếu file tồn tại rồi để biến môi trường của process ghi đè; test có thể truyền `environment={}` để không chạm secret local. Override chỉ được thay đường dẫn trường đã tồn tại; sau đó tham chiếu môi trường được resolve cho secret/địa chỉ triển khai. Không đọc tham số từ `cwd`, cell notebook hoặc một file YAML thứ hai trong artifact như nguồn chỉnh sửa.

Loader cấu hình dừng sớm khi thiếu file bắt buộc, root YAML không phải mapping, root marker/path project sai, logging level không hợp lệ, override không tồn tại hoặc preprocessing còn pending nhưng có method. Quality validator kiểm rule generic và các rule raw HMDA, gồm checksum, header, token, định dạng chuỗi và khả năng parse số. Rule cohort chỉ áp dụng sau lọc; mapping target đã xác nhận, còn feature timing và split chưa được chốt.

Validation trả lỗi có `field_path` và thông điệp có thể xử lý, nhưng không in secret. Resolved config có bản redacted, serialization chuẩn hóa và SHA-256 `config_hash`; hash này là hạ tầng, chưa phải ID của một run/snapshot thật.

## Đường dẫn và môi trường

Đường dẫn tương đối được giải từ project root do `src/hmda/core/path.py` tìm bằng `__file__` và marker `pyproject.toml` cùng `src/hmda`; không dùng hoặc fallback về `cwd`. Đường dẫn dữ liệu/artifact ngoài repository phải được khai báo tường minh cho môi trường đó.

`configs/local.env` là file local bị Git loại trừ. Môi trường triển khai nên cấp secret bằng cơ chế của nền tảng, không đóng gói file secret vào image/artifact.

## Đóng băng cấu hình cho snapshot và run

Khi pipeline hoạt động, mỗi snapshot/run lưu bản cấu hình đã resolve và che secret, cùng `config_hash`, `code_version` và schema/protocol version. Hash dùng trên dạng serialization chuẩn hóa đã được định nghĩa; không coi hai file có thứ tự key khác là hai cấu hình nghiệp vụ khác nếu loader chuẩn hóa chúng giống nhau.

Bản cấu hình trong artifact là bằng chứng đã dùng, không phải nguồn để chỉnh tham số. Chạy lại từ artifact phải kiểm version và từ chối secret bị thiếu bằng lỗi rõ.

## Trạng thái chưa chốt

Preprocessing tiếp tục để trống đến khi hoàn tất data quality, EDA gần raw và thử nghiệm train/validation. Python/dependency lock đã chốt ở Phase 1; schema PostgreSQL raw-first và quyền runtime đã được kiểm trên Neon PostgreSQL 18.6 branch test nhưng chưa deploy vào DB đích. Ngưỡng fairness, region, frontend/hosting và latency chưa được điền cho tới khi có quyết định/bằng chứng tương ứng.
