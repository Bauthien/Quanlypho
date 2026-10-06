# HTML Export – Phở Nhà Restaurant Management System

Thư mục này chứa các file HTML/CSS thuần (không cần React, không cần build) được export từ giao diện Figma/React của dự án.

## Danh sách file

| File | Màn hình |
|------|----------|
| `styles.css` | CSS chung cho toàn bộ các trang |
| `home.html` | 🏠 Trang chủ nhà hàng (public) – Hero, menu, story, review, liên hệ |
| `dashboard.html` | 📊 Tổng quan – Stats cards, biểu đồ doanh thu, đơn gần đây |
| `orders.html` | 🧾 Đơn hàng – Bảng lọc và quản lý tất cả đơn |
| `menu.html` | 🍜 Thực đơn – Grid món ăn, filter theo danh mục |
| `kitchen.html` | 👨‍🍳 Màn hình bếp – Cards chế biến theo thời gian thực |
| `queue.html` | 🪑 Hàng đợi & Bàn – Số thứ tự và sơ đồ bàn |

## Cách dùng

### Mở trực tiếp bằng Live Server (VS Code)
1. Cài extension **Live Server** trong VS Code
2. Click chuột phải vào `dashboard.html` → **Open with Live Server**

### Mở bằng Python server
```bash
cd "html-export"
python -m http.server 8080
# Mở http://localhost:8080/home.html
```

### Nhúng vào project chính
Nhúng `styles.css` vào `<head>` của project và copy các đoạn HTML cần thiết vào template của bạn.

## Hình ảnh
Các file HTML tham chiếu ảnh từ `../public/images/`. Đảm bảo thư mục `public/images/` nằm đúng vị trí so với thư mục `html-export/`.

## Điều hướng
Các trang đều có sidebar với links nối với nhau, click vào nav items để chuyển trang.
