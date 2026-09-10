# Quy trình Git của nhóm HMDA

Quy tắc dùng chung cho thành viên và agent: mỗi thay đổi có phạm vi rõ, kiểm tra phù hợp và được review trước khi đưa vào nhánh chính. File này là nguồn quy tắc Git; hồ sơ agent tham chiếu thay vì duy trì bản riêng.

## 1 Nhánh làm việc

`main` là nhánh tích hợp. Dùng nhánh công việc ngắn hạn cho từng thay đổi, mở pull request (PR) vào `main`; không cần thêm nhánh `develop` ở giai đoạn này.

- Thành viên dùng `feature/<mo-ta>`, `fix/<mo-ta>`, `docs/<mo-ta>` hoặc `chore/<mo-ta>`; tên ngắn, không chứa thông tin cá nhân.
- Agent tạo nhánh mới với tiền tố `codex/`, trừ khi người dùng chỉ định tên khác. Nếu đã được giao làm trên một nhánh hiện có, tiếp tục đúng nhánh đó.
- Một nhánh/PR giải quyết một đầu ra có thể review. Không gộp sửa tài liệu với thay đổi model hoặc dữ liệu không liên quan.
- Không push trực tiếp vào `main`, force-push nhánh chung hoặc viết lại lịch sử của người khác trong luồng thông thường.

Đây là quy trình của nhóm, chưa phải bằng chứng đã cấu hình branch protection hoặc bắt buộc review trên GitHub. Những thiết lập phía GitHub cần được cấu hình riêng khi nhóm giao thực hiện.

## 2 Bắt đầu và cập nhật nhánh

Đọc yêu cầu/issue dùng chung, xác định file và kiểm thay đổi đang có:

```shell
git status --short
git branch --show-current
git diff --stat
```

Giữ lại công việc đang dở trước khi chuyển nhánh; không reset hoặc stash thay đổi của người khác để làm sạch workspace. Khi được giao đồng bộ remote, dùng `git fetch origin`, kiểm nhánh đích và tạo nhánh công việc từ bản `origin/main` đã cập nhật. Không đổi tên hoặc tạo lại nhánh chỉ vì khác ví dụ trong tài liệu.

Nếu nhánh công việc cần cập nhật `main`, ưu tiên merge `origin/main` vào nhánh đó sau khi workspace sạch. Rebase chỉ dùng cho các commit riêng chưa chia sẻ hoặc khi nhóm đã thống nhất, không áp dụng lên lịch sử người khác đang dùng.

## 3 File được đưa lên Git

`.gitignore` là nguồn quy tắc loại trừ. Giữ code, notebook nguồn, SQL migration, test, dependency lock, cấu hình không bí mật và tài liệu dùng chung. CSV, dữ liệu/artifact/log local, secret, archive và hồ sơ cá nhân phải theo quy tắc loại trừ hiện hành.

Các tài liệu agent dùng chung được phép theo dõi gồm Project Master context, rules, session start, project state, guidelines, decisions, issues và research log theo `.gitignore` hiện hành. Chúng giúp thành viên thống nhất kiến trúc, cách làm và tiến độ, nhưng không được chứa secret/thông tin cá nhân. `AGENTS.md`, task chi tiết và cấu hình trợ lý vẫn local. Không đưa link đến task hoặc evidence chỉ có trên máy cá nhân vào PR làm bằng chứng duy nhất.

Trước stage, kiểm notebook output/metadata, DOCX và mẫu config; `.gitignore` không quét nội dung nhạy cảm. Giữ output phân tích chỉ khi cần review, có nguồn và đã rà soát; không chạy/xóa output hàng loạt chỉ để làm đẹp diff. Model và số liệu chi tiết nằm trong kho artifact theo quyền nhóm, PR dẫn version/bằng chứng đã được phép chia sẻ.

Nếu nghi một file bị loại trừ đã được theo dõi:

```shell
git ls-files -ci --exclude-standard
git check-ignore -v --no-index <duong-dan>
```

Với file đã xác nhận chỉ cần giữ local, `git rm --cached -- <duong-dan>` gỡ khỏi index nhưng giữ bản trên đĩa; thao tác này tạo thay đổi cần review/commit và không xóa file khỏi lịch sử cũ. Không dùng `git add -f` để vượt quy tắc. Credential đã lộ cần được thu hồi/thay mới, không chỉ thêm ignore.

## 4 Commit

Một commit thể hiện một thay đổi có mục đích rõ. Tiêu đề theo dạng `type(scope): mô tả`, dùng `feat`, `fix`, `docs`, `refactor`, `test` hoặc `chore`; scope ngắn như `data`, `model`, `api`, `git`. Mô tả bằng tiếng Việt hoặc tiếng Anh nhất quán trong commit, tránh “update files” không nói thay đổi gì.

Ví dụ tiêu đề: `docs(git): bổ sung workflow và mẫu pull request`.

Stage các đường dẫn cụ thể thuộc công việc, rồi kiểm nội dung sẽ commit:

