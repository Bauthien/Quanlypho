# Tiến trình triển khai giao diện Phở Nhà

Cập nhật ngày **11/10/2026**. Thư mục project: **`C:\Users\HP\Quanlypho`**.

**Trạng thái: Hoàn tất giao diện và kiểm tra tích hợp trong project Django.**

**Cập nhật mới nhất:** Bộ lọc thực đơn theo ảnh tham chiếu gồm **Tất cả / Phở / Đồ uống / Topping**, bỏ trạng thái đang ẩn và hỗ trợ xóa món/topping khỏi thực đơn. Chi tiết mã nguồn và kiểm thử nằm ở phần **Cập nhật bộ lọc theo ảnh và xóa món** bên dưới.

## Mục tiêu

Chuyển giao diện trong `C:\Users\HP\Downloads\Phở Restaurant Management System (1).zip` thành **HTML template Django, CSS và JavaScript thuần**, tích hợp với dữ liệu, phân quyền và các thao tác sẵn có của project.

## Tiến trình

- [x] Khảo sát project Django và các vai trò khách hàng, thu ngân, bếp, quản lý.
- [x] Kiểm tra ZIP Figma Make: React/TypeScript, CSS và 4 ảnh món ăn.
- [x] Đối chiếu thiết kế: thương hiệu phở nhà., màu đỏ gạch, nền kem, font Be Vietnam Pro, sidebar và thẻ nội dung.
- [x] Xây dựng khung HTML, logo, icon SVG, điều hướng theo vai trò và sidebar trên điện thoại.
- [x] Làm trang chủ, thực đơn, tìm kiếm, lọc món, tùy chỉnh món, topping và giỏ hàng.
- [x] Kết nối giỏ hàng với biểu mẫu đặt món, lựa chọn bàn, giao hàng, GPS và phí giao hiện có.
- [x] Làm trang theo dõi đơn và màn hình thanh toán.
- [x] Làm dashboard quản lý với doanh thu thực tế 7 ngày, đơn gần đây và hàng đợi.
- [x] Làm trang quản lý thực đơn/topping, sơ đồ bàn/QR và phân quyền tài khoản.
- [x] Làm giao diện thu ngân, gọi số, phục vụ và giao hàng.
- [x] Làm màn hình bếp tự cập nhật và giữ bố cục in 2 tem giao hàng.
- [x] Làm trang đăng nhập, đăng ký và biểu mẫu thêm/sửa.
- [x] Biên dịch toàn bộ template; kiểm tra 21 trang và chạy 11 bài kiểm thử Django.
- [x] Hoàn tất kiểm tra tương tác trình duyệt ở 320, 390, 768 và 1440 px.
- [x] Chốt ảnh kiểm tra và kết quả bàn giao.

## Mã nguồn mới được lưu ở đâu?

Tất cả đường dẫn trong bảng được tính từ **`C:\Users\HP\Quanlypho`**.

