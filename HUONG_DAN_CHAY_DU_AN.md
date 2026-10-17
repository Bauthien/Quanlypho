# 📘 HƯỚNG DẪN CHẠY VÀ SỬ DỤNG DỰ ÁN QUẢN LÝ PHỞ (QUANLYPHO)

Tài liệu hướng dẫn chi tiết cách thiết lập, chạy dự án và thao tác thử nghiệm các luồng nghiệp vụ trên máy tính cục bộ.

---

## I. TỔNG QUAN DỰ ÁN

- **Tên dự án**: Hệ thống Quản lý Quán Phở Việt (`Quanlypho`)
- **Kiến trúc**: Django Web Framework (Monolith MVT)
- **Cơ sở dữ liệu**: PostgreSQL + PostGIS (Hỗ trợ dữ liệu không gian, định tuyến khoảng cách giao hàng)
- **4 Phân hệ người dùng**:
  1. 👤 **Khách hàng (`CUSTOMER`)**: Đặt món tại bàn theo mã QR, lấy số thứ tự xếp hàng khi quán đông, đặt món giao tận nơi.
  2. 💵 **Thu ngân / Tiếp tân (`STAFF`)**: Điều phối bàn ăn, tiếp nhận tiền mặt, gọi số thứ tự xếp hàng, bàn giao shipper.
  3. 🍳 **Bếp trưởng (`KITCHEN`)**: Tiếp nhận đơn theo thời gian thực, chế biến món, in tem giao hàng.
  4. 👑 **Quản trị viên (`ADMIN`)**: Phân quyền tài khoản, quản lý bàn ăn, chỉnh sửa món ăn/topping, quản lý định lượng kho (BOM).

---

## II. CÁCH CHẠY DỰ ÁN NHANH (QUICK START)

Dự án hiện **đã được khởi chạy thành công** tại:
👉 **URL**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

Nếu bạn muốn khởi động lại máy chủ trong lần làm việc tiếp theo:

1. Mở cửa sổ **Terminal** hoặc **PowerShell** tại thư mục `c:\Users\HP\Quanlypho`.
2. Chạy lệnh:
   ```powershell
   py -3.12 manage.py runserver 127.0.0.1:8000
   ```
3. Mở trình duyệt web và truy cập `http://127.0.0.1:8000/`.

---

## III. DANH SÁCH TÀI KHOẢN MẪU & MẬT KHẨU

Hệ thống đã được nạp sẵn dữ liệu mẫu (Seed Data) với đầy đủ 4 nhóm vai trò:

