# 🍜 Hệ Thống Quản Lý Quán Phở Việt (Quanlypho)

Ứng dụng web toàn diện quản lý hoạt động vận hành quán phở, xây dựng trên nền tảng **Python / Django 6**, hệ cơ sở dữ liệu không gian **PostgreSQL + PostGIS**, hỗ trợ 4 phân hệ người dùng (Khách hàng, Thu ngân, Bếp, Quản lý) và 3 luồng vận hành chuyên sâu: Gọi món tại bàn bằng QR, Hàng đợi ảo FIFO, và Đặt món giao tận nơi với định tuyến GPS.

---

## 📌 Mục Lục
1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Cài đặt và Cấu hình](#2-cài-đặt-và-cấu-hình)
3. [Hướng dẫn Khởi chạy Dự án](#3-hướng-dẫn-khởi-chạy-dự-án)
4. [Tài khoản mẫu & Các phân hệ truy cập](#4-tài-khoản-mẫu--các-phân-hệ-truy-cập)
5. [Các luồng nghiệp vụ chính](#5-các-luồng-nghiệp-vụ-chính)
6. [Chạy Kiểm thử tự động (Tests)](#6-chạy-kiểm-thử-tự-động-tests)
7. [Cấu trúc mã nguồn](#7-cấu-trúc-mã-nguồn)
8. [Lưu ý kỹ thuật & Bảo mật](#8-lưu-ý-kỹ-thuật--bảo-mật)

---

## 1. Yêu cầu hệ thống

- **Hệ điều hành**: Windows 10/11 (hoặc Linux / macOS)
- **Python**: Phiên bản `3.12+` (khuyến nghị chạy bằng launcher `py -3.12`)
- **PostgreSQL**: Phiên bản `16+` hoặc `18` có cài tiện ích không gian **PostGIS**
  - Thư mục thư viện PostGIS Windows mặc định: `C:\Program Files\PostgreSQL\18\bin`
- **Các thư viện Python chính**:
  - `Django==6.1.1`
  - `Pillow==12.3.0` (xử lý hình ảnh món ăn, QR code)
  - `psycopg2-binary==2.9.13` (driver kết nối PostgreSQL)
  - `python-dotenv>=1.0.0` (tự động đọc cấu hình `.env`)

---

## 2. Cài đặt và Cấu hình

### Bước 1: Cài đặt thư viện Python
Mở Terminal / PowerShell tại thư mục dự án và chạy:
```powershell
py -3.12 -m pip install -r requirements.txt
```

### Bước 2: Chuẩn bị Cơ sở dữ liệu PostgreSQL
Khởi tạo cơ sở dữ liệu `Quanlypho` và kích hoạt extension `postgis`:
```sql
CREATE DATABASE "Quanlypho";
\c Quanlypho
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Bước 3: Cấu hình biến môi trường (`.env`)
Sau khi clone repository, tạo file cấu hình cục bộ từ mẫu rồi điền thông tin PostgreSQL và các khóa riêng của bạn:
```powershell
Copy-Item .env.example .env
```
File `.env` được Django tự nạp và không đưa lên Git. Ví dụ cấu hình chỉ dành cho môi trường phát triển:
```ini
DJANGO_SECRET_KEY=django-insecure-dev-only-change-before-deploy
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=Quanlypho
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123456
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Cấu hình thanh toán VietQR
VIETQR_BANK_ID=
VIETQR_ACCOUNT_NO=
VIETQR_ACCOUNT_NAME=
PAYMENT_WEBHOOK_SECRET=vietqr-secret-key-123456

# Cấu hình phí giao hàng và GPS quán
DELIVERY_FLAT_FEE=30000
DELIVERY_BASE_FEE=15000
DELIVERY_FEE_PER_KM=8000
DELIVERY_MAX_KM=10
RESTAURANT_LAT=10.7769
RESTAURANT_LNG=106.7009

# Mật khẩu quản trị viên ban đầu
ADMIN_INITIAL_PASSWORD=admin123
```

---

## 3. Hướng dẫn Khởi chạy Dự án

Chỉ cần thực hiện 3 lệnh sau theo thứ tự:

### Bước 1: Áp dụng Migrations vào Cơ sở dữ liệu
```powershell
py -3.12 manage.py migrate
```

### Bước 2: Khởi tạo Dữ liệu Mẫu (Seed Data)
Lệnh này sẽ tự động:
- Tạo 15 bàn ăn (Bàn 1 đến 15).
- Nạp 5 món phở và nước uống kèm ảnh minh họa.
- Nạp danh mục Topping (Trứng chần, Quẩy giòn, Bò thêm...).
- Nạp các tùy chọn miễn phí (Nước dùng béo/trong, Rau giá, Bánh phở).
- Thiết lập định lượng kho (BOM) và nguyên vật liệu tồn kho.
- Khởi tạo 5 tài khoản mẫu cho đầy đủ các vai trò.

```powershell
py -3.12 manage.py seed_demo_data
```

### Bước 3: Chạy Máy Chủ Phát Triển (Development Server)
```powershell
py -3.12 manage.py runserver 127.0.0.1:8000
```
Sau khi chạy, mở trình duyệt truy cập:
👉 **http://127.0.0.1:8000/**

---

## 4. Tài khoản mẫu & Các phân hệ truy cập

Hệ thống phân quyền nghiêm ngặt theo 4 vai trò. Khi đăng nhập tại `/dang-nhap/`, hệ thống sẽ tự động điều hướng đúng trang của vai trò đó:

| Vai trò | Tên đăng nhập | Mật khẩu | Trang truy cập chính | Chức năng chính |
| :--- | :--- | :--- | :--- | :--- |
| **Quản trị viên** | `admin` | `admin123` | `http://127.0.0.1:8000/quan-ly/` | Quản lý người dùng, phân quyền, cấu hình bàn, sửa thực đơn, báo cáo doanh thu |
| **Quản lý quán** | `quanly` | `admin123` | `http://127.0.0.1:8000/quan-ly/` | Quản lý danh mục món, topping, giám sát hoạt động quán |
| **Thu ngân / Tiếp tân** | `thungan` | `thungan123` | `http://127.0.0.1:8000/thu-ngan/` | Điều phối bàn ăn, duyệt đơn tiền mặt, gọi số xếp hàng, giao đơn shipper |
| **Bếp Trưởng** | `bep` | `bep123` | `http://127.0.0.1:8000/bep/` | Nhận đơn thời gian thực, chế biến món, in tem giao hàng, hoàn thành món |
| **Khách hàng** | `khachhang` | `khach123` | `http://127.0.0.1:8000/thuc-don/` | Xem thực đơn, đặt món tại bàn, lấy số hàng đợi, đặt món giao tận nơi |

> **Lưu ý bảo mật:** Django admin mặc định `/admin/` đã bị tắt (trả về 404). Toàn bộ thao tác quản trị được thực hiện tại giao diện riêng `/quan-ly/`.

---

## 5. Các luồng nghiệp vụ chính

### Luồng 1: Gọi món tại bàn (Dine-in với mã QR)
1. Khách truy cập menu chọn bàn hoặc quét mã QR: `http://127.0.0.1:8000/thuc-don/?table=1`
2. Chọn món chính (Phở Tái, Phở Nạm...), chọn Topping tính phí, tùy chỉnh miễn phí (Nước dùng béo/thanh, Không hành...).
3. Chọn hình thức thanh toán:
   - **Tiền mặt**: Chờ thu ngân tại quầy xác nhận đã nhận tiền trên màn hình Thu Ngân.
   - **Chuyển khoản VietQR**: Hệ thống sinh mã QR chuyển khoản chính xác nội dung đơn. Trong môi trường kiểm thử, khách có thể nhấn nút **"Mô phỏng thanh toán thành công"** để chuyển ngay đơn xuống bếp.
4. Bếp nhận đơn, chế biến, đánh dấu hoàn tất.
5. Sau khi khách dùng xong, thu ngân chuyển trạng thái bàn qua `Đang dọn dẹp` rồi giải phóng về `Trống`.

### Luồng 2: Hàng đợi ảo (Virtual Queue - FIFO)
1. Khi tất cả các bàn đều có khách hoặc khách chưa có chỗ, khách có thể lấy số thứ tự tại: `http://127.0.0.1:8000/xep-hang/lay-so/` (khách vãng lai nhập tên hoặc khách đã đăng nhập).
2. Hệ thống cấp vé thứ tự (VD: `P-001`, `P-002`...).
3. Khách có thể xem trước thực đơn và thêm món sẵn vào giỏ trong lúc chờ đợi.
4. Khi có bàn trống, Thu ngân vào màn hình `/thu-ngan/`, chọn bàn và nhấn **Gọi số**.
5. Màn hình của khách tự động cập nhật, rung chuông báo hiệu và chuyển giỏ hàng sang luồng vào bàn ăn.

### Luồng 3: Đặt món Giao tận nơi (Delivery & Định tuyến GPS)
1. Khách chọn hình thức **Giao tận nơi** tại trang giỏ hàng.
2. Nhập họ tên, số điện thoại, địa chỉ nhận hàng và tọa độ GPS (kinh độ, vĩ độ).
3. Hệ thống dùng công thức khoảng cách Haversine tính cước phí giao hàng tự động theo km.
4. Đơn giao hàng thanh toán qua VietQR.
5. Khi Bếp chế biến xong, bếp mở trang **In tem nhãn** (`/bep/don-giao-hang/<id>/in-tem/`) để in 2 tem nhiệt: 1 tem dán hộp thức ăn, 1 tem bàn giao tài xế.
6. Thu ngân xác nhận bàn giao cho shipper và hoàn tất đơn hàng.

### Luồng 4: Định lượng & Quản lý Kho nguyên vật liệu (BOM)
- Hệ thống thiết lập bảng định lượng (Bill of Materials): mỗi tô Phở Tái tiêu hao 150g thịt bò, 200g bánh phở, 0.5L nước hầm.
- Khi đơn hàng chuyển trạng thái **ĐÃ THANH TOÁN (PAID)**, signal Django tự động trừ tồn kho nguyên liệu tương ứng và ghi nhận lịch sử giao dịch xuất kho.

---

## 6. Chạy Kiểm thử tự động (Tests)

Bộ kiểm thử bao gồm 49 kịch bản về phân quyền, bảo mật webhook HMAC-SHA256 VietQR, xếp hàng, đặt món, quản lý đơn hàng, bộ lọc nhóm và xóa món/topping có giữ lịch sử:
```powershell
py -3.12 manage.py test
```
**Kết quả mong đợi:**
```
Ran 49 tests
OK
System check identified no issues (0 silenced).
```

---

## 7. Cấu trúc mã nguồn

```
Quanlypho/
├── core_project/                   # Cấu hình dự án Django
│   ├── settings.py                 # Cấu hình DB, PostGIS, GDAL Windows, Dotenv, VietQR
│   ├── urls.py                     # Định tuyến gốc & vô hiệu hóa /admin/
│   └── wsgi.py / asgi.py           # Điểm kết nối Web Server
├── pho_app/                        # Ứng dụng chính Quản lý Quán Phở
│   ├── management/commands/        # Lệnh CLI quản trị
│   │   ├── create_admin.py         # Lệnh tạo tài khoản admin
│   │   └── seed_demo_data.py       # Lệnh nạp dữ liệu mẫu hoàn chỉnh
│   ├── migrations/                 # Lịch sử 8 phiên bản migration
│   ├── forms.py                    # Form đăng ký, đăng nhập, CRUD bàn, món, topping
│   ├── models.py                   # ORM Models (User, Table, MenuItem, Order, Recipe...)
│   ├── permissions.py              # Decorators kiểm tra vai trò (@admin_required, @staff_required...)
│   ├── services.py                 # Logic nghiệp vụ (tính phí ship, tọa độ, sức chứa bàn)
│   ├── signals.py                  # Tự động xuất kho theo định lượng (BOM)
│   ├── tests.py                    # 11 kịch bản kiểm thử tự động
│   ├── urls.py                     # Định tuyến toàn bộ API & màn hình ứng dụng
│   ├── views.py                    # Controllers xử lý logic nghiệp vụ
│   ├── static/pho_app/             # CSS & JS (app.css, menu.js)
│   └── templates/pho_app/          # Giao diện HTML (admin, staff, kitchen, customer, auth)
├── media/                          # Thư mục chứa hình ảnh món ăn, topping, QR code
├── .env                            # Tệp biến môi trường cục bộ (tự động nạp)
├── .env.example                    # Tệp mẫu hướng dẫn khai báo môi trường
├── requirements.txt                # Danh mục thư viện Python
└── README.md                       # Tài liệu hướng dẫn sử dụng chi tiết
```

---

## 8. Lưu ý kỹ thuật & Bảo mật

1. **PostGIS trên Windows**: Trong `core_project/settings.py` đã cấu hình tự động trỏ đến đường dẫn cài đặt PostgreSQL 18 (`C:\Program Files\PostgreSQL\18\bin`) và nạp thư viện `libgdal-35.dll`, `libgeos_c.dll`. Nếu bạn dùng phiên bản PostgreSQL khác, hãy điều chỉnh đường dẫn `POSTGIS_BIN` trong `settings.py`.
2. **Khách hàng tự đăng ký**: Mọi tài khoản tự tạo tại `/dang-ky/` luôn được hệ thống gán vai trò `Khách hàng (CUSTOMER)`. Không một ai có thể tự nâng quyền thành Quản lý hoặc Thu ngân thông qua API đăng ký.
3. **Webhook VietQR**: Endpoint nhận callback thanh toán `/thanh-toan/vietqr/webhook/` bắt buộc kiểm tra chữ ký số HMAC-SHA256 qua header `X-Payment-Signature` với bí mật `PAYMENT_WEBHOOK_SECRET` để chống giả mạo giao dịch.
