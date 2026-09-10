# HMDA New York 2024

Dự án DAP391m · AI2003 · Group 2 nghiên cứu dự đoán trạng thái xử lý hồ sơ vay trên HMDA New York 2024, giải thích mô hình và đánh giá fairness, sau đó đưa kết quả vào ứng dụng Web thông qua API.

**Trạng thái hiện tại: hạ tầng lõi Phase 1 đã triển khai và đang chờ review G1; chưa nhập dữ liệu, triển khai pipeline nghiệp vụ, huấn luyện model hoặc vận hành API.**

## Mục tiêu và phạm vi

- **RQ1:** so sánh Logistic Regression, Decision Tree, Random Forest, XGBoost và MLP, kèm baseline; chọn model trên validation với macro-F1 là chỉ số chính.
- **RQ2:** đối chiếu GSV và Shapley–Lorenz theo từng lớp trên Logistic Regression và model phi tuyến được chọn. Phương pháp phải được kiểm chứng trước thực nghiệm rộng.
- **RQ3:** đánh giá chênh lệch giữa các nhóm giới tính trong các county đủ điều kiện tại New York. Thực nghiệm trên bang khác là phần mở rộng có điều kiện.

Target `action_taken` gồm ba lớp: khoản vay đã được cấp, hồ sơ được chấp thuận nhưng người nộp không chấp nhận, và hồ sơ bị từ chối. Kết quả mô tả xử lý hồ sơ lịch sử; không phải dự đoán vỡ nợ hoặc quyết định cấp tín dụng thực tế.

## Tài liệu chính

- [Project Master](docs/HMDA_Project_Master_Main.docx): kiến trúc, phạm vi công việc, đầu ra và điều kiện nghiệm thu của 9 phase trong 10 tuần.
- [Project Planning](docs/HMDA_New_York_Project_Planning.docx): căn cứ nghiên cứu, RQ, thiết kế thực nghiệm và yêu cầu học phần.
- [Chỉ mục tài liệu](docs/README.md): vai trò, trạng thái và nguồn sự thật của từng tài liệu.
- [Protocol](docs/protocol.md), [paper review](docs/paper_review.md) và [API contract](docs/api_contract.md): bản nháp nền đã đối chiếu; các mục phụ thuộc dữ liệu, công thức hoặc triển khai vẫn được đánh dấu `PENDING`.
- [Notebook guidelines](docs/notebook_guidelines.md) và [reproducibility](docs/reproducibility.md): chuẩn notebook, provenance và mức bằng chứng.
- [Contributing](CONTRIBUTING.md) và [Security](SECURITY.md): quy trình đóng góp, bảo vệ secret/dữ liệu và kiểm tra trước chia sẻ.

README là điểm bắt đầu cho thành viên nhóm; đặc tả chi tiết và gate được quản lý trong Project Master.

## Kiến trúc và luồng dữ liệu

PostgreSQL là nguồn dữ liệu dùng chung. Pipeline đọc dữ liệu, kiểm tra chất lượng và tạo snapshot có phiên bản; CSV nguồn và bản xuất được lưu local trong `data/`. Các thành phần tái sử dụng nằm trong package `src/hmda/`; notebook điều khiển phân tích/thực nghiệm và trình bày kết quả; API gọi package/service và nạp model đã lưu.

| Luồng | Trách nhiệm | Notebook |
| --- | --- | --- |
| EDADataPipeline | Dữ liệu gần raw để kiểm chất lượng và mô tả; không split, imputation, scaling hoặc encoding cho model | `notebooks/eda/` |
| TrainingDataPipeline | Kiểm dữ liệu, chia tập, phân tích train, lựa chọn preprocessing rồi train/đánh giá theo protocol | `notebooks/train/` |
| RegionDataPipeline | Kiểm dữ liệu vùng đối chiếu và dùng lại pipeline/model NY đã khóa; không fit lại | `notebooks/research/` |

**Preprocessing chưa được quyết định.** Chỉ lựa chọn sau phân tích và kiểm tra dữ liệu. Mọi phép biến đổi học từ dữ liệu phải fit trên train; validation, test, API và cross-region dùng lại trạng thái phù hợp đã lưu.

`path.py` đã tìm project root từ `__file__` và marker dự án, không dùng `cwd`. Config và logging lõi đã có kiểm tra/redaction; các quality gate, snapshot bất biến và đối soát PostgreSQL–CSV vẫn thuộc Phase 2.

## Cấu trúc dùng chung

| Vùng | Trách nhiệm |
| --- | --- |
| `src/hmda/core/` | Path, config, logging và exceptions |
| `src/hmda/data/`, `pipelines/` | Nạp dữ liệu, repository, validation, split, snapshot và ba pipeline |
| `src/hmda/preprocessing/`, `modeling/`, `evaluation/` | Xử lý sau khi được lựa chọn, huấn luyện và đánh giá |
| `src/hmda/explainability/`, `fairness/`, `visualization/` | Giải thích, audit và biểu đồ dùng chung |
| `src/hmda/services/` | Dự đoán và đọc kết quả cho API |
| `notebooks/` | EDA, train và research theo ba thư mục riêng |
| `configs/` | Toàn bộ tham số và mẫu môi trường không chứa secret |
| `data/raw/`, `data/snapshots/` | CSV nguồn và bản xuất EDA/training/region theo ID, lưu local |
| `artifacts/runs/`, `logs/` | Kết quả theo run và log runtime local |
| `sql/` | Migrations PostgreSQL và truy vấn quality |
| `api/`, `web/` | Dịch vụ và giao diện; frontend stack chưa chọn |
| `tests/` | 22 unit test Phase 1; integration/e2e nghiệp vụ vẫn là placeholder |
| `docs/` | Tài liệu chính và đặc tả theo phase |

