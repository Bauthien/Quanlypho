# Tổng hợp sửa lỗi và kịch bản demo

**Dự án:** Quản lý quán phở — Phở Nhà

**Ngày tổng hợp:** 20/10/2026

**Phạm vi:** 8 mục trong ảnh phản hồi ban đầu và các bản sửa bổ sung cho logic kiểm tra nguyên liệu khi chọn món, tạo đơn và thanh toán.

## 1. Tổng quan các mục đã sửa

| Mã | Hạng mục | Kết quả sau khi sửa |
| --- | --- | --- |
| DEMO-01 | Định lượng món chính/topping | Mỗi định lượng chỉ gắn với đúng một món chính hoặc một topping; chặn dữ liệu gắn cả hai hoặc không gắn đối tượng nào. |
| DEMO-02 | Xóa nguyên liệu làm mất lịch sử | Chặn xóa nguyên liệu đang có định lượng hoặc lịch sử kho; nguyên liệu chưa được tham chiếu vẫn xóa được. |
| DEMO-03 | Sức chứa bàn | Máy chủ kiểm tra số nguyên từ 1 trở lên; có ràng buộc tại cơ sở dữ liệu. |
| DEMO-04 | Tồn kho/ngưỡng âm và số liệu không hợp lệ | Kiểm tra tại biểu mẫu, máy chủ và cơ sở dữ liệu; bổ sung kiểm tra số lượng nhập kho, độ chính xác và giới hạn số. |
| DEMO-05 | Xóa bàn làm mất liên kết lịch sử | Chặn xóa bàn đã được đơn hàng hoặc vé xếp hàng tham chiếu. |
| DEMO-06 | Trạng thái đơn trong trang đánh giá | Hiển thị đúng nhãn từ trường trạng thái đơn hàng. |
| DEMO-07 | Khả năng truy cập của tab tồn kho | Bổ sung vai trò tab/panel, trạng thái lựa chọn, liên kết ARIA và điều khiển bàn phím. |
| DEMO-08 | Điểm trung bình và số sao | Hiển thị phần sao lẻ theo điểm trung bình; 4,5/5 tương ứng phần tô màu 90%. |
| DEMO-09 | Nhầm đơn vị định lượng | Hiển thị đơn vị của nguyên liệu; bổ sung ví dụ `300 gram = 0.3 kg` khi nguyên liệu tính bằng kg. |
| DEMO-10 | Đặt món/thanh toán khi nguyên liệu không đủ | Kiểm tra trước khi tạo đơn, trước khi hiển thị thanh toán và khi xác nhận thanh toán. |
| DEMO-11 | Giỏ hàng cũ và số lượng có thể bán | Hiện “Tạm hết món”, giới hạn số lượng theo tồn; giỏ cũ thiếu hàng không gửi được. |
| DEMO-12 | Tổng hao phí của nhiều món và topping | Cộng tổng theo từng nguyên liệu cho toàn bộ giỏ hàng; không kiểm tra riêng lẻ từng dòng rồi bỏ sót tổng nhu cầu. |
| DEMO-13 | Thanh toán đồng thời, lặp lại và tính toàn vẹn | Khóa nguyên liệu khi xuất kho; chặn bán vượt tồn, tránh trừ kho lặp lại và hoàn tác khi không đủ hàng. |
| DEMO-14 | Phở chưa có định lượng | Tạm ngừng đặt món phở chưa được cấu hình định lượng; chặn cả thanh toán đơn chờ cũ. |

## 2. Chuẩn bị demo

Các số liệu dưới đây là dữ liệu minh họa. Chuẩn bị trên cơ sở dữ liệu demo/kiểm thử riêng nếu cần thay đổi số tồn, tạo đánh giá hoặc xóa dữ liệu.

### 2.1. Trang sử dụng

Mặc định máy chủ chạy tại `http://127.0.0.1:8000`.

