# Hợp đồng tái lập

**Trạng thái:** DRAFT — runtime và unit test Phase 1 đã được xác minh ngày 2026-09-09; tái lập sạch bởi thành viên khác và các luồng dữ liệu/model/API chưa thực hiện.

Một kết quả được gọi là tái lập khi thành viên khác có thể dùng đúng source/snapshot, code, config và môi trường để tạo lại output trong tolerance đã công bố. File tồn tại, notebook có output cũ hoặc import được package chưa đủ chứng minh.

## Provenance bắt buộc

Mỗi snapshot/run/model/result phải truy vết được tối thiểu:

- `source_id` và `source_hash`;
- `snapshot_id`, schema version và quality report;
- Git commit/code version;
- resolved config đã che secret và `config_hash`;
- protocol version;
- runtime/dependency lock và platform cần thiết;
- `run_id`, thời gian, pipeline, seed/split;
- input/output checksum hoặc artifact manifest;
- trạng thái `READY`, `FAILED` hoặc `NOT RUN`.

Không điền giá trị minh họa vào các trường trên như thể là ID thực.

## Mức bằng chứng

| Mức | Ý nghĩa được phép ghi |
| --- | --- |
| Source review | Đã đọc code/config/tài liệu; chưa chạy |
| Static check | Parse, link, schema tĩnh hoặc lint đạt; chưa chứng minh runtime/data |
| Saved output | Đã đối chiếu output lưu sẵn; không phải lần chạy mới |
| Targeted run | Một test/lệnh cụ thể đã chạy trong môi trường được nêu |
| Clean reproduction | Thiết lập sạch, chạy toàn luồng theo thứ tự và đối chiếu output cuối |

Mọi báo cáo phải dùng đúng tên mức bằng chứng, kèm thời điểm và phạm vi.

## Môi trường

Phase 1 khóa Python 3.13.x bằng `.python-version` tại 3.13.9, dùng `uv` và `uv.lock`. Package được cài editable theo `src` layout. Notebook kernel và command-line interpreter import cùng package, không sửa `sys.path`. `path.py` tìm root bằng `__file__` và marker dự án, không dùng `cwd`.

Secret/địa chỉ triển khai lấy từ môi trường; file mẫu chỉ chứa tên biến. Cần ghi OS/phần cứng khi chúng ảnh hưởng runtime, SL hoặc kết quả số. Endpoint DB, dữ liệu và môi trường chạy nghiên cứu vẫn `PENDING`.

## Bằng chứng Phase 1 ngày 2026-09-09

Môi trường thử: Windows, Python 3.13.9, `uv` 0.10.6, package `hmda-project` 0.1.0, PyYAML 6.0.3, pytest 8.4.2 và ipykernel 6.31.0.

| Kiểm tra đã chạy | Kết quả |
| --- | --- |
| `uv sync --dev` từ `pyproject.toml`/`uv.lock` | Tạo `.venv`, cài 33 package và package dự án ở chế độ editable |
| `.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=<thư mục tạm duy nhất>` | 22 test được thu thập, 22 passed trong 0.13 giây ở lần chạy cuối |
| `.venv\Scripts\python.exe -m compileall -q src` | Đạt, không có lỗi compile |
| `uv lock --check` và `uv pip check` | Lockfile hợp lệ; 33 package đã cài không có xung đột được báo |
| Import từ thư mục cha repository | `hmda.__version__ == 0.1.0`; root trả đúng repository, không phụ thuộc `cwd` |
| Khởi động kernel `hmda-project` và thực thi import/root | Đạt; kernel trả version 0.1.0 và đúng project root |

Lệnh thiết lập dùng chung:

```powershell
uv sync --dev
uv run pytest
uv run python -c "import hmda; print(hmda.__version__)"
uv run python -m ipykernel install --user --name hmda-project --display-name "Python (HMDA Project)"
```

Máy kiểm thử có một thư mục pytest cũ trong `%TEMP%` bị sai quyền. Lần chạy cuối dùng một `--basetemp` có tên UUID mới và đạt 22/22; nếu gặp cùng lỗi, dùng:

```powershell
$pytestTemp = Join-Path ([System.IO.Path]::GetTempPath()) ("hmda-pytest-" + [guid]::NewGuid().ToString("N"))
uv run pytest -p no:cacheprovider --basetemp=$pytestTemp
```

Kernel chỉ cần đăng ký lại khi môi trường/user profile thay đổi. Bằng chứng trên là targeted run (lần chạy có mục tiêu) của Phase 1, chưa phải clean reproduction: chưa có thành viên thứ hai dựng môi trường sạch, và không có data/notebook/DB/model/API nào được chạy.

## Trình tự tái lập dự kiến

1. Checkout đúng code version và cài môi trường từ lockfile đã duyệt.
2. Cấp secret/địa chỉ dữ liệu ngoài Git theo quyền; validate config.
3. Xác minh raw source bằng hash và tạo/đọc snapshot `READY` cụ thể.
4. Chạy quality gate; không tiếp tục khi còn `ERROR`.
5. Chạy EDA, training, RQ2, RQ3 hoặc API theo dependency trong Master.
6. Ghi run/artifact manifest, checksum và trạng thái.
7. Đối chiếu metric, số dòng, mapping lớp, fairness denominators và offline/API parity theo tolerance đã khóa.

Lệnh cho pipeline dữ liệu/model/API chỉ được thêm sau khi đã chạy thành công trong môi trường tương ứng. Không viết lệnh giả hoặc dùng đường dẫn máy cá nhân làm hướng dẫn chung.

## Yêu cầu theo đầu ra

- **Data:** cùng source/config/schema tạo snapshot có row/key reconciliation và checksum theo hợp đồng.
- **RQ1:** cùng split/model config tạo metric trong tolerance; model selection không đọc test trước khóa.
- **RQ2:** cùng sample/background/seed/formula tạo ranking và diagnostic đã định; ghi tài nguyên.
- **RQ3:** cùng predictions/audit config tạo rate, gap, mẫu số và trạng thái undefined giống nhau.
- **API:** cùng model bundle/input tạo cùng class/probabilities với offline trong tolerance.
- **Tài liệu:** số liệu, bảng và figure dẫn đúng artifact/run; DOCX/PPTX được kiểm trực quan.

## Gate hoàn thiện tài liệu này

Tài liệu chỉ chuyển khỏi `DRAFT` khi runtime/dependency lock đã có; setup được thử từ môi trường sạch; lệnh data/test/notebook/API đã kiểm; một thành viên khác tái lập đường chính; mọi khác biệt ngoài tolerance được giải thích. Mục chưa chạy phải ghi `NOT RUN`, không suy từ scaffold.
