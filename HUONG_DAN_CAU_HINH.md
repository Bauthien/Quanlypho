# Hướng dẫn cấu hình hệ thống quản lý phở

## Vai trò và tài khoản

- Đăng ký tại `/dang-ky/`: máy chủ luôn gán vai trò **Khách hàng**; dữ liệu POST tự gửi vai trò không được chấp nhận.
- Đăng nhập tại `/dang-nhap/`: sau đăng nhập, người dùng được chuyển tới menu, thu ngân, bếp hoặc quản lý tùy vai trò.
- Chỉ tài khoản có vai trò Quản lý mới được sửa vai trò/khóa tài khoản ở `/quan-ly/nguoi-dung/`.
- Django admin `/admin/` đã bị tắt. Trang quản lý riêng dùng `/quan-ly/` và tài khoản role ADMIN (không cần superuser).
- Tạo tài khoản quản lý ban đầu bằng management command `create_admin`, truyền username/password riêng qua tham số hoặc biến môi trường `ADMIN_INITIAL_PASSWORD`. Không dùng mật khẩu mẫu trong môi trường thật.

## Cài đặt và chạy local

1. Cài các gói trong `requirements.txt` vào môi trường Python của dự án.
2. Cài PostgreSQL có PostGIS, tạo database `Quanlypho` (hoặc cấu hình tên database khác).
3. Đặt các biến môi trường cần thiết trước khi chạy Django:
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.
   - `DJANGO_SECRET_KEY` (chuỗi ngẫu nhiên riêng), `DJANGO_DEBUG` và `DJANGO_ALLOWED_HOSTS`.
   - `VIETQR_BANK_ID`, `VIETQR_ACCOUNT_NO`, `VIETQR_ACCOUNT_NAME` để tạo ảnh QR theo định dạng VietQR.
   - `PAYMENT_WEBHOOK_SECRET` để xác thực callback thanh toán.
   - `DELIVERY_FLAT_FEE` (mặc định 30000 VNĐ).
4. Áp dụng migration bằng `manage.py migrate`, tạo quản lý và khởi động bằng `manage.py runserver`.
5. Trong giao diện Quản lý, thêm món, topping, bàn và đảm bảo các tùy chọn tùy biến mặc định đã có (được tạo bởi migration 0002).

> Cấu hình database, secret key và GIS DLL hiện có giá trị mặc định phục vụ môi trường phát triển Windows. Không đưa các giá trị mặc định này lên môi trường public/production. Production phải dùng HTTPS, DEBUG=False, secret riêng, ALLOWED_HOSTS chính xác và PostGIS/GDAL tương thích.

## Tích hợp VietQR / webhook

Trang đơn tạo ảnh QR VietQR với số tiền chính xác (tiền món + phí giao hàng), nội dung chuyển khoản là mã đơn. Việc tạo ảnh QR **không chứng minh đã nhận tiền**; đơn luôn ở trạng thái chờ cho đến callback hợp lệ.

Endpoint callback là `POST /thanh-toan/vietqr/webhook/`. Lớp tích hợp cổng thanh toán/ngân hàng cần chuẩn hóa callback thành JSON gồm `order_code`, `amount` (VND) và `status` (`success`/`paid` khi thành công), sau đó ký **nguyên byte body** bằng HMAC-SHA256 với `PAYMENT_WEBHOOK_SECRET`, gửi chữ ký hex ở header `X-Payment-Signature`. Ứng dụng kiểm chữ ký, mã đơn, phương thức và số tiền; xử lý callback lặp một cách idempotent. Callback thành công mới đặt đơn `PAID` và đẩy vào màn hình Bếp.

VietQR chỉ là chuẩn sinh mã chuyển khoản; ảnh QR không tự cung cấp webhook ngân hàng. Cần đăng ký một nhà cung cấp có webhook (hoặc dịch vụ ngân hàng hỗ trợ), viết/cấu hình adapter để xác minh chữ ký của chính nhà cung cấp rồi mới ký payload chuẩn của ứng dụng. Không để endpoint này công khai nhận callback chưa xác thực.

## Các luồng đã triển khai

- Tại bàn: menu QR có thể mở bằng `?table=<id>`; chỉ bàn trống hoặc bàn đang ở QR tương ứng nhận đơn. Tiền mặt chờ thu ngân xác nhận; VietQR chờ callback. Sau khi khách hoàn tất phục vụ, bàn chuyển qua trạng thái cần dọn rồi thu ngân giải phóng.
- Hàng đợi: vé FIFO; thu ngân phải gắn vé kế tiếp với bàn đang trống. Trình duyệt khách đang mở menu kiểm tra vé mỗi 8 giây, rung thiết bị khi được gọi và chuyển giỏ sang luồng vào bàn.
- Giao hàng: yêu cầu địa chỉ, bắt buộc VietQR, tính phí ship cấu hình dạng phí cố định. Bếp hoàn tất sẽ mở trang in hai tem tách biệt; thu ngân bàn giao và xác nhận giao xong.
- Admin: báo cáo, vai trò tài khoản, món và topping. Xóa món sẽ ẩn khỏi menu để giữ lịch sử đơn.

## Phần cần tích hợp ngoài trước khi vận hành thật

- Phí ship theo khoảng cách/PostGIS: hiện dùng phí cố định, chưa định tuyến địa chỉ/tọa độ.
- Thông báo hàng đợi chạy khi khách còn mở trang; chưa có push notification nền/SMS.
- In tem dùng hộp thoại in trình duyệt; cần cấu hình driver/kích cỡ giấy và máy in nhiệt tại quán.
- Bàn giao đơn giao hàng được ghi nhận trong hệ thống; chưa có API điều phối Grab/ShopeeFood/đơn vị vận chuyển.
- VietQR cần adapter webhook thực tế như mô tả trên; không đánh dấu đã trả chỉ dựa vào việc khách tải trang/ảnh QR.
