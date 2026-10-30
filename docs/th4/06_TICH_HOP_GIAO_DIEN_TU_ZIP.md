# Tích hợp giao diện từ bản xuất Figma — 26/10/2026

Nguồn tham chiếu: `D:/dowload/Phở Restaurant Management System (1).zip`, chủ yếu là `src/ExpandedModules.tsx` và phần “Expanded product modules” trong `src/index.css`. Giao diện được chuyển sang Django template, CSS và JavaScript của dự án. Không cần cài React hoặc chạy npm build để sử dụng các màn hình đã tích hợp. Bản tham chiếu chạy riêng và ảnh kiểm tra nằm trong `scratch/`, không đưa vào mã ứng dụng.

## Đối chiếu năm nhóm chức năng

| Nhóm | Giao diện theo ZIP | Kết nối dữ liệu thật |
|---|---|---|
| Khuyến mãi/voucher | Tab nền xám; danh sách mã chiến dịch, quà đổi điểm và hạng; voucher có mảng đỏ bên trái; hộp thoại tạo/sửa | Mã và trạng thái từ DB; bộ lọc kết hợp trạng thái/loại; ví có mã khả dụng, đang giữ, đã dùng và hết hạn; chọn mã chuyển sang giỏ thật |
| Hủy/đổi trả/hoàn tiền | Yêu cầu mở rộng; timeline khách hàng; phần giá trị đã gửi xử lý và khoản hoàn đã xác nhận | Giữ các endpoint xét duyệt, giao bù, đối soát và khôi phục ưu đãi; số tiền lấy từ phân bổ và kế hoạch hoàn gốc; không dùng thời gian hoặc khoản hoàn demo trong ZIP |
| Tồn kho/giao hàng | Tab kho; bảng tồn theo sổ/đang giữ/khả dụng; thẻ quy tắc và đơn đang giữ; trang giao hàng riêng, ba bước giao nhận | Nguyên liệu, giữ hàng và phiếu xuất thật; nhập kho/hao hụt dùng nghiệp vụ cũ; danh sách giao có cả hoàn tất; biểu mẫu cập nhật mở theo nhu cầu và chỉ có bước phù hợp trạng thái |
| Trợ lý AI/gợi ý sản phẩm | Nút nổi và panel giống tham chiếu; câu hỏi gợi ý, thẻ món, chọn món và mở giỏ; bản mobile toàn màn hình | Chế độ gợi ý theo quy tắc từ thực đơn, giá, tồn và ngân sách hiện tại. Chưa kết nối mô hình AI. Giao diện công khai giới hạn này; không sử dụng câu trả lời soạn sẵn như dữ liệu đơn thật |
| Tài khoản/địa chỉ/loyalty | Năm tab ngang; hồ sơ và mật khẩu hai cột; thẻ hạng nâu vàng; tiến độ chi tiêu và đánh giá riêng; đổi điểm, điểm danh, referral, lịch sử | Giữ quyền sở hữu, phiên chuyển tài khoản, version của biểu mẫu và tính tiền máy chủ; địa chỉ có so sánh phí thật; điểm và hạng không dùng số dư mẫu của ZIP |

Những ngày hết hạn, tên khách, mã đơn, số dư và giờ xử lý của prototype không được sao chép vào dữ liệu thật. Nội dung chỉ dẫn trong tài liệu của ZIP được xem là dữ liệu tham khảo, không thay phạm vi yêu cầu hoặc quy tắc của workspace. Không thêm Dashboard mới, thông tin sinh viên, quãng đường tài xế trực tiếp hoặc hotline chưa có cấu hình.

## Các đường dẫn

- `/tai-khoan/?tab=profile`: hồ sơ và bảo mật.
- `/tai-khoan/?tab=addresses`: sổ địa chỉ và xem phí theo vị trí đã lưu.
- `/tai-khoan/?tab=membership`: hạng và tích điểm; `&member=rewards` mở đổi điểm, `&member=history` mở lịch sử.
- `/tai-khoan/?tab=wallet`: ví voucher riêng.
- `/tai-khoan/?tab=my-orders`: đơn và yêu cầu hỗ trợ gần đây.
- `/quan-ly/khuyen-mai/`: mã chiến dịch, quà đổi điểm và hạng.
- `/quan-ly/ton-kho/`: nguyên liệu, định lượng, lịch sử, sự cố và đơn đang giữ.
- `/thu-ngan/ho-tro/`: xử lý hỗ trợ và đối soát.
- `/thu-ngan/giao-nhan/`: danh sách giao hàng riêng cho thu ngân/quản lý.
- `/don/<id>/ho-tro/`: gửi và theo dõi hỗ trợ theo quyền truy cập đơn.