```shell
git add -- <file-1> <file-2>
git diff --cached --name-status
git diff --cached
git diff --cached --check
```

Các ký hiệu `<...>` là chỗ thay bằng giá trị thật, không chạy nguyên văn. `git diff --check` chỉ kiểm whitespace; không thay test hoặc rà soát thông tin cá nhân.

### Dùng mẫu commit

[COMMIT_TEMPLATE.txt](COMMIT_TEMPLATE.txt) gồm gợi ý được comment bằng `#`. Khi đã được giao commit và đã kiểm staged diff, mở editor với mẫu:

Chạy lệnh dưới đây từ root của checkout để đường dẫn template được giải đúng.

```shell
git -c core.commentChar="#" commit --cleanup=strip --template=docs/git/COMMIT_TEMPLATE.txt
```

Viết tiêu đề và nội dung thật ở các dòng không có `#`; chỉ giữ phần cần thiết với thay đổi. Toàn bộ dòng gợi ý được bỏ khi tạo message. Không dùng `-m` nếu muốn mở editor với template. Mẫu chỉ có comment để không vô tình commit nguyên khung chưa điền.

Lệnh dùng mẫu trực tiếp, không sửa cấu hình global/local. Những lệnh làm thay đổi index/branch/commit trong hướng dẫn chưa được thực thi chỉ vì tài liệu này được tạo; thực hiện khi đúng phạm vi được giao.

## 5 Pull request và review

Khi được giao chia sẻ thay đổi, push nhánh công việc rồi mở PR vào `main`, điền [mẫu PR](../../.github/pull_request_template.md). GitHub tự dùng mẫu sau khi file có trên nhánh mặc định; chỉ có file ở nhánh công việc chưa bảo đảm UI đã áp dụng.

PR cần nêu vấn đề và hành vi sau thay đổi, cách kiểm tra, ảnh hưởng và giới hạn còn lại. Với Data Science, ghi phiên bản config/code và ID snapshot/model thật nếu có; không bịa run hoặc số liệu cho PR tài liệu. Evidence phải truy cập được bởi reviewer và không chứa secret/dữ liệu cá nhân.

Ít nhất một thành viên khác review nội dung trước merge. Reviewer kiểm đúng phạm vi, dữ liệu/nhãn/leakage khi liên quan, tương thích API/schema, test và khả năng tái lập. Với PR tài liệu, kiểm link, trạng thái và nội dung; với thay đổi DOCX, kiểm bản kết xuất trực quan. Không bắt buộc chạy model cho PR chỉ sửa tài liệu.

Người có quyền merge xử lý sau khi review đạt, các nhận xét cần sửa đã giải quyết và kiểm tra liên quan đạt. Nhóm dùng squash merge làm mặc định để mỗi PR thành một commit rõ; nếu cần giữ lịch sử nhiều commit có ý nghĩa, ghi lý do trong PR. Sau merge, chỉ xóa nhánh khi đã xác nhận không còn công việc chưa tích hợp.

## 6 Conflict và hoàn tác

Khi conflict, đọc cả hai thay đổi và trao đổi với người phụ trách file. Không chọn toàn bộ “ours/theirs” nếu chưa hiểu phần bị mất.

- Code/config: giải quyết theo hợp đồng hiện hành, kiểm lại phần bị ảnh hưởng.
- Notebook: không ghép JSON mù quáng; kiểm cell ID, thứ tự code/output và tính nhất quán sau hợp nhất. Chạy lại chỉ khi được giao và có môi trường/dữ liệu phù hợp.
- DOCX/PPTX: điều phối một người sửa bản chuẩn hoặc hợp nhất nội dung có chủ đích, rồi kết xuất và kiểm hình ảnh.

Nếu chưa thể giải quyết merge đang diễn ra, bảo toàn phần cần giữ rồi dùng `git merge --abort` để trở về trước merge; lệnh không thay việc sao lưu công việc đang dở. Với thay đổi đã chia sẻ cần hoàn tác, ưu tiên `git revert <commit>` qua nhánh/PR mới. Không reset/clean hàng loạt hoặc viết lại lịch sử như cách xử lý mặc định.

## 7 Xem lịch sử

Git đã lưu lịch sử commit, không tạo `GIT_LOG.md` để chép lại:

```shell
git log --oneline --decorate --graph -15
git log --oneline -- docs/git/WORKFLOW.md
git show --stat <commit>
```

Commit chưa có trong lịch sử thì không ghi như đã phát hành. Khi dự án có release, có thể bổ sung `CHANGELOG.md` để tóm tắt thay đổi đáng chú ý theo phiên bản; chưa tạo changelog rỗng ở bước này.

## Tham chiếu cơ chế

[Git commit và template](https://git-scm.com/docs/git-commit), [gỡ file khỏi index](https://git-scm.com/docs/git-rm), [Git log](https://git-scm.com/docs/git-log), [GitHub PR template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository).