| Trang | Đường dẫn | Vai trò |
| --- | --- | --- |
| Quản lý tồn kho và định lượng | `/quan-ly/ton-kho/` | Quản lý |
| Thêm nguyên liệu | `/quan-ly/ton-kho/them/` | Quản lý |
| Sơ đồ bàn & QR | `/so-do-ban/` | Thu ngân hoặc quản lý |
| Thêm bàn | `/quan-ly/ban/them/` | Quản lý |
| Danh sách đánh giá quản lý | `/quan-ly/danh-gia/` | Quản lý |
| Thực đơn khách hàng | `/thuc-don/` | Khách hàng hoặc khách vãng lai |
| Chi tiết đơn | `/thuc-don/don/<order_id>/` | Chủ đơn hoặc người có quyền |
| Thu ngân | `/thu-ngan/` | Thu ngân |
| Bếp | `/bep/` | Bếp hoặc người có quyền |

### 2.2. Bộ dữ liệu minh họa

| Đối tượng | Thiết lập |
| --- | --- |
| Bánh phở demo | Đơn vị `kg`; thay đổi tồn theo từng kịch bản. |
| Phở A | Nhóm `PHO`; dùng `0.20 kg` bánh phở/tô. |
| Phở B | Nhóm `PHO`; dùng `0.10 kg` bánh phở/tô. |
| Topping bánh thêm | Dùng `0.10 kg` bánh phở/phần. |
| Bàn DEMO-01 | Sức chứa 4 tô; chưa có đơn hoặc vé tham chiếu khi bắt đầu. |

Mỗi kịch bản độc lập: đưa dữ liệu về mức chuẩn bị của kịch bản đó trước khi thao tác. Nếu món có thêm định lượng thịt, nước dùng hoặc nguyên liệu khác, các nguyên liệu đó cũng phải đủ.

**Quy tắc cần nhớ:**

- Số tồn và định lượng phải cùng đơn vị; `0.20 kg = 200 gram`.
- Ngưỡng tối thiểu dùng để cảnh báo. Khả năng bán được quyết định bằng số tồn thực tế so với lượng nguyên liệu cần cho giỏ hàng.
- Đơn chờ thanh toán chưa trừ hoặc giữ nguyên liệu. Hệ thống kiểm tra lại tại bước xác nhận thanh toán.
- Khi thay đổi tồn kho ở trang quản lý, tải lại trang khách để nhận trạng thái thực đơn mới. Máy chủ vẫn kiểm tra lại nếu khách gửi giỏ hàng từ trang cũ.

## 3. Demo 8 mục sửa ban đầu

### DEMO-01 — Định lượng chỉ gắn với một đối tượng

**Đã sửa:** Bộ chọn món/topping vô hiệu hóa trường không được sử dụng. Máy chủ, kiểm tra model và ràng buộc cơ sở dữ liệu cùng bảo đảm mỗi công thức có đúng một đối tượng.

**Thao tác:**

1. Mở quản lý tồn kho, chuyển sang tab **Định lượng công thức món**.
2. Chọn loại **Món chính trong thực đơn**, chọn Phở A và nguyên liệu bánh phở, nhập `0.20`.
3. Lưu công thức.
4. Chuyển loại sang **Topping gọi thêm**, chọn topping bánh thêm, nhập `0.10` và lưu.
5. Chuyển qua lại giữa hai loại để kiểm tra trường được hiển thị.

**Kết quả mong đợi:**

- Công thức món chính chỉ gắn với Phở A; công thức topping chỉ gắn với topping bánh thêm.
- Trường đang ẩn bị vô hiệu hóa và không gửi kèm biểu mẫu.
- Gửi yêu cầu trực tiếp có cả hai đối tượng, không có đối tượng hoặc đối tượng không hợp lệ đều bị từ chối.
- Công thức có định lượng bằng 0, âm, không hữu hạn hoặc quá 2 chữ số thập phân bị từ chối.

**Kiểm thử đại diện:** `InventoryManagementTests.test_recipe_rejects_both_targets`, `test_database_rejects_ambiguous_recipe`.

### DEMO-02 — Bảo vệ nguyên liệu có định lượng hoặc lịch sử

**Đã sửa:** Quan hệ nguyên liệu của công thức và giao dịch kho chuyển sang chế độ bảo vệ khi xóa. Giao diện thông báo lý do thay vì xóa dây chuyền dữ liệu.

**Thao tác:**

1. Tạo nguyên liệu demo có tồn ban đầu `0`, chưa gắn công thức.
2. Xóa nguyên liệu này: thao tác phải thành công.
3. Tạo nguyên liệu demo thứ hai và gắn một công thức định lượng.
4. Thử xóa nguyên liệu thứ hai.
5. Với một nguyên liệu có lịch sử nhập hoặc xuất kho, thử xóa thêm lần nữa.

