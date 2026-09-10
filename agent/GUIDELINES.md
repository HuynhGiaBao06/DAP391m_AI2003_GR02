# Hướng dẫn thực hiện công việc

Đọc [SESSION_START](SESSION_START.md) để vào phiên và [AGENT_RULES](AGENT_RULES.md) để xác định giới hạn. File này mô tả cách làm; trạng thái mới nhất nằm ở [PROJECT_STATE](PROJECT_STATE.md).

## Một nguồn cho mỗi loại thông tin

| Thông tin | Nơi lưu |
| --- | --- |
| Kiến trúc, phase, đầu ra và gate | [PROJECT_MASTER_CONTEXT](PROJECT_MASTER_CONTEXT.md) để đọc nhanh; DOCX nguồn chỉ mở theo điều kiện trong context |
| Căn cứ nghiên cứu và RQ | Project Planning trong docs/ |
| Điểm dừng, việc đang làm và bước tiếp theo | PROJECT_STATE.md |
| Phạm vi, quyền đã giao, công việc và kiểm tra | tasks/TASK-xxx.md; INDEX chỉ tóm tắt |
| Vấn đề, ảnh hưởng, owner và điều kiện đóng | ISSUES.md |
| Quyết định và lý do, hoặc đề xuất đang chờ | DECISIONS.md |
| Phát hiện, nguồn, kết luận và giới hạn | RESEARCH_LOG.md |
| Tham số thực thi | configs/; không chép lại giá trị vào rules/task |
| Số liệu và log chi tiết | artifacts/runs/<run_id>/ và logs/ khi có run thật |

## 1 Chuẩn bị một task

Dùng [TEMPLATE](tasks/TEMPLATE.md). Đọc yêu cầu → xác định đầu vào/file → ghi phạm vi và thao tác được giao → đặt tiêu chí kiểm tra → thực hiện. Task phải đủ nhỏ để có một đầu ra rõ; tách khi có đích ghi, owner hoặc nghiệm thu độc lập.

Trong task ghi owner/reviewer thực nếu đã phân công; nếu chưa có thì ghi vai trò dự kiến và “chưa phân công”. Không giao tên giả. Dependency dẫn đến task/gate thật, không dùng mã chưa tồn tại.

BACKLOG → READY khi đầu vào/phụ thuộc đã đủ → IN_PROGRESS khi thực sự bắt đầu trong quyền được giao → REVIEW nếu cần đối chiếu/reviewer → DONE sau đạt tiêu chí. BLOCKED chỉ dùng khi task đang cần tiếp tục nhưng bị một điều kiện cụ thể chặn; ghi cách tháo gỡ. Một task chưa đến lượt vẫn là BACKLOG. Có thể chuyển lại IN_PROGRESS khi phát hiện việc cần sửa và ghi lý do.

Nếu công việc trước đó đã có task phù hợp, cập nhật task đó thay vì tạo bản trùng. Task cha chỉ đóng khi tất cả đầu ra của nó đạt, kể cả quyết định cần nhóm xác nhận.

## 2 Môi trường và lệnh chạy

Hiện chưa có runtime dự án được khóa hoặc lệnh chạy pipeline/API đã kiểm chứng. Không chạy lệnh huấn luyện dự đoán từ tên file khung. Xem state để biết điều kiện còn thiếu.

Khi triển khai Phase 1, ghi phiên bản Python, môi trường, dependency lock, cách cài package, kernel notebook và kiểm import từ ngoài project root. Runtime của công cụ tạo tài liệu không tự là môi trường chuẩn của dự án. Không sửa sys.path để che lỗi cài package.

Quy tắc branch, commit, template, PR, review/merge, conflict và lệnh kiểm Git được quản lý tại [docs/git/WORKFLOW.md](../docs/git/WORKFLOW.md). Agent dùng cùng workflow với nhóm; không duy trì bộ quy tắc Git riêng trong hồ sơ local.

Lệnh Git chạy trong checkout; path.py của ứng dụng vẫn phải độc lập cwd. Khi ghi lệnh mới vào task, đánh dấu ĐÃ KIỂM hoặc CHƯA KIỂM cùng môi trường và kết quả; không ghi secret vào command/log. Việc có hướng dẫn commit/push không cấp quyền thực hiện nếu người dùng chỉ yêu cầu sửa file.

## 3 Viết code và notebook

Kiểm hợp đồng input/output trước khi viết. Sửa ít file nhất cần cho task; dùng package chung cho phần tái sử dụng và giữ config tách code. Chọn kiểm tra theo rủi ro thực: đường dẫn/config, lỗi dữ liệu, split leakage, serialization hoặc API parity ở đúng phase.