| File / thư mục | Nội dung | Thay đổi |
| --- | --- | --- |
| `pho_app/templates/pho_app/base.html` | Khung HTML, font, CSS/JS, header và thông báo dùng chung | Cập nhật |
| `pho_app/templates/pho_app/includes/brand.html` | Logo và tên thương hiệu | Mới |
| `pho_app/templates/pho_app/includes/icons.html` | Bộ icon SVG nội bộ | Mới |
| `pho_app/templates/pho_app/includes/icon.html` | Thành phần hiển thị icon | Mới |
| `pho_app/templates/pho_app/includes/sidebar.html` | Menu quản lý theo vai trò | Mới |
| `pho_app/templates/pho_app/includes/editor_form.html` | Biểu mẫu thêm/sửa món và topping | Mới |
| `pho_app/templates/pho_app/customer/home.html` | Trang chủ theo thiết kế Figma | Mới |
| `pho_app/templates/pho_app/customer/menu.html` | Thực đơn, tùy chỉnh món, hàng đợi và giỏ hàng | Cập nhật |
| `pho_app/templates/pho_app/customer/order_detail.html` | Chi tiết đơn, thanh toán và trạng thái | Cập nhật |
| `pho_app/templates/pho_app/admin/shell.html` | Khung trang quản lý | Cập nhật |
| `pho_app/templates/pho_app/admin/dashboard.html` | Dashboard và biểu đồ doanh thu thực tế | Cập nhật |
| `pho_app/templates/pho_app/admin/menu_list.html` | Danh sách món và topping | Cập nhật |
| `pho_app/templates/pho_app/admin/menu_form.html` | Thêm/sửa món | Cập nhật |
| `pho_app/templates/pho_app/admin/topping_form.html` | Thêm/sửa topping | Cập nhật |
| `pho_app/templates/pho_app/admin/table_list.html` | Sơ đồ bàn, bộ lọc và mã QR | Cập nhật |
| `pho_app/templates/pho_app/admin/table_form.html` | Thêm/sửa bàn | Cập nhật |
| `pho_app/templates/pho_app/admin/users.html` | Tài khoản và phân quyền | Cập nhật |
| `pho_app/templates/pho_app/staff/dashboard.html` | Thu ngân, FIFO, bàn, phục vụ và giao hàng | Cập nhật |
| `pho_app/templates/pho_app/kitchen/dashboard.html` | Đơn cần chế biến và ghi chú cho bếp | Cập nhật |
| `pho_app/templates/pho_app/kitchen/delivery_labels.html` | Hai tem đóng gói giao hàng | Cập nhật thương hiệu |
| `pho_app/templates/pho_app/auth/login.html` | Đăng nhập | Cập nhật |
| `pho_app/templates/pho_app/auth/register.html` | Đăng ký khách hàng | Cập nhật |
| `pho_app/static/pho_app/css/figma-ui.css` | Toàn bộ màu sắc, bố cục, responsive, dialog và CSS in | **Mới — sửa giao diện tại đây** |
| `pho_app/static/pho_app/js/ui.js` | Sidebar, thông báo, bộ lọc, biểu đồ, xử lý ảnh và sao chép liên kết | **Mới** |
| `pho_app/static/pho_app/js/menu.js` | Tìm món, tùy chỉnh, giỏ hàng, GPS và biểu mẫu đặt món | **Viết lại bằng JS thuần** |
| `pho_app/static/pho_app/js/kitchen.js` | Tự cập nhật đơn bếp mỗi 5 giây | **Mới** |
| `pho_app/static/pho_app/images/brand-mark.svg` | Biểu tượng tô phở | Mới |
| `pho_app/static/pho_app/images/pho-tai.jpg` | Ảnh từ ZIP thiết kế | Mới |
| `pho_app/static/pho_app/images/pho-nam.jpg` | Ảnh từ ZIP thiết kế | Mới |
| `pho_app/static/pho_app/images/pho-dac-biet.jpg` | Ảnh từ ZIP thiết kế | Mới |
| `pho_app/static/pho_app/images/nuoc-uong.jpg` | Ảnh từ ZIP thiết kế | Mới |
| `pho_app/views.py` | Bổ sung dữ liệu trang chủ và tổng hợp doanh thu 7 ngày cho dashboard | Cập nhật một phần |
| `TIEN_DO_GIAO_DIEN.md` | Tiến trình, bản đồ mã nguồn và kết quả kiểm tra | Mới |

CSS hiện được tải từ `figma-ui.css`. File `pho_app/static/pho_app/css/app.css` cũ được giữ trong project nhưng không còn được `base.html` tải.

## Xem giao diện