**Kết quả mong đợi:**

- Chỉ nguyên liệu không có tham chiếu mới được xóa.
- Nguyên liệu có công thức hoặc giao dịch bị chặn với thông báo “Không thể xóa…”.
- Công thức, lịch sử nhập/xuất và liên kết nguyên liệu được giữ nguyên.

**Lưu ý demo:** Nguyên liệu được tạo với tồn ban đầu lớn hơn 0 sẽ có giao dịch nhập kho ban đầu, vì vậy đã thuộc trường hợp có lịch sử.

**Kiểm thử đại diện:** `test_ingredient_with_recipe_cannot_be_deleted`, `test_ingredient_with_transactions_cannot_be_deleted`, `test_unused_ingredient_can_be_deleted`.

### DEMO-03 — Sức chứa bàn được kiểm tra tại máy chủ

**Đã sửa:** Dùng biểu mẫu kiểm tra số nguyên từ 1 đến `2147483647`; chặn tên bàn trùng không phân biệt hoa/thường. Cơ sở dữ liệu có ràng buộc sức chứa từ 1 trở lên.

**Thao tác:**

1. Mở trang thêm bàn, nhập tên `DEMO-01`, sức chứa `4` và lưu.
2. Thử tạo hoặc sửa bàn với sức chứa `0`, `-1` hoặc `1.5`.
3. Kiểm thử yêu cầu POST gửi trực tiếp chuỗi rỗng, chữ hoặc giá trị vượt giới hạn.
4. Thử tạo tên `demo-01` khi `DEMO-01` đã tồn tại.

**Kết quả mong đợi:**

- Sức chứa 4 được chấp nhận; dữ liệu không hợp lệ không được lưu.
- Yêu cầu POST sai không gây lỗi máy chủ 500.
- Biểu mẫu hiển thị lỗi và giữ dữ liệu người dùng đã nhập.
- Tên bàn trùng bị từ chối.

**Kiểm thử đại diện:** `test_table_create_edit_reject_invalid_capacity`, `test_table_form_validates_names_and_accepts_valid_capacity`.

### DEMO-04 — Chặn tồn/ngưỡng âm và số lượng kho không hợp lệ

**Đã sửa:** Kiểm tra số tồn, ngưỡng tối thiểu và lượng nhập; chặn số âm, `NaN`, `Infinity`, quá 2 chữ số thập phân và vượt giới hạn lưu trữ. Cơ sở dữ liệu chặn các lần ghi tồn/ngưỡng âm mới.

**Thao tác:**

1. Thêm nguyên liệu với tồn `1.25`, ngưỡng `0.20`: phải lưu được.
2. Thử thêm hoặc sửa tồn/ngưỡng thành `-1`.
3. Thử nhập thêm `0`, `-1`, `0.001` hoặc số vượt giới hạn.
4. Nhập thêm `0.01`: số tồn phải tăng đúng `0.01`.
5. Kiểm tra tab lịch sử kho.

**Kết quả mong đợi:**

- Dữ liệu sai không thay đổi số tồn và không tạo giao dịch kho.
- Dữ liệu hợp lệ được ghi nhận đúng số lượng; điều chỉnh tồn có lịch sử điều chỉnh tương ứng.
- Gửi trực tiếp yêu cầu sai vẫn bị chặn dù bỏ qua giới hạn của trình duyệt.

**Giới hạn số:** Các trường số lượng kho dùng tối đa 10 chữ số, trong đó tối đa 2 chữ số thập phân; giá trị không âm tối đa là `99999999.99`.

**Dữ liệu âm cũ:** Migration giữ số dư âm đã tồn tại để kiểm kê, không tự đưa về 0. Khi cập nhật theo tồn thực tế qua biểu mẫu quản lý, hệ thống ghi giao dịch điều chỉnh. Nhập thêm mà tổng vẫn âm bị từ chối và yêu cầu kiểm kê.

**Kiểm thử đại diện:** `test_ingredient_create_and_edit_reject_invalid_numbers`, `test_import_rejects_invalid_amounts_without_stock_changes`, `StockLimitTests.test_database_rejects_negative_stock_and_minimum_even_with_queryset_update`.

### DEMO-05 — Bảo vệ liên kết lịch sử của bàn

