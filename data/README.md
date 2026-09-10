# Dữ liệu local

PostgreSQL là nguồn dữ liệu dùng chung cho pipeline; `data/` giữ tệp nguồn và bản xuất snapshot phục vụ tái lập/local analysis. Hiện chưa có dữ liệu, kết nối PostgreSQL, `source_id` hoặc `snapshot_id` thật.

## Cấu trúc local

| Vị trí | Nội dung | Tính chất |
| --- | --- | --- |
| `raw/<source_id>/source.csv` | Tệp nguồn HMDA đúng phiên bản đã nhận | Bất biến sau khi đăng ký |
| `raw/<source_id>/manifest.json` | Nguồn, hash, kích thước, schema/header và thời điểm nhận | Đi cùng source CSV |
| `snapshots/eda/<snapshot_id>/` | `data.csv`, manifest và quality report cho dữ liệu gần raw | Không split/imputation/scaling/OHE |
| `snapshots/training/<snapshot_id>/` | Dữ liệu trước preprocessing, manifest và `split_manifest.csv` | Giữ `record_id` và split khóa |
| `snapshots/region/<snapshot_id>/` | Dữ liệu miền đối chiếu, manifest và compatibility report | Không fit lại model NY |

Toàn bộ CSV và nội dung snapshot bị loại khỏi Git. Chỉ README và marker thư mục được theo dõi. Nơi phân phối dữ liệu cho nhóm chưa được quyết định.

## Vòng đời nguồn và snapshot

1. Nhận CSV nguồn và ghi metadata; tính hash trước khi parse.
2. Kiểm header/schema/encoding và đăng ký `source_id`.
3. Nạp staging bằng một ingestion run có ID và transaction rõ.
4. Đối soát số dòng, khóa, token và chạy quality rules đúng tầng.
5. Tạo snapshot metadata ở trạng thái chưa công bố; xuất CSV qua file tạm.
6. Kiểm checksum và đối soát DB ↔ CSV theo `record_id`.
7. Chỉ chuyển snapshot thành `READY` khi dữ liệu, manifest, quality report và export nhất quán. Run lỗi giữ `FAILED` và không được reader chọn.

CSV sửa tay không cập nhật ngược PostgreSQL. Nếu cần dùng, đăng ký nó như nguồn mới để giữ lineage. PostgreSQL không thay thế bản raw gốc và manifest.

## ID, manifest và tính bất biến

`record_id` được tạo từ phiên bản/tệp nguồn và số thứ tự dòng gốc theo thuật toán đã version; giữ ổn định qua lọc. ID không chứng minh các dòng là những cá nhân duy nhất. Không dùng DataFrame index làm khóa.

Manifest snapshot tối thiểu gồm `snapshot_id`, `parent_snapshot_id`, `source_id/source_hash`, schema version, config hash, code version, protocol version, cohort/filter, số dòng/cột, danh sách cột/kiểu, thời gian tạo và trạng thái. Training snapshot thêm split strategy/seed và checksum của `split_manifest`.

Snapshot `READY` là bất biến. Sửa schema, filter hoặc logic biến đổi tạo snapshot mới có parent; không ghi đè để giữ cùng ID. Mỗi run tham chiếu snapshot có thật, không tạo ID giả trong tài liệu hoặc notebook.

## Quality gate

Quality report ghi `rule_id`, tầng dữ liệu, severity `ERROR/WARNING`, số dòng ảnh hưởng, ID minh họa đã giới hạn, phiên bản rule và kết quả. `ERROR` chặn công bố; `WARNING` được giữ để điều tra. `is_valid = true` chỉ nghĩa không còn lỗi chặn.

Không tự xóa outlier, impute, đổi NA/Exempt hoặc sửa category để vượt gate. Assert hỗ trợ kiểm invariant trong test/notebook; validation và exception mới là hàng rào của pipeline/API.

Tối thiểu cần kiểm: header/schema; parse/token đặc biệt; target/cohort; uniqueness/khóa ngoại; số dòng qua từng bước; checksum; join một-một; probability/label mapping ở bảng predictions; idempotency, rollback, retry và hai ingestion chạy đồng thời.

## Ba loại snapshot

- **EDA:** gần raw để hiểu nguồn/chất lượng/phân bố; giữ token và missingness; không dùng làm bằng chứng preprocessing đã chọn.
- **Training:** dữ liệu trước biến đổi học tham số, đi cùng split manifest; transformer/model chỉ fit trên train.
- **Region:** áp cùng schema/protocol và model NY đã fit; ghi unknown category, missingness và khác biệt phạm vi. Chạy bang thật vẫn là mở rộng chờ quyết định.

## Quy tắc sử dụng

Reader phải yêu cầu `snapshot_id` cụ thể và chỉ đọc trạng thái `READY`. Join analysis/split/predictions trong cùng snapshot/run bằng khóa, kiểm số dòng trước và sau. Không nối bằng vị trí hoặc tự chọn snapshot mới nhất mà không ghi ID.

Export CSV dùng encoding, thứ tự cột, biểu diễn NULL/NA/Exempt và serialization ổn định đã được version. Ghi vào file tạm rồi đổi tên khi hoàn tất; lỗi filesystem có thể xuất lại từ cùng snapshot nhưng không tự đổi dữ liệu DB.
