# Chuẩn notebook cho dự án HMDA

**Trạng thái: REFERENCE — áp dụng cho notebook mới và các lần review.**

Notebook là nơi điều khiển phân tích, train, nghiên cứu và trực quan. Logic tái sử dụng, validation bắt buộc, pipeline và service nằm trong `src/hmda/`; Web API không import notebook.

## Phân tách theo mục đích

- `notebooks/eda/`: dữ liệu gần raw, kiểm chất lượng, cấu trúc và phân bố; không split, imputation, scaling hoặc encoding cho model.
- `notebooks/train/`: EDA phụ thuộc target trên train, thử nghiệm preprocessing, huấn luyện, chọn model trên validation và đánh giá test sau khi khóa.
- `notebooks/research/`: kiểm chứng phương pháp, GSV/SL, fairness NY và cross-region có điều kiện.

Không di chuyển kết luận giữa ba luồng khi provenance hoặc tập dữ liệu khác nhau. Biểu đồ hỗ trợ parse trong EDA không được gọi là preprocessing đã chọn.

## Cấu trúc một notebook

1. Mục tiêu, phạm vi và câu hỏi cần trả lời.
2. Đầu vào: `snapshot_id`, manifest, config, code version và notebook kernel.
3. Import package đã cài; không sửa `sys.path` hoặc dựa vào `cwd`.
4. Nạp và validate dữ liệu qua thành phần dùng chung.
5. Phân tích hoặc thực nghiệm theo đúng thứ tự dữ liệu → thao tác → output.
6. Assertions cho invariant quan trọng và kiểm đối soát số dòng/khóa.
7. Kết quả, giới hạn, quyết định được hỗ trợ và bước tiếp theo.
8. Tóm tắt bằng chứng: artifact, figure, bảng hoặc quality report được tạo thật.

Mỗi cell nên có một mục đích rõ. Đặt Markdown trước đoạn code khó hoặc biểu đồ để nêu câu hỏi và cách đọc; không diễn giải từng dòng code hiển nhiên.

## Cấu hình, đường dẫn và logging

Đọc tham số từ `configs/` qua loader dùng chung. Đường dẫn project do `src/hmda/core/path.py` giải từ `__file__` và marker dự án, không từ `cwd`. Notebook chỉ nhận đường dẫn ngoài repository qua cấu hình tường minh.

Dùng logger theo module hoặc run context; không tạo handler mới sau mỗi lần chạy cell. Ghi ID, bước, số dòng và cảnh báo cần thiết; không in secret hoặc toàn bộ DataFrame chỉ để debug.

## Dữ liệu và chống leakage

EDA snapshot giữ token nguồn và không áp dụng phép biến đổi học dữ liệu. Training dùng `record_id` và `split_manifest`; mọi imputation, encoding, scaling, feature selection hoặc estimator có trạng thái đều fit trên train. Validation dùng để chọn; test chỉ mở sau khi model và quy tắc đánh giá đã khóa.

API và RegionDataPipeline dùng lại model bundle đã fit, không fit lại trên request hoặc miền mới. Join bằng khóa trong đúng snapshot/run, không nối bằng vị trí dòng.

## Output và khả năng tái lập

Notebook phải hiển thị đơn vị, mẫu số, số dòng và phiên bản liên quan cạnh bảng/biểu đồ. Tên lớp dùng đúng mapping `action_taken` 1/2/3; kết quả fairness ghi chiều gap, lớp OvR, nhóm, county và metric không xác định.

Không ghi run hoặc snapshot giả. Output đã lưu chỉ là bằng chứng saved-output; chỉ ghi clean-kernel reproducible khi đã restart kernel, chạy toàn bộ theo thứ tự và kiểm output cuối trong môi trường được nêu.

Trước khi chia sẻ, xóa secret và thông tin cá nhân khỏi cell/output/metadata. Không xóa output cần review nếu chưa lưu bằng chứng ở nơi khác và chưa có yêu cầu phù hợp.

## Checklist review

- Đúng thư mục và đúng mục tiêu notebook.
- Input có snapshot/config/code/kernel rõ ràng.
- Không dùng `cwd`, `sys.path` thủ công hoặc đường dẫn máy cá nhân.
- EDA không bị trộn với split/preprocessing; train không dùng test để chọn.
- Assertions và validation đúng tầng, không dùng assert làm bảo vệ production duy nhất.
- Bảng/biểu đồ có nhãn, đơn vị, mẫu số và phạm vi kết luận.
- Output, log và metadata không chứa secret/dữ liệu cá nhân.
- Trạng thái chạy được mô tả đúng bằng chứng thực tế.