**Đã sửa:** Đơn hàng và vé xếp hàng bảo vệ bàn đang được tham chiếu khi có thao tác xóa.

**Thao tác:**

1. Tạo một bàn demo chưa có đơn/vé, rồi xóa: phải thành công.
2. Chuẩn bị một bàn đã có đơn hàng và thử xóa bàn.
3. Chuẩn bị một bàn được vé xếp hàng tham chiếu, rồi thử xóa.
4. Mở lại đơn hoặc vé liên quan.

**Kết quả mong đợi:**

- Bàn có tham chiếu không bị xóa; người dùng nhận thông báo rõ ràng.
- Đơn hàng/vé vẫn liên kết với đúng bàn.
- Quy tắc bảo vệ áp dụng cả lịch sử, không chỉ đơn đang phục vụ.

**Kiểm thử đại diện:** `test_table_with_orders_cannot_be_deleted`, `test_table_with_queue_history_cannot_be_deleted`, `test_unused_table_can_be_deleted`.

### DEMO-06 — Trạng thái đơn trong đánh giá

**Đã sửa:** Template sử dụng `get_order_status_display` thay cho phương thức không tồn tại `get_status_display`.

**Thao tác:**

1. Chuẩn bị một đánh giá có gắn đơn hàng.
2. Đưa đơn sang trạng thái `COOKING` bằng luồng xử lý phù hợp.
3. Mở danh sách đánh giá quản lý.

**Kết quả mong đợi:** Phần thông tin đơn hiển thị loại đơn và nhãn **“Bếp đang làm”**; không còn phần trạng thái bị trống.

**Kiểm thử đại diện:** `test_reviews_show_order_status_and_fractional_average`.

### DEMO-07 — Tab kho hỗ trợ bàn phím và công nghệ hỗ trợ

**Đã sửa:** Bổ sung `role="tab"`, `role="tabpanel"`, `aria-selected`, `aria-controls`, `aria-labelledby`, quản lý `tabindex` và điều khiển bàn phím.

**Thao tác:**

1. Mở quản lý tồn kho, dùng phím `Tab` đưa tiêu điểm đến tab đang chọn.
2. Nhấn `→` để sang tab kế tiếp, `←` để quay lại.
3. Nhấn `End` đến tab cuối; nhấn `Home` về tab đầu.
4. Tại tab cuối, nhấn `→` để kiểm tra quay vòng về tab đầu.
5. Thử chọn các tab bằng chuột.

**Kết quả mong đợi:**

- Chỉ một panel hiển thị tại một thời điểm.
- Tab đang chọn có `aria-selected="true"` và nằm trong thứ tự tab bàn phím.
- Tiêu điểm đi cùng tab được chọn; trạng thái hiển thị và ARIA đồng nhất.

**Kiểm thử đại diện:** `test_inventory_tabs_have_accessible_relationships`; kiểm tra trình duyệt với phím mũi tên, Home/End và chuyển panel.

### DEMO-08 — Điểm trung bình khớp với sao hiển thị

**Đã sửa:** Phần sao trung bình được tô theo tỷ lệ điểm trên 5; có nhãn văn bản hỗ trợ đọc màn hình.

**Thao tác:**

1. Trong bộ dữ liệu demo riêng, chuẩn bị đúng hai đánh giá có điểm 4 và 5.
2. Mở danh sách đánh giá quản lý.
3. Quan sát điểm trung bình và hàng sao.

**Kết quả mong đợi:**

- Điểm trung bình là **4,5** theo định dạng tiếng Việt.
- Phần sao tô màu chiếm **90%**, tương ứng 4 sao rưỡi.
- Nhãn hỗ trợ là **“4,5 trên 5 sao”**.
- Khi chưa có đánh giá: điểm trung bình 0,0 và phần sao tô màu 0%.

**Kiểm thử đại diện:** `test_reviews_show_order_status_and_fractional_average`; trình duyệt kiểm tra tỷ lệ chiều rộng phần sao bằng 0,9.

## 4. Demo các bản sửa bổ sung về tồn kho và thanh toán

### DEMO-09 — Hướng dẫn nhập đúng đơn vị

**Đã sửa:** Ô định lượng hiển thị đơn vị của nguyên liệu được chọn. Khi đơn vị là kg, có ví dụ chuyển đổi gram sang kg.