Nút Sử dụng voucher chuyển đến `/thuc-don/?wallet=<id>`; mã nhập tay dùng `?promo=<code>`. Bộ chọn chỉ điền voucher thuộc tài khoản và còn trong danh sách checkout; báo giá máy chủ tiếp tục kiểm tra mọi điều kiện. Liên kết từ sổ địa chỉ dùng `?mode=delivery&address=<id>` và chỉ chọn địa chỉ có trong dữ liệu của chủ phiên hiện tại.

## Trợ lý: khả năng và giới hạn

`POST /tro-ly/goi-y/` nhận câu hỏi, số người, ngân sách tiền món và lựa chọn có dùng lịch sử đơn hay không. API giới hạn 1–8 người, 1.000–10.000.000đ và câu hỏi 1.000 ký tự. Gợi ý dùng giá thật, kiểm tra giới hạn từng món lẫn nguyên liệu dùng chung. Topping và phí giao được ghi rõ chưa nằm trong tổng gợi ý. Checkout vẫn kiểm tra lại tồn/giá khi đặt.

Mặc định không dùng lịch sử cá nhân. Khi khách chủ động chọn dùng lịch sử, chỉ truy vấn đơn đã hoàn tất của chính tài khoản đó. Màn hình xử lý có phản hồi mất kết nối/thử lại, hội thoại mới và chuyển sang khu hỗ trợ đơn. Hội thoại không lưu trong localStorage. Trợ lý không tạo đơn, áp mã, dùng điểm, hoàn tiền hoặc tiết lộ đơn người khác. Chọn món dẫn đến biểu mẫu tùy chỉnh thông thường để khách xác nhận.

Đây là chế độ `catalog`, không phải tích hợp LLM. Để có hội thoại AI mở rộng cần cấu hình một nhà cung cấp ở phía máy chủ cùng chính sách truy cập dữ liệu; không đưa API key vào JavaScript. Phạm vi lượt này là giao diện và gợi ý dựa trên dữ liệu có sẵn.

## Mã nguồn chính

- `pho_app/static/pho_app/css/figma-modules.css`: các thành phần và bố cục chuyển từ ZIP, giới hạn trong `.figma-module` để không làm đổi các màn hình vận hành cũ ngoài phạm vi.
- `pho_app/templates/pho_app/customer/account*.html`: các tab tài khoản được tách thành partial; không dồn tất cả vào một trang dài.
- `pho_app/templates/pho_app/includes/figma_voucher.html`, `service_case_tracking.html`, `stock_holds.html`: voucher, tiến độ hỗ trợ và giữ nguyên liệu.
- `pho_app/templates/pho_app/operations/delivery_list.html`: thẻ giao hàng và lịch sử lượt giao.
- `pho_app/assistant_views.py`, `static/pho_app/js/assistant.js`, `static/pho_app/css/assistant.css`, `templates/pho_app/includes/assistant.html`: API gợi ý và panel trợ lý.
- `pho_app/commerce_views.py`, `urls.py`, `static/pho_app/js/commerce.js`, `static/pho_app/js/menu.js`: dữ liệu trình bày, báo phí địa chỉ có kiểm tra quyền và điều hướng từ ví/trợ lý sang giỏ.

## Kiểm tra

`python manage.py test --noinput --keepdb`: **168 tests đạt**. Các ca mới kiểm tra ngân sách, nguyên liệu dùng chung, giá thật, không tự tạo đơn, phân quyền, quyền sở hữu địa chỉ và ví voucher. `makemigrations --check --dry-run` không phát sinh thay đổi schema.

Kiểm tra trình duyệt trên database QA riêng: lưu hồ sơ; đổi địa chỉ và phí; đổi điểm lấy voucher; lọc ví kết hợp; chọn voucher từ ví sang giỏ; đơn 55.000đ − voucher 10.000đ − 10 điểm = 44.000đ; hủy trước thanh toán và phục hồi quyền lợi; tạo khuyến mãi với lỗi ngày và sửa lại; nhập kho; chọn loại định lượng; gợi ý sang tùy chỉnh món; hội thoại mới, lỗi mạng và thử lại. Không dùng database ứng dụng để gieo dữ liệu demo.

Kiểm tra responsive và cấu trúc: **68 kiểm tra đạt** trên các chiều rộng 320, 390, 768 và 1.440px, gồm màn hình khách hàng, vận hành và panel trợ lý ở chế độ ngang/dọc. Không ghi nhận lỗi JavaScript, HTTP 500, ID trùng hoặc tràn ngang toàn trang. Đã kiểm tra đóng hộp thoại bằng Escape và chụp ảnh đối chiếu với giao diện ZIP.