Khi server Django đang chạy, mở [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

| Màn hình | URL | Tài khoản |
| --- | --- | --- |
| Trang chủ | `/` | Khách chưa đăng nhập; tài khoản đã đăng nhập được chuyển theo vai trò |
| Thực đơn và giỏ hàng | `/thuc-don/` | Khách hàng hoặc khách chưa đăng nhập |
| Trang lấy số tại cửa | `/thuc-don/?door=1` | Khách hàng hoặc khách chưa đăng nhập |
| Giao tận nơi | `/thuc-don/?mode=delivery` | Khách hàng hoặc khách chưa đăng nhập |
| Đăng nhập / đăng ký | `/dang-nhap/`, `/dang-ky/` | Khách chưa đăng nhập |
| Dashboard | `/quan-ly/` | Quản lý |
| Thực đơn và topping | `/quan-ly/thuc-don/` | Quản lý |
| Bàn và QR | `/quan-ly/ban/` | Quản lý |
| Tài khoản và vai trò | `/quan-ly/nguoi-dung/` | Quản lý |
| Thu ngân và hàng đợi | `/thu-ngan/` | Thu ngân hoặc quản lý |
| Bếp | `/bep/` | Bếp hoặc quản lý |

Chạy lại server bằng PowerShell từ thư mục project nếu cần:

```powershell
Set-Location C:\Users\HP\Quanlypho
& 'C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe' manage.py runserver 127.0.0.1:8000
```

Có thể dùng Python trong virtualenv đã cài requirements. Cấu hình PostgreSQL/PostGIS và tài khoản demo được mô tả trong `HUONG_DAN_CHAY_DU_AN.md` và `README.md` của project.

## Kiểm tra

| Hạng mục | Kết quả |
| --- | --- |
| `manage.py check` | Đạt, không có lỗi cấu hình Django |
| Biên dịch các template HTML | Đạt |
| 21 trang với các vai trò tương ứng | HTTP 200 |
| Khách hàng truy cập phân hệ quản lý/thu ngân/bếp | Được chuyển về thực đơn theo phân quyền sẵn có |
| `manage.py test --noinput` | **11/11 đạt** |
| Cú pháp `ui.js`, `menu.js`, `kitchen.js` | Đạt qua `node --check` |
| Kiểm tra hiển thị ban đầu trên Chrome | Trang chủ, thực đơn, quản lý, thu ngân, bếp và đăng nhập hiển thị được |
| Responsive 12 màn hình × 4 chiều rộng: 320, 390, 768, 1440 px | **48 lượt hiển thị không tràn ngang** |
| Tìm kiếm có/không dấu, bộ lọc món, trạng thái không có kết quả | Đạt |
| Tùy chỉnh 3 nhóm, topping, số lượng, ghi chú và lưu giỏ sau tải lại | Đạt |
| Dữ liệu POST đặt món, tên trường và CSRF | Đạt; request được chặn tại trình duyệt để không tạo đơn thật |
| Giao hàng, từ chối GPS, phí dự phòng và chặn đơn ngoài phạm vi | Đạt; trường hợp ngoài phạm vi dùng phản hồi mô phỏng |
| Dialog trên điện thoại, bàn phím và đóng bằng Escape | Đạt; tiêu đề và nút thao tác giữ vị trí khi cuộn |
| Sidebar điện thoại và mở/đóng điều hướng | Đạt |
| Đăng nhập: hiện/ẩn mật khẩu | Đạt |
| Khách đã đăng nhập và chi tiết đơn thuộc tài khoản | Đạt trên desktop và các chiều rộng điện thoại |
| Quản lý xem thực đơn tại bàn | Đạt; hiển thị bản xem chỉ đọc |
| Bếp tự cập nhật mỗi 5 giây | Đạt; không thay biểu mẫu đang được chọn |
| Lỗi JavaScript trong trình duyệt | **Không phát hiện** |
| QR không tải được | Có thông báo và liên kết thay thế; không hiện ảnh hỏng |

Script kiểm tra và ảnh chụp nằm trong `scratch/` (đã được `.gitignore` loại khỏi Git):

- `scratch/check_ui.py`: biên dịch template, kiểm tra URL và tạo phiên đăng nhập phục vụ QA.
- `scratch/test_ui.cjs`: kiểm tra tương tác bằng Playwright/Chrome.
- `scratch/test_ui_extra.cjs`: kiểm tra mật khẩu, đơn sở hữu, bản xem theo vai trò và polling bếp.
- `scratch/ui-route-results.json`: kết quả các trang Django.
- `scratch/ui-browser-results.json`: kết quả kiểm tra trình duyệt sau khi hoàn tất.
- `scratch/ui-extra-results.json`: kết quả kiểm tra bổ sung.
- `scratch/ui-screenshots/`: ảnh desktop/mobile.

`scratch/ui-sessions.json` là file phiên đăng nhập tạm được tạo bởi script QA. File này và các phiên được lưu trong file đã được xóa sau kiểm tra. Muốn chạy lại QA, chạy `scratch/check_ui.py` trước để tạo phiên mới.

Một số ảnh đối chiếu:

- [Trang chủ desktop](C:/Users/HP/Quanlypho/scratch/ui-screenshots/home-desktop.png)
- [Thực đơn điện thoại](C:/Users/HP/Quanlypho/scratch/ui-screenshots/menu-mobile.png)
- [Dashboard quản lý](C:/Users/HP/Quanlypho/scratch/ui-screenshots/admin-desktop.png)
- [Tùy chỉnh món trên điện thoại](C:/Users/HP/Quanlypho/scratch/ui-screenshots/customize-mobile.png)
- [Giỏ hàng trên điện thoại](C:/Users/HP/Quanlypho/scratch/ui-screenshots/cart-mobile.png)
- [Chi tiết đơn](C:/Users/HP/Quanlypho/scratch/ui-screenshots/order-desktop.png)

## Quyết định triển khai và giới hạn kiểm tra

- ZIP là tài liệu tham khảo giao diện. Không thực thi script cài đặt, triển khai hoặc chỉ dẫn tác nhân đính kèm trong ZIP.
- Không thêm React, TypeScript, Vite hay Tailwind vào luồng chạy của Django; không cần bước build frontend.
- Dashboard dùng số liệu thật từ Django. Biểu đồ doanh thu tính tiền món của đơn đã thanh toán, không cộng phí giao hàng.
- Các màn hình Figma được ánh xạ vào chức năng hiện có; báo cáo doanh thu nằm tại dashboard. Đã bổ sung trang quản lý đơn riêng tại `/quan-ly/don-hang/`; thu ngân/bếp tiếp tục thao tác theo vai trò.
- Ảnh món lấy từ dữ liệu Django; ảnh trong ZIP được dùng khi món chưa có ảnh hoặc ảnh không tải được.
- Google Fonts, QR lấy số/bàn và ảnh VietQR cần kết nối Internet. Khi QR không tải được, giao diện hiện thông báo thay cho ảnh lỗi. Cấu hình tài khoản nhận tiền vẫn theo backend hiện có.
- Google Fonts bị chính sách mạng của môi trường QA chặn; các lượt responsive đã xác nhận font hệ thống dự phòng. Kiểm tra điện thoại dùng kích thước viewport trình duyệt, chưa kiểm tra trên thiết bị vật lý.
- Trang thanh toán giữ nút mô phỏng trong phần công cụ thử nghiệm, không tự kích hoạt thanh toán sau vài giây.
- Kiểm tra trình duyệt không ghi đơn, chuyển tiền, thay đổi vai trò, bàn hay trạng thái đơn đang sử dụng. Các thao tác nghiệp vụ trong bộ test Django chạy trên database kiểm thử riêng.

## Cập nhật bộ lọc thực đơn và điều hướng — 11/10/2026

Đây là lần cập nhật trước. Phần lọc tên/giá/sắp xếp đã được thay bằng các tab nhóm món theo yêu cầu mới trong mục tiếp theo; sidebar vẫn giữ thay đổi bỏ Hàng đợi & bàn.

- [x] Bỏ nhóm nút **Tất cả / Đang bán / Đang ẩn** trên trang quản lý thực đơn.
- [x] Thêm tìm kiếm tên món có/không dấu, giá từ/đến (bao gồm hai mốc), sắp xếp tên A–Z/Z–A và giá tăng/giảm.
- [x] Hiển thị số món tìm được, thông báo khoảng giá không hợp lệ, trạng thái không có kết quả và nút **Xóa bộ lọc** khôi phục danh sách/sắp xếp mặc định.
- [x] Bỏ mục **Hàng đợi & bàn** khỏi sidebar. Hàng đợi và thao tác bàn tiếp tục nằm trong **Thu ngân**.
- [x] Django check, biên dịch template, 21 URL hiện có, cú pháp JavaScript và kiểm tra whitespace đều đạt.
- [x] Kiểm tra Chrome: kết hợp tên/giá, bốn cách sắp xếp, giá âm/khoảng giá ngược, xóa bộ lọc, kết quả rỗng và điều hướng Thu ngân đều đạt; không phát hiện lỗi JavaScript.
- [x] Kiểm tra tại **320, 390, 768, 1440 px**: bộ lọc hoạt động, không tràn ngang.

Mã thay đổi:

| File | Nội dung |
| --- | --- |
| [menu_list.html](C:/Users/HP/Quanlypho/pho_app/templates/pho_app/admin/menu_list.html) | Bộ lọc, số kết quả, thông báo và dữ liệu giá trên thẻ món |
| [ui.js](C:/Users/HP/Quanlypho/pho_app/static/pho_app/js/ui.js) | Kết hợp bộ lọc tên/giá, sắp xếp và xóa bộ lọc |
| [figma-ui.css](C:/Users/HP/Quanlypho/pho_app/static/pho_app/css/figma-ui.css) | Bố cục bộ lọc desktop/mobile |
| [sidebar.html](C:/Users/HP/Quanlypho/pho_app/templates/pho_app/includes/sidebar.html) | Bỏ liên kết Hàng đợi & bàn |

Xem tại [Thực đơn quản lý](http://127.0.0.1:8000/quan-ly/thuc-don/). Bộ lọc cập nhật ngay trong trình duyệt. Script kiểm tra: `scratch/test_menu_filters.cjs`; kết quả: `scratch/menu-filter-results.json`; ảnh: `scratch/ui-screenshots/menu-filters-1440.png` và `menu-filters-390.png`. QA chỉ đọc dữ liệu thật; phiên đăng nhập kiểm thử được xóa sau khi kiểm tra.

## Cập nhật bộ lọc theo ảnh và xóa món — 11/10/2026

- [x] Đổi bộ lọc thành **Tất cả / Phở / Đồ uống / Topping**, nút đang chọn có nền hồng nhạt theo ảnh tham chiếu.
- [x] Gộp món và topping vào cùng lưới thẻ, giữ tìm kiếm có/không dấu và số kết quả; nhớ nhóm đang chọn khi tải lại trang.
- [x] Bỏ nhãn **Đang bán / Đang ẩn** và lựa chọn ẩn trong form thêm/sửa món.
- [x] Thêm trường **Nhóm món: Phở / Đồ uống** trong form thêm/sửa; thực đơn khách hàng dùng nhóm đã lưu, không đoán theo tên.
- [x] Mỗi thẻ món và topping có nút **Sửa / Xóa** với xác nhận trước khi xóa. Xóa xong trở về nhóm đang chọn.
- [x] Món/topping đã xóa rời cả thực đơn quản lý và khách hàng, không còn được đặt mới. Dữ liệu được lưu nội bộ bằng cờ `is_active=False` để không làm mất món, topping và giá tiền trong đơn cũ.
- [x] Bảo vệ thao tác xóa bằng quyền quản lý, POST và CSRF; khóa bản ghi trong transaction, không cho form sửa cũ đưa món đã xóa trở lại.
- [x] Áp dụng migration `0009_menu_categories_and_topping_active` vào database cục bộ; các đồ uống hiện có được phân nhóm ban đầu. Khi thêm/sửa, người dùng chọn nhóm rõ ràng.
- [x] Django check, migration đồng bộ model, biên dịch template và **21 URL HTTP 200** đều đạt.
- [x] Toàn bộ **49/49 bài kiểm thử Django** đạt, gồm 10 bài mới về nhóm món, quyền xóa, CSRF, xóa lặp lại, từ chối topping đã xóa và bảo toàn đơn cũ.
- [x] Chrome kiểm tra lọc nhóm/tìm kiếm, trạng thái rỗng, nhớ nhóm, form phân nhóm, xác nhận hủy/xóa và thực đơn khách hàng đều đạt; không phát hiện lỗi JavaScript.
- [x] Kiểm tra bốn nhóm tại **320, 390, 768, 1440 px**: không tràn ngang; đã xem ảnh desktop/mobile.

### Mã nguồn của lần cập nhật này

| File | Nội dung |
| --- | --- |
| [menu_list.html](C:/Users/HP/Quanlypho/pho_app/templates/pho_app/admin/menu_list.html) | Tiêu đề theo ảnh, tab nhóm, ô tìm kiếm và lưới món/topping |
| [catalog_card.html](C:/Users/HP/Quanlypho/pho_app/templates/pho_app/includes/catalog_card.html) | Thẻ dùng chung với giá, nhóm và nút Sửa/Xóa |
| [figma-ui.css](C:/Users/HP/Quanlypho/pho_app/static/pho_app/css/figma-ui.css) | Kiểu tab, thẻ và bố cục responsive |
| [ui.js](C:/Users/HP/Quanlypho/pho_app/static/pho_app/js/ui.js) | Lọc nhóm/tên, cập nhật số lượng, nhớ nhóm và xác nhận xóa |
| [models.py](C:/Users/HP/Quanlypho/pho_app/models.py) | Nhóm Phở/Đồ uống và trạng thái kinh doanh của topping |
| [forms.py](C:/Users/HP/Quanlypho/pho_app/forms.py) | Lựa chọn nhóm món, bỏ checkbox ẩn món |
| [views.py](C:/Users/HP/Quanlypho/pho_app/views.py) | Danh sách còn kinh doanh, xóa khỏi thực đơn, giữ lịch sử và kiểm tra đặt món |
| [menu.js](C:/Users/HP/Quanlypho/pho_app/static/pho_app/js/menu.js) | Thực đơn khách hàng dùng nhóm từ backend |
| [0009_menu_categories_and_topping_active.py](C:/Users/HP/Quanlypho/pho_app/migrations/0009_menu_categories_and_topping_active.py) | Migration và phân nhóm đồ uống hiện có |
| [seed_demo_data.py](C:/Users/HP/Quanlypho/pho_app/management/commands/seed_demo_data.py) | Gán nhóm cho món demo khi tạo mới |
| [test_menu_management.py](C:/Users/HP/Quanlypho/pho_app/test_menu_management.py) | 10 bài kiểm thử nghiệp vụ thực đơn |

Xem tại [Thực đơn quản lý](http://127.0.0.1:8000/quan-ly/thuc-don/). Mã HTML/CSS/JavaScript được tích hợp trực tiếp vào Django, không cần build frontend. Database hiện tại đã áp dụng migration; khi chuyển code sang môi trường khác, chạy `manage.py migrate` trước.

Script QA mới: [test_catalog_tabs.cjs](C:/Users/HP/Quanlypho/scratch/test_catalog_tabs.cjs). Kết quả: [catalog-tabs-results.json](C:/Users/HP/Quanlypho/scratch/catalog-tabs-results.json). Ảnh: [desktop](C:/Users/HP/Quanlypho/scratch/ui-screenshots/catalog-tabs-1440.png), [điện thoại](C:/Users/HP/Quanlypho/scratch/ui-screenshots/catalog-tabs-390.png). Các request xóa trong trình duyệt được chặn trước khi tới server; kiểm thử xóa thật chạy trong database test riêng. Phiên đăng nhập QA được xóa sau kiểm tra.

## Đồng bộ nhánh develop trước khi push — 11/10/2026

- Giữ các cập nhật mới trên GitHub (`d7d70d6`, `7dcf5d5`) cùng giao diện, quản lý đơn hàng và thực đơn đã triển khai.
- Hòa giải hai file giao diện khách hàng: giữ HTML/CSS/JS mới, không tự đổi hình thức đặt món khi vé được gọi và áp dụng điều kiện banner đơn hàng từ nhánh remote.
- Giữ thay đổi backend cho phép địa chỉ hoặc GPS khi giao hàng; biểu mẫu cập nhật trường địa chỉ bắt buộc theo trạng thái GPS.
- Bổ sung [0010_merge_menu_and_queue.py](C:/Users/HP/Quanlypho/pho_app/migrations/0010_merge_menu_and_queue.py) để nối hai migration `0009`; đã áp dụng thành công vào database cục bộ.
- Sau khi đồng bộ: Django check và migration check đạt, **49/49 tests đạt**. Chrome xác nhận giữ hình thức giao hàng khi được gọi số, đặt giao hàng bằng GPS và yêu cầu địa chỉ khi từ chối GPS. Request đặt món QA được chặn trước server; kết quả nằm ở `scratch/merge-ui-results.json`.
- Cập nhật README với cách tạo `.env` từ `.env.example` sau khi clone và số lượng kiểm thử hiện tại. `.env`, ảnh chụp và dữ liệu QA mới tiếp tục được Git bỏ qua.
- Nhánh đích: [Bauthien/Quanlypho · develop](https://github.com/Bauthien/Quanlypho/tree/develop).

## Nhật ký

Phần **Quản lý đơn hàng** bổ sung có tiến độ, bản đồ code, 39 bài kiểm thử và cách kiểm tra tại [TIEN_DO_QUAN_LY_DON_HANG.md](C:/Users/HP/Quanlypho/TIEN_DO_QUAN_LY_DON_HANG.md).

| Ngày | Công việc | Kết quả |
| --- | --- | --- |
| 11/10/2026 | Khảo sát Django và ZIP Figma Make | Xác định thương hiệu, bố cục, ảnh và các phân hệ cần tích hợp |
| 11/10/2026 | Xây dựng HTML/CSS/JS và nối dữ liệu | Hoàn thiện các màn hình khách hàng, quản lý, thu ngân, bếp và tài khoản |
| 11/10/2026 | Kiểm tra template, URL và nghiệp vụ hiện có | 21 trang trả HTTP 200; 11 bài kiểm thử Django đạt |
| 11/10/2026 | Kiểm tra trực quan và tương tác | 48 lượt responsive đạt; giỏ hàng, GPS, dialog, sidebar và polling bếp hoạt động |
| 11/10/2026 | Bàn giao | Hoàn thành bản đồ mã nguồn, hướng dẫn xem và ảnh kiểm tra |
| 11/10/2026 | Bộ lọc nhóm theo ảnh và xóa món/topping | Hoàn tất; 49 bài kiểm thử và 4 chiều rộng trình duyệt đạt |