**Thao tác:**

1. Mở biểu mẫu thêm định lượng.
2. Chọn nguyên liệu có đơn vị `kg`.
3. Quan sát hướng dẫn bên dưới ô số lượng.
4. Với một tô cần 300 gram, nhập `0.30` thay vì `300`.

**Kết quả mong đợi:** Hiển thị **“Đơn vị định lượng: kg. Ví dụ: 300 gram = 0.3 kg.”**; công thức dùng `0.30 kg` cho một đơn vị bán.

Hệ thống không tự chuyển một công thức đã lưu là `300 kg` thành `0.30 kg`, vì cần xác nhận định lượng thực tế.

### DEMO-10 — Còn 0,10 kg nhưng món cần 0,20 kg

**Đã sửa:** Thực đơn, bước tạo đơn và xác nhận thanh toán dùng chung logic tính nguyên liệu. Trang đơn chờ kiểm tra lại trước khi hiển thị hướng dẫn thanh toán.

#### A. Chặn đặt đơn mới

**Chuẩn bị:** Bánh phở tồn `0.10 kg`; Phở A cần `0.20 kg/tô`.

**Thao tác:**

1. Tải lại thực đơn khách hàng.
2. Quan sát Phở A.
3. Kiểm thử gửi trực tiếp một giỏ có 1 Phở A, lần lượt chọn tiền mặt và VietQR.

**Kết quả mong đợi:**

- Phở A hiện **“Tạm hết món”**, không chọn được.
- Yêu cầu trực tiếp bị từ chối với thông tin cần `0.20 kg`, còn `0.10 kg`.
- Không tạo đơn, không ghi xuất kho, không đổi bàn thành có khách.
- Áp dụng cho khách đăng nhập, khách vãng lai, đơn giao hàng và đơn từ hàng đợi.
- Khi đơn hàng đợi bị từ chối, vé đang `CALLED` vẫn được giữ ở trạng thái đó.

#### B. Chặn thanh toán đơn chờ đã tạo trước đó

**Chuẩn bị:** Đặt tồn `0.40 kg`, tạo một đơn chờ có 1 Phở A; sau đó cập nhật tồn thực tế của dữ liệu demo xuống `0.10 kg`.

**Thao tác:**

1. Tải lại trang chi tiết đơn chờ.
2. Thử xác nhận tiền mặt ở thu ngân/quản lý hoặc gọi mô phỏng VietQR trực tiếp trong môi trường phát triển.

**Kết quả mong đợi:**

- Trang đơn hiện **“Tạm thời chưa thể thanh toán”** và lý do thiếu nguyên liệu.
- Không hiển thị mã QR hoặc nút mô phỏng thanh toán; không mời khách thanh toán tiền mặt.
- Xác nhận thanh toán bị từ chối; đơn không được chuyển xuống bếp.
- Số tồn và các nguyên liệu khác không bị trừ dở dang.

Với webhook chuyển khoản thật đã có chữ ký hợp lệ nhưng đơn thiếu kho, API trả HTTP `409`, kèm `requires_reconciliation: true` để yêu cầu đối soát. Đây không phải chức năng tự hoàn tiền hoặc hủy một khoản chuyển tiền bên ngoài ứng dụng.

#### C. Đủ đúng một phần

**Chuẩn bị:** Bánh phở tồn `0.20 kg`; một Phở A cần đúng `0.20 kg`.

**Kết quả mong đợi:** Tạo được đơn chờ; tồn chưa bị trừ tại bước tạo đơn. Khi thanh toán được xác nhận, tồn về đúng `0.00 kg`. Tải lại thực đơn sẽ không đặt thêm được Phở A.

**Kiểm thử đại diện:** Các ca trong `CheckoutStockTests`, `StockLimitTests.test_exact_stock_can_be_sold_to_zero`, `test_simulated_qr_payment_shows_shortage_and_can_retry_after_restock`.

### DEMO-11 — Giỏ hàng cũ và giới hạn số lượng

**Đã sửa:** Không chỉ dựa vào trạng thái nút trên thực đơn. Giỏ lưu trong trình duyệt cũng được đối chiếu với khả năng bán mới nhất khi tải trang; máy chủ tiếp tục kiểm tra lúc gửi đơn.

**Thao tác:**

