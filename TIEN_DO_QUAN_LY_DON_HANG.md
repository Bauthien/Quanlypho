# Tiến độ: trang Quản lý đơn hàng

Cập nhật: **11/10/2026** · Trạng thái: **Hoàn thành**.

Triển khai theo prompt đính kèm, dùng Django Templates, CSS, JavaScript thuần và dữ liệu PostgreSQL/PostGIS hiện có.

## URL truy cập

Đăng nhập tài khoản có vai trò **ADMIN**, chọn **Đơn hàng** ở sidebar.

| Màn hình | URL |
| --- | --- |
| Danh sách đơn | [http://127.0.0.1:8000/quan-ly/don-hang/](http://127.0.0.1:8000/quan-ly/don-hang/) |
| Chi tiết | `/quan-ly/don-hang/<order_id>/` |
| Xử lý đơn | `POST /quan-ly/don-hang/<order_id>/xu-ly/` · Có CSRF |

## Công việc đã hoàn thành

- [x] Trang danh sách riêng, liên kết sidebar đang chọn và liên kết từ dashboard.
- [x] Mã đơn, giờ tạo, khách, loại đơn/bàn, phương thức/thanh toán, trạng thái, tiền món, phí giao và tổng thanh toán.
- [x] Tìm theo mã đơn, tên/tài khoản khách, tên khách vãng lai, số bàn và mã vận đơn.
- [x] Lọc loại đơn, trạng thái đơn, thanh toán, phương thức và khoảng ngày tạo theo múi giờ Django.
- [x] Sắp xếp mới nhất/cũ nhất/tổng tiền tăng hoặc giảm; phân trang 20 đơn, giữ bộ lọc.
- [x] Thống kê trên toàn bộ kết quả lọc. Đang chế biến gồm chờ bếp và đang nấu; chờ thanh toán dùng `payment_status=PENDING`.
- [x] Tổng tiền đã thanh toán chỉ tính `PAID`, **bao gồm phí giao hàng**.
- [x] Trang chi tiết có món, topping và tổng số lượng topping của dòng món, tùy chọn miễn phí, ghi chú, khách, bàn/vé, giao hàng, giá và tổng tiền.
- [x] Đơn giá lấy từ `OrderItem.item_price` đã lưu, **đã gồm topping**; thành tiền = đơn giá × số lượng, không cộng topping lần nữa.
- [x] Nút xử lý chỉ hiện khi hợp lệ. Hủy đơn và xác nhận nhận tiền có hộp xác nhận.
- [x] Dùng chung nghiệp vụ với thu ngân và bếp; kiểm tra lại điều kiện ở backend sau khi khóa đơn.
- [x] Giữ ngoại lệ bếp được hoàn tất món trực tiếp từ `PENDING_KITCHEN`.
- [x] Không xác nhận thủ công VietQR tại trang quản lý; giữ webhook kiểm tra chữ ký và số tiền.
- [x] Hủy chỉ cho tiền mặt `PENDING + CART`; kiểm tra các đơn chưa dọn bàn trước khi giải phóng bàn.
- [x] Phục vụ xong đơn tại bàn vẫn giữ `is_cleared=False`; dọn bàn qua thao tác riêng của thu ngân.
- [x] In tem chỉ cho đơn giao hàng đã thanh toán ở trạng thái `READY` hoặc `DELIVERING`.
- [x] ADMIN truy cập trang mới; STAFF/KITCHEN giữ các endpoint theo quyền hiện có; CUSTOMER bị chặn.
- [x] POST + CSRF, giao dịch atomic và khóa dòng chống xử lý lặp; signal hiện có tiếp tục là nơi trừ kho.
- [x] Giao diện Phở Nhà, tiền VNĐ định dạng từ server, bảng cuộn ngang và hướng dẫn cuộn trên điện thoại.
- [x] Kiểm thử Django và Chrome desktop/mobile.

## Code mới được lưu ở đâu?

Toàn bộ nằm trong **`C:\Users\HP\Quanlypho`**. Không cần build frontend hoặc thêm migration.

| File | Nội dung |
| --- | --- |
| [orders.html](C:/Users/HP/Quanlypho/pho_app/templates/pho_app/admin/orders.html) | HTML danh sách, lọc, thống kê, bảng, phân trang |
| [order_detail.html](C:/Users/HP/Quanlypho/pho_app/templates/pho_app/admin/order_detail.html) | HTML chi tiết, thanh toán, giao hàng và các nút xử lý |
| [figma-ui.css](C:/Users/HP/Quanlypho/pho_app/static/pho_app/css/figma-ui.css) | Phần CSS bổ sung: `Dedicated order management` |
| [orders.js](C:/Users/HP/Quanlypho/pho_app/static/pho_app/js/orders.js) | Xác nhận hủy/nhận tiền và chống nhấn nút liên tục |
| [views.py](C:/Users/HP/Quanlypho/pho_app/views.py) | Danh sách/chi tiết/xử lý ADMIN; các màn hình cũ gọi service chung |
| [services.py](C:/Users/HP/Quanlypho/pho_app/services.py) | `available_order_actions`, `apply_order_action` và khóa đơn/bàn |
| [forms.py](C:/Users/HP/Quanlypho/pho_app/forms.py) | `OrderFilterForm` kiểm tra lựa chọn, tìm kiếm và ngày |
| [urls.py](C:/Users/HP/Quanlypho/pho_app/urls.py) | Ba route mới |
| [order_format.py](C:/Users/HP/Quanlypho/pho_app/templatetags/order_format.py) | Bộ lọc template `vnd` định dạng tiền; có `__init__.py` cùng thư mục |
| [sidebar.html](C:/Users/HP/Quanlypho/pho_app/templates/pho_app/includes/sidebar.html) | Liên kết Đơn hàng và trạng thái đang chọn |
| [dashboard.html](C:/Users/HP/Quanlypho/pho_app/templates/pho_app/admin/dashboard.html) | Liên kết xem tất cả và mở chi tiết đơn gần đây |
| [test_orders.py](C:/Users/HP/Quanlypho/pho_app/test_orders.py) | 28 bài kiểm thử mới |

## Kết quả kiểm thử

| Kiểm tra | Kết quả |
| --- | --- |
| Django `manage.py check` | Đạt, không có lỗi |
| Django `manage.py test --noinput` | **39/39 đạt**: 11 bài cũ + 28 bài mới |
| Phân quyền, POST và CSRF | Đạt |
| Tìm kiếm, mọi bộ lọc, ngày/múi giờ, sắp xếp và phân trang giữ điều kiện | Đạt |
| Thống kê nhiều trang, tổng tiền gồm phí giao, không dùng lại giá món hiện tại | Đạt |
| Luồng tiền mặt/tại bàn/giao hàng; chặn sai trạng thái, sai loại, đơn chưa trả tiền | Đạt |
| Gửi lại xác nhận qua trang quản lý và thu ngân | Trừ nguyên liệu đúng một lần |
| Hai yêu cầu xác nhận chạy đồng thời trên PostgreSQL | Một yêu cầu cập nhật; yêu cầu còn lại bị chặn; kho trừ đúng một lần |
| Callback VietQR lặp, chữ ký không hợp lệ | Đạt |
| Hủy đơn có đơn khác đang hoạt động hoặc hoàn tất nhưng chưa dọn | Giữ bàn đang sử dụng |
| Số query chi tiết khi tăng số món | Không tăng theo số món |
| Cú pháp `orders.js`, `git diff --check` | Đạt |
| 21 trang có sẵn qua Django Client | HTTP 200; quyền khách hàng giữ nguyên |
| 12 kiểm tra URL/quyền của trang đơn mới trên dữ liệu thật | Đạt |
| Chrome: danh sách/chi tiết/rỗng × 320, 390, 768, 1440 px | **12 lượt hiển thị không tràn ngang** |
| Chrome: cuộn bảng, tìm kiếm, kết hợp bộ lọc, xóa lọc, lỗi ngày, sidebar, dashboard → chi tiết | Đạt |
| Chrome: xác nhận hủy/nhận tiền và payload POST có CSRF | Đạt bằng fixture chưa lưu và request bị chặn |
| Lỗi JavaScript | Không phát hiện |

Python Launcher của máy hiện báo `No suitable Python runtime found` với `py -3.12`. Các lệnh được chạy thành công bằng Python 3.12 đã cài ở đường dẫn đầy đủ:

```powershell
cd C:\Users\HP\Quanlypho
& 'C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe' -B manage.py check
& 'C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe' -B manage.py test --noinput
```

Kiểm thử nghiệp vụ chạy trong database kiểm thử riêng. QA trình duyệt chỉ đọc đơn thật; xác nhận hộp thoại dùng một đối tượng đơn chưa lưu và chặn POST trước khi tới server. Không thay đổi đơn hoặc tồn kho thật để kiểm tra.

Ảnh và kết quả nằm trong `scratch/` (được Git bỏ qua): `orders-route-results.json`, `orders-browser-results.json`, `ui-screenshots/orders-desktop.png`, `orders-mobile.png`, `order-management-desktop.png`, `order-management-mobile.png`.

Script QA: `scratch/check_ui.py` tạo phiên tạm; `scratch/check_orders_ui.py` kiểm tra URL và tạo fixture chưa lưu; `scratch/test_orders_ui.cjs` kiểm tra trình duyệt. Phiên QA và HTML fixture tạm được xóa sau khi kiểm tra. Google Fonts bị môi trường QA chặn; đã kiểm tra font hệ thống dự phòng. Responsive kiểm tra bằng viewport Chrome, chưa kiểm tra trên điện thoại vật lý.

## Cách kiểm tra thủ công

1. Khởi động Django, đăng nhập ADMIN, chọn **Đơn hàng** trên sidebar hoặc mở URL ở trên.
2. Tìm mã đơn/tên khách/số bàn/mã vận đơn. Kết hợp trạng thái, phương thức, ngày rồi chọn **Áp dụng bộ lọc**. Chuyển trang nếu có hơn 20 kết quả; kiểm tra bộ lọc vẫn giữ nguyên.
3. Mở **Chi tiết**. Đối chiếu đơn giá đã lưu, topping, tiền món, phí giao và tổng thanh toán. Đổi giá thực đơn không làm thay đổi số tiền lịch sử đơn.
4. Trên đơn thử nghiệm tiền mặt chưa trả tiền, xác nhận đã nhận tiền rồi bắt đầu chế biến, đánh dấu món xong và phục vụ. Đơn giao hàng đi qua bàn giao và giao xong; link in tem xuất hiện khi hợp lệ.
5. Thử **Hủy đơn tiền mặt**, chọn Hủy/Cancel trong hộp thoại để bỏ thao tác; chọn đồng ý chỉ trên đơn thử nghiệm. Bàn còn đơn chưa dọn vẫn được giữ.
6. Sau khi phục vụ tại bàn, kiểm tra đơn hoàn tất nhưng bàn vẫn sử dụng; dọn bàn riêng tại **Thu ngân**.
7. Đăng nhập STAFF/KITCHEN/CUSTOMER để kiểm tra trang mới bị chặn; thu ngân và bếp vẫn thao tác tại màn hình được cấp quyền.
8. Thu hẹp cửa sổ về điện thoại: mở sidebar, cuộn ngang bảng và kiểm tra các nút/nhãn.

## Nhật ký

| Ngày | Công việc | Trạng thái |
| --- | --- | --- |
| 11/10/2026 | Đọc prompt, model, signal, phân quyền và luồng xử lý cũ | Hoàn thành |
| 11/10/2026 | Viết kiểm thử trước, thêm service chung và route quản lý | Hoàn thành |
| 11/10/2026 | Xây dựng HTML/CSS/JS, nối sidebar và dashboard | Hoàn thành |
| 11/10/2026 | Chạy kiểm thử PostgreSQL, đồng thời và Chrome | Hoàn thành |
| 11/10/2026 | Ghi bản đồ mã nguồn, URL và hướng dẫn kiểm tra | Hoàn thành |