| Phân hệ / Vai trò | Tài khoản | Mật khẩu | Đường dẫn đăng nhập / trực tiếp |
| :--- | :--- | :--- | :--- |
| **Quản trị viên** | `admin` | `admin123` | [http://127.0.0.1:8000/quan-ly/](http://127.0.0.1:8000/quan-ly/) |
| **Quản lý quán** | `quanly` | `admin123` | [http://127.0.0.1:8000/quan-ly/](http://127.0.0.1:8000/quan-ly/) |
| **Thu ngân / Tiếp tân** | `thungan` | `thungan123` | [http://127.0.0.1:8000/thu-ngan/](http://127.0.0.1:8000/thu-ngan/) |
| **Bếp Trưởng** | `bep` | `bep123` | [http://127.0.0.1:8000/bep/](http://127.0.0.1:8000/bep/) |
| **Khách hàng** | `khachhang` | `khach123` | [http://127.0.0.1:8000/thuc-don/](http://127.0.0.1:8000/thuc-don/) |

> 💡 **Mẹo:** Bạn có thể mở một cửa sổ trình duyệt bình thường (ví dụ: đăng nhập tài khoản Khách hàng) và một cửa sổ ẩn danh (Incognito) để đăng nhập tài khoản Thu ngân hoặc Bếp nhằm kiểm tra các luồng tương tác thời gian thực giữa hai bên.

---

## IV. HƯỚNG DẪN TEST CÁC LUỒNG NGHIỆP VỤ

### 1. Luồng 1: Khách ngồi tại bàn gọi món (QR Table Ordering)
1. **Truy cập thực đơn kèm số bàn**: Vào [http://127.0.0.1:8000/thuc-don/?table=1](http://127.0.0.1:8000/thuc-don/?table=1) (đóng vai khách đang ngồi Bàn số 1).
2. **Chọn món**:
   - Chọn món chính (ví dụ: *Phở Bò Tái* 55.000đ).
   - Chọn thêm Topping (ví dụ: *Trứng chần nước béo* +5.000đ, *Quẩy giòn* +10.000đ).
   - Chọn tùy chọn miễn phí (Nước dùng béo ngậy, Không hành hoa, Bánh phở bình thường).
3. **Thanh toán**:
   - Nhấn mở giỏ hàng -> Chọn phương thức **Chuyển khoản VietQR** (hoặc Tiền mặt).
   - Nhấn **Đặt món**.
   - Tại trang chi tiết đơn hàng:
     - Nếu chọn VietQR: Màn hình hiển thị mã QR chuyển khoản. Để kiểm thử nhanh không cần chuyển khoản thật, nhấn nút **"Mô phỏng thanh toán thành công"**.
4. **Bếp nhận đơn**:
   - Đăng nhập tài khoản `bep` (mật khẩu `bep123`) tại [http://127.0.0.1:8000/bep/](http://127.0.0.1:8000/bep/).
   - Thấy đơn Bàn số 1 xuất hiện ở trạng thái **Đang gửi Bếp**.
   - Bếp nhấn **"Bắt đầu làm"** (chuyển sang *Bếp đang làm*) -> Làm xong nhấn **"Hoàn thành món"**.
5. **Dọn bàn & Thu ngân giải phóng bàn**:
   - Thu ngân vào [http://127.0.0.1:8000/thu-ngan/](http://127.0.0.1:8000/thu-ngan/) xác nhận khách dùng xong -> bàn chuyển sang trạng thái **Đang dọn dẹp** -> nhấn **Giải phóng bàn** để bàn trở lại trạng thái **Trống**.

---

### 2. Luồng 2: Xếp hàng ảo khi quán đông (Virtual Queue - FIFO)
1. Khách truy cập: [http://127.0.0.1:8000/xep-hang/lay-so/](http://127.0.0.1:8000/xep-hang/lay-so/)
2. Nhập tên của khách (hoặc đã đăng nhập sẵn) và nhấn **Lấy số thứ tự**.
3. Hệ thống cấp vé số (ví dụ: `P-001`, `P-002`...).
4. Khách được chuyển sang trang thực đơn để **chọn món trước vào giỏ hàng**, không cần đợi có bàn mới chọn món.
5. Khi có bàn trống, Thu ngân tại [http://127.0.0.1:8000/thu-ngan/](http://127.0.0.1:8000/thu-ngan/) nhìn thấy danh sách hàng đợi FIFO:
   - Thu ngân chọn một bàn trống và nhấn **"Gọi vào bàn"**.
6. Trình duyệt của khách đang mở tự động thông báo đã được gọi vào bàn, rung chuông và chuyển thẳng giỏ hàng đã chọn vào bàn ăn để tiến hành đặt món.

---

### 3. Luồng 3: Đặt món Giao tận nơi (Delivery & Định vị GPS)
1. Khách vào [http://127.0.0.1:8000/thuc-don/](http://127.0.0.1:8000/thuc-don/), chọn món vào giỏ hàng.
2. Tại giỏ hàng, chọn loại đơn: **Giao tận nơi**.
3. Nhập địa chỉ nhận hàng, số điện thoại người nhận.
4. Nhập tọa độ GPS (hoặc hệ thống tự động gán tọa độ nhận hàng).
5. Hệ thống sử dụng công thức tính khoảng cách không gian (Haversine qua PostGIS) để tự động tính phí ship theo số km (ví dụ: 15.000đ cơ bản + 8.000đ/km).
6. Thanh toán qua VietQR (hoặc mô phỏng thanh toán).
7. Màn hình Bếp hiển thị đơn giao tận nơi. Sau khi chế biến xong, Bếp mở liên kết **In tem nhãn** ([http://127.0.0.1:8000/bep/don-giao-hang/<id>/in-tem/](http://127.0.0.1:8000/bep/)) để in 2 tem:
   - Tem 1: Dán lên bao bì / hộp phở.
   - Tem 2: Bàn giao cho tài xế giao hàng (ghi rõ địa chỉ, tiền thu, mã đơn).
8. Thu ngân xác nhận shipper đã nhận hàng và hoàn tất đơn.

---

### 4. Luồng 4: Quản lý Quán & Kiểm soát tồn kho tự động (BOM)
1. Đăng nhập tài khoản `admin` (mật khẩu `admin123`) tại [http://127.0.0.1:8000/quan-ly/](http://127.0.0.1:8000/quan-ly/).
2. **Quản lý Bàn ăn**: Thêm mới bàn, sửa sức chứa (số tô tối đa trên bàn), tải mã QR của từng bàn.
3. **Quản lý Thực đơn & Topping**: Thêm món ăn mới, upload ảnh chính, ảnh góc cận cảnh, thêm topping tính phí.
4. **Quản lý Người dùng**: Phân quyền nhân viên (nâng quyền một tài khoản lên Thu ngân hoặc Bếp).
5. **Kho nguyên vật liệu (BOM)**:
   - Khi một đơn hàng bất kỳ hoàn tất thanh toán (trạng thái `PAID`), hệ thống tự động kích hoạt Signal trừ số lượng thịt bò, bánh phở, nước dùng theo công thức định lượng đã cấu hình.

---

## V. CÁC LỆNH TIỆN ÍCH HỆ THỐNG

### 1. Nạp lại dữ liệu mẫu từ đầu
Nếu muốn tạo mới lại toàn bộ dữ liệu mẫu (15 bàn, 5 món, topping, 5 tài khoản):
```powershell
py -3.12 manage.py seed_demo_data
```

### 2. Tạo tài khoản quản trị viên mới
```powershell
py -3.12 manage.py create_admin --username ten_admin --password mat_khau_moi --name "Tên Quản Trị"
```

### 3. Chạy kiểm thử tự động (Unit Tests)
```powershell
py -3.12 manage.py test
```
*(Hiện tại 49/49 bài kiểm thử tự động đã đạt, gồm quản lý đơn hàng và thực đơn/topping)*.

---

## VI. THÔNG TIN CẤU HÌNH KỸ THUẬT

- **Tệp cấu hình môi trường**: `.env` đặt tại thư mục gốc `c:\Users\HP\Quanlypho\.env`.
- **Cơ sở dữ liệu**:
  - Tên DB: `Quanlypho`
  - Người dùng: `postgres`
  - Mật khẩu: `123456`
  - Host: `localhost:5432`
- **Đường dẫn PostGIS/GDAL Windows**: `C:\Program Files\PostgreSQL\18\bin`