1. Với tồn `0.40 kg`, thêm Phở A vào giỏ nhưng chưa đặt đơn.
2. Tại quản lý, đổi tồn demo thành `0.10 kg`.
3. Tải lại thực đơn, mở giỏ hàng đang lưu.
4. Tiếp tục demo với tồn `0.20 kg`, tải lại thực đơn và thử tăng số lượng Phở A lên 2.
5. Thử thêm Phở A lần nữa dưới một ghi chú/biến thể khác.

**Kết quả mong đợi:**

- Ở mức `0.10 kg`, giỏ vẫn hiển thị món để khách chỉnh sửa nhưng nút đặt món bị khóa và có thông báo.
- Ở mức `0.20 kg`, chỉ có thể thêm tổng cộng 1 Phở A; tách thành nhiều biến thể không vượt được giới hạn đó.
- Khách gửi dữ liệu từ trang chưa tải lại vẫn bị máy chủ chặn nếu tồn đã không đủ.
- Món khác còn đủ nguyên liệu vẫn có thể chọn.

Giới hạn hiển thị của từng món là ảnh chụp tồn tại lúc tải trang. Kiểm tra tổng giỏ ở máy chủ là bước quyết định cuối cùng khi nhiều món cùng dùng một nguyên liệu.

### DEMO-12 — Cộng tổng nguyên liệu của món và topping

**Đã sửa:** Gom nhu cầu theo từng nguyên liệu trước khi kiểm tra và xuất kho. Số lượng topping đã lưu trong đơn là tổng số phần, không nhân thêm số tô một lần nữa.

#### A. Hai món dùng chung bánh phở

**Chuẩn bị:** Tồn `0.20 kg`; Phở A dùng `0.20 kg`, Phở B dùng `0.10 kg`.

**Thao tác:** Gửi giỏ gồm 1 Phở A và 1 Phở B.

**Kết quả mong đợi:** Chặn đặt đơn vì tổng cần `0.30 kg`, dù mỗi món xét riêng đều có thể đủ.

#### B. Món và topping dùng chung nguyên liệu

**Chuẩn bị:** Tồn `1.00 kg`; Phở A dùng `0.20 kg/tô`; topping bánh thêm dùng `0.10 kg/phần`.

**Thao tác:** Đặt 2 Phở A, mỗi tô kèm 1 phần topping bánh thêm, rồi xác nhận thanh toán.

**Phép tính:**

```text
Món chính: 2 × 0.20 kg = 0.40 kg
Topping:   2 × 0.10 kg = 0.20 kg
Tổng:                    0.60 kg
Tồn còn lại: 1.00 − 0.60 = 0.40 kg
```

**Kết quả mong đợi:** Tồn còn `0.40 kg`; lịch sử xuất phản ánh đúng hao phí món chính và topping, không trừ thiếu hoặc nhân topping thêm một lần.

**Kiểm thử đại diện:** `test_total_requirements_include_different_dishes_using_same_ingredient`, `test_total_requirements_include_toppings`, `test_paid_order_deducts_main_and_topping_recipes_once`.

### DEMO-13 — Đồng thời, xác nhận lặp và hoàn tác

**Đã sửa:** Kiểm tra tổng nhu cầu trước khi ghi xuất; khóa nguyên liệu theo cùng thứ tự khi xác nhận thanh toán. Việc lưu trạng thái thanh toán và xuất kho nằm trong giao dịch có thể hoàn tác.

#### A. Hai đơn tranh phần tồn cuối

**Chuẩn bị:** Tồn `0.20 kg`; có hai đơn chờ, mỗi đơn cần `0.20 kg`.

**Thao tác:** Xác nhận thanh toán hai đơn đồng thời; ưu tiên dùng kiểm thử tự động bên dưới để tái hiện chính xác.

**Kết quả mong đợi:** Chỉ một đơn thanh toán thành công và xuất kho; đơn còn lại nhận lỗi thiếu kho. Tồn kết thúc ở 0, không xuống âm.

```powershell
python manage.py test pho_app.test_stock_limits.ConcurrentStockLimitTests --noinput
```

#### B. Xác nhận lại cùng một khoản thanh toán

**Thao tác:** Sau khi một đơn đã được xác nhận thành công, gửi lại cùng thao tác hoặc cùng callback hợp lệ.