Xem thêm [cấu hình](configs/README.md), [dữ liệu local](data/README.md), [artifacts](artifacts/README.md) và [kiểm tra](tests/README.md).

## Bắt đầu làm việc

1. Đọc Project Master và Planning để hiểu phạm vi và phase đang thực hiện.
2. Cài `uv` và dùng Python 3.13.9; tại project root chạy `uv sync --dev` để đồng bộ từ `uv.lock`.
3. Chạy `uv run pytest` và kiểm import bằng `uv run python -c "import hmda; print(hmda.__version__)"`.
4. Ở Phase 2, thiết lập quyền PostgreSQL, nguồn dữ liệu, quality checks và snapshot trước khi phân tích/train.

Hạ tầng Phase 1 gồm package `src` layout, root/path, config, logging/exceptions và các protocol component/pipeline độc lập dữ liệu. 11 notebook vẫn chỉ có Markdown và chưa có code/output; các module nghiệp vụ ngoài Phase 1 phần lớn còn là scaffold. Chưa có dữ liệu, snapshot, model hoặc kết quả nghiên cứu. Không dùng 22 unit test hạ tầng làm bằng chứng G2–G8.

Lệnh, phiên bản và bằng chứng kiểm thực tế nằm trong [reproducibility](docs/reproducibility.md). Deployment vẫn chưa được triển khai.

## Quy tắc đưa file lên Git

Nhóm dùng [workflow Git](docs/git/WORKFLOW.md), [mẫu commit](docs/git/COMMIT_TEMPLATE.txt) và [mẫu pull request](.github/pull_request_template.md). Workflow quy định branch, commit, review/merge, conflict và cách xem lịch sử; hồ sơ agent tham chiếu cùng tài liệu này.

Git quản lý code, notebook nguồn, test, SQL, cấu hình không bí mật, dependency lock và tài liệu dùng chung. `.gitignore` loại trừ:

- CSV ở mọi thư mục, kể cả `.CSV`, `.csv.gz` và bản sao `.csv.*`.
- Dữ liệu, model/artifact và log local; chỉ giữ README cùng marker `.gitkeep` trong các vùng này.
- Hồ sơ agent mặc định bị loại trừ, nhưng context kiến trúc, rules, session start, project state, guideline, decision, issue và research log của dự án được phép theo dõi để thành viên dùng chung. Task chi tiết, cấu hình trợ lý, `AGENTS.md`, `_archive/` và `.tmp/` vẫn local. Danh sách chính xác do `.gitignore` hiện hành quản lý; mọi file agent phải được rà soát trước chia sẻ.
- Nhật ký AI cá nhân trong `docs/ai_audit/`; chỉ chuẩn bị bản bàn giao đã rà soát khi đến phase liên quan.
- File môi trường thật, secret, credentials, khóa truy cập, cấu hình máy và tệp tạm. Mẫu `configs/local.env.example` được giữ vì không chứa giá trị bí mật.
- Tài liệu cá nhân đặt trong `personal/`, `private/`, `.private/` hoặc `local_only/`; các file mang hậu tố `.private.*` và `.personal.*` cũng được loại trừ.

`agent/PROJECT_MASTER_CONTEXT.md`, `agent/SESSION_START.md`, `agent/AGENT_RULES.md` và `agent/PROJECT_STATE.md` giúp thành viên/agent mới đọc kiến trúc, quy tắc và tiến độ mà không cần nạp toàn bộ DOCX. `AGENTS.md` và task chi tiết vẫn local; README này tiếp tục là điểm vào dùng chung cho người làm dự án.

`.gitignore` chỉ lọc theo đường dẫn/tên file, không phát hiện thông tin cá nhân hoặc secret bên trong README, DOCX, notebook hay mã nguồn. Trước commit, kiểm tra danh sách file và nội dung được stage; rà soát cả output/metadata của notebook. Không dùng `git add -f` để đưa các file đã chặn lên Git.

Nếu một file đã được Git theo dõi, thêm vào `.gitignore` không tự gỡ file hoặc xóa lịch sử. Khi gặp trường hợp đó cần xử lý riêng trước khi chia sẻ; credential đã lộ phải được thu hồi hoặc thay mới.

## Lộ trình

Phase 0 chốt phạm vi và tổ chức công việc → Phase 1 hạ tầng → Phase 2 dữ liệu/quality → Phase 3 EDA → Phase 4 training và RQ1 → Phase 5 GSV/SL → Phase 6 fairness/region → Phase 7 Web API → Phase 8 tái lập và bàn giao.

Tổng thời lượng dự kiến là 10 tuần, có phụ thuộc và phần chuẩn bị song song theo Master. Mỗi phase chỉ được nghiệm thu khi có bằng chứng đúng phạm vi; báo cáo và slide cuối học phần được tạo từ kết quả thực tế.