Notebook đi theo nguồn/cấu hình → đọc dữ liệu → kiểm tra → phân tích/thực nghiệm → bảng/biểu đồ → kết luận. Ghi snapshot/run/version khi có thật. Không nhúng logic dùng chung dài vào từng notebook và không thay config bằng biến hard-code rải rác.

Chỉ chạy khi nằm trong yêu cầu đã giao và có đầu vào/môi trường đủ điều kiện. Chạy lại từ kernel sạch khi task yêu cầu tái lập; lưu lỗi, thời điểm và phạm vi. Saved output dùng để review phải được gọi đúng là output đã lưu. Không suy số liệu từ notebook còn trống.

## 4 Dữ liệu, quality và DB

Trước nạp/chạy, xác định nguồn, đích, snapshot và quyền DB trong task; không đưa mật khẩu vào hồ sơ. Đối soát đúng tầng raw/processed. ERROR chặn publish/bước phụ thuộc; WARNING cần mô tả và xử lý theo protocol, không tự biến thành lỗi chặn hoặc bỏ qua âm thầm.

Khi có run, giữ bằng chứng nguồn/schema/config, số dòng và kết quả kiểm tra. Không sửa raw/snapshot cũ; output mới phải có danh tính riêng. Khi thao tác bị ngắt, đọc trạng thái DB/manifest trước retry. Transaction DB không bao phủ CSV trên filesystem; kiểm cả trạng thái export.

Đối với thử nghiệm nhỏ, có thể dùng fixture tổng hợp được ghi rõ là dữ liệu kiểm thử; không đưa fixture vào data/raw hoặc mô tả nó là dữ liệu nghiên cứu thật.

## 5 Phân tích và quyết định

Đọc paper/nguồn, ghi trích dẫn và phạm vi được nguồn hỗ trợ. Phân biệt giả thuyết, phát hiện mô tả, kiểm chứng phương pháp và kết luận thực nghiệm. Không dùng tương quan, ranking agreement hoặc fairness gap để khẳng định nhân quả.

Ghi kết quả trong RESEARCH_LOG, quyết định trong DECISIONS, vấn đề cần xử lý trong ISSUES; liên kết nhau thay vì sao chép số liệu. Preprocessing vẫn để trống cho đến khi có phân tích và kiểm tra thực. Không chốt một ngưỡng hoặc mặc định từ tài liệu vận hành này.

## 6 Kiểm tra và đóng phiên

Đối chiếu file thay đổi với phạm vi ban đầu; kiểm link/cấu trúc với tài liệu, kiểm runtime với phần triển khai cần chạy. Test thành công không chứng minh các phần chưa được kiểm. File DOCX đã sửa phải kết xuất và kiểm hình ảnh trang trước khi gọi là đã kiểm hiển thị.

Ghi vào task: kiểm tra nào, bằng công cụ/môi trường nào, kết quả, đường dẫn evidence và phần chưa chạy. Với output thực nghiệm, thêm ID và version cần để tìm lại; không tạo mã giả cho tác vụ chỉ sửa tài liệu.

Cập nhật task → issue/decision/research nếu có thay đổi → INDEX → PROJECT_STATE. Final gửi người dùng gồm kết quả, file chính, kiểm tra và giới hạn còn ảnh hưởng. Nếu bị chặn, nêu đúng bước và điều kiện tiếp tục; không ghi toàn bộ phase DONE.

## 7 Làm việc nhiều thành viên

Kiểm thay đổi đang có trước khi sửa. Tách file/module khi chạy đồng thời; phối hợp thay đổi hợp đồng dùng chung trước khi ghi. Không reset/revert thay đổi không thuộc task.

Project Master context, rules, session start, project state, guidelines, decisions, issues và research log được phép theo dõi để thành viên đồng bộ kiến trúc, cách làm và tiến độ. Task chi tiết, `AGENTS.md` và cấu hình trợ lý vẫn local. Không đặt secret hoặc dữ liệu cá nhân trong hồ sơ được chia sẻ; link tới task/evidence local không thay bằng chứng dùng chung cho PR.

Khi cần dùng lại kết luận cho nhóm, đưa bản đã rà soát vào tài liệu dự án trong phạm vi người dùng giao. Trước chuyển giao snapshot/artifact, dùng manifest và version; không coi trạng thái Markdown là khóa DB hay cơ chế chia sẻ dữ liệu.