**Kết quả mong đợi:** Không trừ kho hoặc tạo giao dịch xuất lần thứ hai. Callback thành công lặp lại được nhận diện là trùng.

```powershell
python manage.py test pho_app.test_orders.OrderManagementTests.test_repeated_cash_confirmation_across_screens_deducts_inventory_once --noinput
python manage.py test pho_app.test_orders.OrderManagementTests.test_vietqr_verified_callback_is_still_required_and_idempotent --noinput
```

#### C. Một nguyên liệu thiếu trong đơn có nhiều nguyên liệu

**Chuẩn bị:** Thịt bò đủ, nước dùng đủ nhưng bánh phở không đủ.

**Kết quả mong đợi:** Toàn bộ thao tác xác nhận bị từ chối; thịt bò, nước dùng, bánh phở và lịch sử xuất không bị thay đổi dở dang. Lưu trực tiếp model để đổi trạng thái sang đã thanh toán cũng phải tuân theo quy tắc này.

**Kiểm thử đại diện:** `StockLimitTests.test_shortage_in_one_ingredient_leaves_all_other_ingredients_untouched`, `test_direct_paid_save_rolls_back_payment_when_stock_is_short`.

### DEMO-14 — Phở chưa cấu hình định lượng

**Đã sửa:** Món thuộc nhóm `PHO` nhưng chưa có công thức định lượng sẽ không được xem là món bán không giới hạn.

**Thao tác:**

1. Tạo một món phở demo còn kinh doanh nhưng chưa có định lượng.
2. Tải lại thực đơn khách hàng.
3. Thử gửi trực tiếp giỏ có món đó.
4. Với đơn chờ cũ chứa món đó, thử xác nhận thanh toán.
5. Thêm công thức hợp lệ, bảo đảm nguyên liệu đủ rồi tải lại thực đơn.

**Kết quả mong đợi:**

- Trước khi có định lượng: hiện “Tạm hết món”; đặt đơn/thanh toán bị từ chối với thông báo món chưa thể phục vụ.
- Sau khi có công thức và đủ nguyên liệu: có thể đặt món theo giới hạn tồn thực tế.
- Quy tắc bắt buộc công thức này áp dụng cho nhóm phở. Đồ uống và topping chưa có công thức vẫn giữ cách xử lý hiện tại; nếu đã có công thức thì lượng tiêu hao được kiểm tra và tính vào tổng giỏ.

**Kiểm thử đại diện:** `test_pho_without_recipe_cannot_be_ordered`, `test_missing_recipe_cannot_bypass_payment_for_old_pending_order`, `test_menu_exposes_actual_sellable_quantities_and_blocks_missing_recipe`.

## 5. Kết quả kiểm tra đã thực hiện

### 5.1. Kiểm thử tự động

Lần chạy đầy đủ gần nhất sau các bản sửa:

```text
Ran 122 tests in 68.608s
OK
System check identified no issues (0 silenced).
```

Đây là tổng số kiểm thử của dự án tại thời điểm tổng hợp, gồm kiểm thử cũ và các ca bổ sung.

**Chạy lại toàn bộ:**

```powershell
Set-Location 'C:\Users\HP\Quanlypho'
python manage.py check
python manage.py test --noinput
```

**Chạy riêng các nhóm liên quan:**

```powershell
python manage.py test pho_app.test_inventory_management --noinput
python manage.py test pho_app.test_stock_limits --noinput
python manage.py test pho_app.test_checkout_stock --noinput
```

| File kiểm thử | Số ca | Phạm vi chính |
| --- | --- | --- |
| `pho_app/test_inventory_management.py` | 23 | Định lượng, biểu mẫu kho, bảo vệ lịch sử, bàn, đánh giá, ngữ nghĩa tab. |
| `pho_app/test_stock_limits.py` | 13 | Thiếu kho khi thanh toán, hoàn tác, đồng thời, ràng buộc cơ sở dữ liệu và số âm cũ. |
| `pho_app/test_checkout_stock.py` | 12 | Chặn từ bước tạo đơn, nhiều hình thức đặt món, giỏ tổng hợp, QR của đơn chờ và món thiếu công thức. |

Các lệnh test chạy trên cơ sở dữ liệu kiểm thử riêng do Django tạo. Các kết quả trên không có nghĩa là mọi kịch bản demo thủ công đã được thực hiện trên dữ liệu kinh doanh.

