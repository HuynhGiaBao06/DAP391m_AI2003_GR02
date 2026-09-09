# Dữ liệu local

PostgreSQL là nguồn chung; thư mục này giữ CSV nguồn và bản xuất snapshot. Hiện chưa có dữ liệu.

- raw/<source_id>/: source.csv và manifest.json.
- snapshots/eda/<snapshot_id>/: data.csv và manifest.json; dữ liệu gần raw.
- snapshots/training/<snapshot_id>/: data.csv, manifest.json và split_manifest.csv.
- snapshots/region/<snapshot_id>/: data.csv và manifest.json cho vùng đối chiếu.

Chỉ tạo source_id/snapshot_id thật khi pipeline hoạt động. Không tạo CSV hoặc snapshot giả để lấp chỗ trống.
Nội dung dữ liệu được loại khỏi Git. Cơ chế quality, checksum, đối soát PostgreSQL/CSV và công bố bất biến sẽ triển khai tại Phase 2.