### 5.2. Kiểm tra trình duyệt và dữ liệu thực tế

Đã kiểm tra:

- Tab tồn kho: bàn phím, tiêu điểm, trạng thái ARIA và panel hiển thị.
- Chuyển loại định lượng: dữ liệu gửi chỉ có một đối tượng.
- Điểm 4,5: phần sao tô màu 90% và nhãn hỗ trợ tương ứng.
- Biểu mẫu bàn/nguyên liệu ở độ rộng 390 px và 1440 px.
- Hướng dẫn đơn vị kg và ví dụ chuyển đổi 300 gram.
- Món thiếu kho bị vô hiệu hóa, giỏ lưu cũ không gửi được.
- Giới hạn một phần bán được không bị vượt bằng cách thêm biến thể thứ hai.
- Đơn chờ thiếu kho không hiện QR hoặc nút mô phỏng thanh toán.

Đã đối chiếu với dữ liệu thực tế tại thời điểm kiểm tra: **Bánh phở tươi còn 0.10 kg**, **Phở Bò Tái cần 0.20 kg/tô**. Yêu cầu đặt một tô bị từ chối; không tạo thêm đơn hoặc giao dịch xuất. Các thử ghi trong lần đối chiếu được bọc trong giao dịch luôn hoàn tác.

## 6. Migration và mã nguồn liên quan

### 6.1. Migration

| Migration | Nội dung |
| --- | --- |
| `0013_protect_inventory_and_table_history` | Bảo vệ liên kết nguyên liệu/bàn; ràng buộc một đối tượng cho công thức; sức chứa bàn từ 1. |
| `0014_prevent_negative_inventory` | Ràng buộc tồn kho/ngưỡng không âm; giữ số dư âm cũ để đối chiếu, chặn các lần ghi âm mới. |

Hai migration đã được áp dụng vào cơ sở dữ liệu cục bộ trong đợt sửa. Khi đưa mã sang một cơ sở dữ liệu khác, áp dụng các migration còn thiếu bằng:

```powershell
python manage.py migrate --noinput
```

### 6.2. Các phần mã chính

| Thành phần | Vai trò |
| --- | --- |
| `pho_app/models.py` | Ràng buộc dữ liệu, quan hệ bảo vệ khi xóa, giao dịch khi lưu thanh toán. |
| `pho_app/forms.py` | Kiểm tra dữ liệu bàn, nguyên liệu, nhập kho và định lượng. |
| `pho_app/services.py` | Tính hao phí, tổng nhu cầu, kiểm tra tồn và giới hạn số lượng có thể bán dùng chung. |
| `pho_app/signals.py` | Kiểm tra và xuất kho khi đơn chuyển sang đã thanh toán. |
| `pho_app/views.py` | Tích hợp kiểm tra tại tạo đơn, trang thanh toán, thu ngân, quản lý và VietQR. |
| `pho_app/static/pho_app/js/menu.js` | Trạng thái hết món, giỏ cũ, giới hạn số lượng và khóa nút đặt món. |
| `pho_app/templates/pho_app/customer/order_detail.html` | Thông báo thiếu hàng và ẩn phần thanh toán khi không đủ nguyên liệu. |
| Các template quản lý kho/bàn/đánh giá | Lỗi biểu mẫu, hướng dẫn đơn vị, tab hỗ trợ truy cập, trạng thái đơn và sao lẻ. |
| `pho_app/management/commands/seed_demo_data.py` | Điều chỉnh thứ tự xóa dữ liệu demo: xóa vé xếp hàng trước bàn để tương thích quan hệ bảo vệ mới. |

## 7. Thứ tự trình diễn gợi ý

1. **Định lượng và đơn vị:** DEMO-01, DEMO-09.
2. **Tồn kho và bảo vệ dữ liệu:** DEMO-02, DEMO-04.
3. **Bàn:** DEMO-03, DEMO-05.
4. **Đánh giá và khả năng truy cập:** DEMO-06, DEMO-07, DEMO-08.
5. **Tình huống chính 0,10 kg:** DEMO-10, DEMO-11.
6. **Giỏ nhiều món/topping và món thiếu công thức:** DEMO-12, DEMO-14.
7. **Chạy kiểm thử đồng thời và xác nhận lặp:** DEMO-13, sau đó hiển thị kết quả bộ kiểm thử.
