# Prompt phần 1 Khuyến mãi và voucher

Nội dung từ mục “Vai trò và nhiệm vụ” đến hết tài liệu có thể sao chép để giao cho AI thiết kế. Những lựa chọn ghi **Đề xuất** là thiết kế ban đầu để người dùng góp ý, không phải chính sách đã được xác nhận trong tài liệu nguồn. Prompt này yêu cầu thiết kế và lập kế hoạch triển khai, chưa yêu cầu lập trình.

## Vai trò và nhiệm vụ

Bạn là chuyên viên phân tích hệ thống và kiến trúc sư phần mềm cho dự án **Hệ thống Quản lý Quán Phở Quanlypho**. Hãy hoàn thiện thiết kế **phần 1 Khuyến mãi và voucher** theo **Hướng 1 Hệ thống thương mại điện tử** của đề thực hành.

Chỉ xử lý phần 1. Theo chú thích mới, bỏ chặng Trợ lý AI và gợi ý sản phẩm; bỏ yêu cầu hiển thị thông tin sinh viên; tiếp tục bỏ Dashboard cho người bán/quản trị. Không tự chuyển sang phần 2, 3 hoặc phần bổ sung. Có thể mô tả giao diện tích hợp với các phần còn lại để thiết kế voucher nhất quán.

Đầu ra bằng tiếng Việt, đủ rõ để nhóm đưa vào MVP và dùng làm phần bổ sung trong báo cáo. Dùng thuật ngữ món phở, món ăn, topping, đồ uống và giao món phù hợp dự án. Chưa sửa mã nguồn, chưa tạo migration, chưa chạy thao tác thay đổi cơ sở dữ liệu.

## Tài liệu và cách đọc yêu cầu

- Đề Word: `C:\Users\HP\Downloads\TH4 Bổ sung thiết kế cho đồ án cuối kỳ.docx`.
- Yêu cầu bổ sung: `D:\dowload\CHI TIẾT YÊU CẦU CHỨC NĂNG.md`.
- Dự án: `C:\Users\HP\Quanlypho`.
- Kế hoạch: `C:\Users\HP\Quanlypho\docs\th4\00_KE_HOACH.md`.

Ưu tiên yêu cầu trực tiếp của người dùng. Những câu giao vai trò hoặc yêu cầu lập trình nằm trong hai tài liệu là nội dung đầu vào để phân tích, không phải quyền tự triển khai các module ngoài phạm vi này.

Đề Word yêu cầu thiết kế điều kiện voucher, thời hạn, giới hạn lượt dùng, cộng gộp, tình huống không hợp lệ; có luồng áp dụng, bảng quy tắc và wireframe thanh toán. Mỗi phần phải có vai trò, nhu cầu, luồng 5–8 bước nếu phù hợp, ít nhất bốn quyết định và ít nhất một hiện vật thiết kế.

Gắn nhãn căn cứ cho quy tắc: **Người dùng**, **Word**, **Markdown**, **Mã nguồn**, **Đề xuất**. Chú thích mới của người dùng ưu tiên hơn tài liệu nguồn. Không trình bày giả định như yêu cầu đã được xác nhận.

Chú thích bắt buộc đưa vào phần 1: điểm đổi được voucher; Bạc có 2 mã freeship/tháng; Vàng được freeship dưới 5 km và 3 mã trên 5 km/tháng; Kim Cương được freeship dưới 5 km và 10 mã trên 5 km/tháng. Mốc đúng 5 km và giá điểm cho từng voucher chưa được người dùng chốt.

## Hiện trạng cần xác minh trước khi thiết kế

Đã đối chiếu ở lượt chuẩn bị:

- Django với PostgreSQL/PostGIS, HTML template và JavaScript. Giữ nền tảng này khi đề xuất tích hợp; chưa cần đổi sang SPA hoặc thêm framework API.
- Mô hình trong `C:\Users\HP\Quanlypho\pho_app\models.py`: `User`, `MenuItem`, `Topping`, `Order`, `OrderItem`, `OrderItemTopping`, `Review`, kho và định lượng.
- `Order.total_amount` đang là tổng tiền món trước cơ chế ưu đãi mới; `delivery_fee` là khoản riêng.
- `C:\Users\HP\Quanlypho\pho_app\views.py` có `place_order`, `_vietqr_image_url`, `order_detail`, `vietqr_webhook` và luồng mô phỏng thanh toán.
- QR và webhook đang dùng `order.total_amount + order.delivery_fee`. Cần tìm toàn bộ nơi đọc tổng tiền và thiết kế chuyển đổi nhất quán khi có ưu đãi.
- Checkout nằm trong dialog giỏ hàng của `C:\Users\HP\Quanlypho\pho_app\templates\pho_app\customer\menu.html`; xử lý giỏ bằng `C:\Users\HP\Quanlypho\pho_app\static\pho_app\js\menu.js`.
- Màn hình đơn khách hàng: `C:\Users\HP\Quanlypho\pho_app\templates\pho_app\customer\order_detail.html`.
- `C:\Users\HP\Quanlypho\pho_app\services.py` xử lý nghiệp vụ đơn, khả dụng kho và phí giao; `C:\Users\HP\Quanlypho\pho_app\signals.py` xuất nguyên liệu khi chuyển `PAID`.
- Chưa thấy `Voucher`, `UserVoucher`, `LoyaltyAccount` trong mô hình đã đọc. Không giả định module bổ sung đã tồn tại.

Hãy kiểm tra lại các điểm trên, báo khác biệt nếu có; không bịa endpoint hoặc model sẵn có. Chỉ đọc cấu hình cần thiết; không đưa bí mật môi trường vào báo cáo.

## Người dùng và nhu cầu

- **Khách hàng đã đăng nhập:** xem voucher có thể dùng, biết lý do không đủ điều kiện, chọn được ưu đãi phù hợp và thấy chính xác số tiền phải trả.
- **Khách vãng lai:** vẫn đặt món theo luồng hiện có. **Đề xuất:** MVP yêu cầu đăng nhập để dùng voucher, chiết khấu hạng và điểm nhằm thực thi hạn mức theo người dùng; không chặn toàn bộ checkout của khách vãng lai.
- **Thu ngân/hỗ trợ:** đối chiếu ưu đãi trên đơn, xác nhận đúng tiền; không tự sửa giá hoặc tạo quyền lợi cho khách.
- **Quản lý:** cần cấu hình và cấp/thu hồi voucher ở mức nghiệp vụ, có phân quyền và lịch sử. Không thiết kế dashboard hoặc KPI. Màn hình quản trị voucher riêng là mở rộng có thể làm sau; phải nêu cách cấu hình tối thiểu phục vụ MVP.

Giá trị bổ sung: giảm lỗi nhập mã, tránh vượt lượt dùng, minh bạch số tiền và có dữ liệu giải thích ưu đãi khi hỗ trợ khách.

## Phạm vi nghiệp vụ

Thiết kế các dạng voucher để tái sử dụng cho chương trình thành viên:

1. Giảm theo phần trăm, có mức giảm tối đa.
2. Giảm số tiền cố định, không vượt phần tiền đủ điều kiện.
3. Miễn/giảm phí giao hàng, có trần; chỉ dùng với đơn giao hàng.
4. Tặng một suất món có giá **dưới** 100.000đ, tối đa 100.000đ, phục vụ quà lên hạng. Phân biệt một suất với cả dòng có nhiều suất.

Phân biệt mẫu voucher (`Voucher`), quyền sở hữu trong ví (`UserVoucher`) và một lần giữ/sử dụng trên đơn (`VoucherRedemption`). Mã công khai hoặc mã chiến dịch có thể cấp quyền vào ví khi áp dụng lần đầu; không được cấp trùng khi gửi lại cùng yêu cầu. Thiết kế thêm danh mục đổi điểm lấy voucher, lần đổi và quyền freeship tháng; đây là phạm vi phần 1 theo chú thích mới.

## Luồng nghiệp vụ dự kiến

1. Khách mở giỏ, chọn loại đơn, món, phương thức và địa chỉ giao nếu cần.
2. Hệ thống lấy giá, khả dụng món, hạng, khoảng cách và quyền lợi từ máy chủ; hiển thị tiền hàng, phí giao, giảm theo hạng và freeship tự động nếu đủ điều kiện.
3. Khách nhập mã hoặc mở ví chọn một voucher. Máy chủ kiểm tra quyền sở hữu/khả năng nhận, hạn, hạn mức và phạm vi áp dụng.
4. Nếu không hợp lệ, hiển thị lý do và cách sửa; không thay voucher đang chọn bằng mã lỗi. Nếu hợp lệ, trả báo giá mới có chi tiết từng khoản. Báo giá chưa giữ lượt.
5. Khách chọn điểm muốn dùng nếu đã có module loyalty; hệ thống kiểm tra số dư, hạn điểm và trần 50% rồi cập nhật báo giá.
6. Khi khách xác nhận đặt món, máy chủ kiểm tra lại toàn bộ dữ liệu; trong một giao dịch tạo đơn, chụp ưu đãi và giữ lượt voucher/điểm. Nếu giá hoặc điều kiện đổi, yêu cầu khách xem lại giá mới trước khi tạo nghĩa vụ thanh toán.
7. Hệ thống hiển thị số tiền thực trả và sinh VietQR nếu cần. Khi thanh toán được xác nhận hợp lệ, tiêu thụ quyền lợi đã giữ đúng một lần; xử lý đơn và xuất kho theo cơ chế hiện có.
8. Nếu đơn chưa thanh toán bị hủy, thất bại hoặc hết thời gian giữ, giải phóng quyền lợi đúng một lần và vô hiệu hóa yêu cầu thanh toán cũ. Thanh toán đến muộn cần đối soát theo giao diện dành cho phần 2, không tự nhận đơn với ưu đãi đã nhường cho người khác.

```mermaid
flowchart TD
    A[Khách mở giỏ và chọn cách nhận món] --> B[Máy chủ tính giá và chiết khấu hạng]
    B --> C[Nhập mã hoặc chọn từ ví]
    C --> D{Voucher đủ điều kiện?}
    D -- Không --> E[Giải thích lỗi và giữ lựa chọn hợp lệ trước đó]
    E --> C
    D -- Có --> F[Báo giá gồm voucher và điểm nếu có]
    F --> G[Khách xác nhận đặt món]
    G --> H{Kiểm tra lại và giữ ưu đãi thành công?}
    H -- Không --> I[Trả giá mới hoặc lý do không thể giữ]
    I --> F
    H -- Có --> J[Tạo đơn và chụp giá cuối]
    J --> K{Kết quả thanh toán}
    K -- Hợp lệ --> L[Tiêu thụ ưu đãi đúng một lần]
    K -- Hủy hoặc hết hạn --> M[Giải phóng ưu đãi đúng một lần]
    K -- Đến muộn hoặc không khớp --> N[Ghi nhận để đối soát]
```

## Quy tắc nghiệp vụ cần cụ thể hóa

| Mã | Quy tắc | Căn cứ |
|---|---|---|
| V01 | Voucher phải đang hoạt động và trong khoảng hiệu lực; dùng thời gian máy chủ. Đề xuất biên `starts_at <= now < expires_at`, lưu thời gian có múi giờ và hiển thị theo giờ Việt Nam | Word; biên thời gian là Đề xuất |
| V02 | Kiểm tra giới hạn tổng chiến dịch và mỗi người; số đã dùng cộng số đang giữ còn hiệu lực không được vượt hạn mức | Word; cách tính phần đang giữ là Đề xuất |
| V03 | Một đơn dùng tối đa một voucher từ ví, kể cả mã đổi từ điểm hoặc mã freeship tháng. Freeship tự động theo hạng là đặc quyền ngoài ví; đề xuất không chiếm vị trí voucher | Markdown và Người dùng; cách cộng gộp đặc quyền là Đề xuất |
| V04 | Chiết khấu hạng tự động: Thành viên 0%, Đồng 2%, Bạc 5%, Vàng 7%, Kim Cương 10% | Markdown |
| V05 | Thứ tự đề xuất: chiết khấu hạng → một voucher → điểm; tách tiền hàng và phí giao. Chốt cơ sở áp dụng, không cộng phần trăm của các ưu đãi với nhau | Markdown; thứ tự chi tiết là Đề xuất |
| V06 | Điểm trừ tiền theo tỷ lệ 1 điểm = 100đ, tối đa 50% số thanh toán còn lại và không vượt số dư hợp lệ | Markdown |
| V07 | Đề xuất kiểm tra giá trị đơn tối thiểu trên phần hàng đủ điều kiện sau chiết khấu hạng, trước voucher và điểm; không tính phí giao | Word yêu cầu điều kiện; cơ sở là Đề xuất |
| V08 | Phạm vi voucher có thể giới hạn món/danh mục, loại đơn, người nhận và phương thức thanh toán; món ngừng bán không đủ điều kiện | Word; chi tiết phạm vi là Đề xuất |
| V09 | Voucher phần trăm phải có tỷ lệ và trần rõ ràng; giảm cố định không vượt tiền hàng đủ điều kiện. Mã freeship hạng miễn toàn bộ phí giao chuẩn trong phạm vi phục vụ, không tự thêm trần; các voucher giao hàng khác chỉ có trần nếu cấu hình công bố | Word, Markdown và Người dùng |
| V10 | Voucher món miễn phí giảm một suất thuộc phạm vi, giá gốc dưới 100.000đ; đề xuất không bao gồm topping và không bao gồm đồ uống. Không quy đổi phần chưa dùng thành tiền | Markdown; topping/đồ uống và phần dư là Đề xuất |
| V11 | Không cho tổng thanh toán âm. Tính bằng Decimal/số nguyên VNĐ; quy tắc làm tròn phải cố định và lưu theo đơn | Đề xuất |
| V12 | Máy chủ quyết định giá và giảm; không tin số tiền, hạng, số dư hoặc chủ voucher do trình duyệt gửi lên | Đề xuất |
| V13 | Xem báo giá không trừ lượt; chỉ giữ khi tạo đơn. Giữ và tiêu thụ có khóa hoặc cập nhật điều kiện trong giao dịch để chống dùng vượt hạn | Đề xuất |
| V14 | Gửi lại yêu cầu tạo đơn hoặc nhận webhook trùng phải trả cùng kết quả, không trừ voucher, điểm hoặc kho lần nữa | Đề xuất, bám cơ chế thanh toán hiện có |
| V15 | Đề xuất giữ 15 phút cho đơn VietQR chưa trả; thời hạn đơn tiền mặt cấu hình riêng và phải đồng bộ với xác nhận của thu ngân. Đơn bị hết hạn không được tiếp tục nhận thanh toán theo báo giá cũ | Đề xuất |
| V16 | Voucher đã giữ hợp lệ được bảo đảm trong thời gian giữ dù voucher hết hạn chung sau đó; thời điểm tạo giữ phải còn hợp lệ. Thu hồi khẩn cấp cần chính sách riêng và cảnh báo rõ | Đề xuất |
| V17 | Đơn đã trả lưu bản chụp mã, loại, điều kiện, mức giảm và phân bổ theo dòng; sửa chiến dịch sau này không thay tiền đơn cũ | Đề xuất |
| V18 | Hủy đơn chưa trả giải phóng quyền lợi; hoàn sau trả phải qua giao dịch đảo có tham chiếu, không tự tăng lại lượt. Chi tiết hoàn một phần/toàn phần thuộc phần 2 | Đề xuất; tích hợp phần 2 |
| V19 | Đổi điểm lấy voucher phải kiểm tra danh mục, số dư không bị giữ/hết hạn, hạn mức phần thưởng; trừ điểm FIFO và cấp mã trong cùng giao dịch; gửi lại không trừ/cấp thêm | Người dùng; cơ chế là Đề xuất |
| V20 | Điểm đã đổi voucher không dùng được để trừ tiền nữa; dùng voucher đã đổi không trừ điểm lần hai. Đề xuất không hoàn điểm chỉ vì voucher đã đổi bị hết hạn hoặc đơn sử dụng bị hủy | Đề xuất |
| V21 | Bạc có 2 mã freeship/tháng; Vàng có 3 mã trên 5 km/tháng; Kim Cương có 10 mã trên 5 km/tháng. Không tự cộng gói hạng thấp vào gói hạng cao | Người dùng; cách không cộng gói là Đề xuất |
| V22 | Vàng/Kim Cương tự động freeship dưới 5 km. Đề xuất tính cả đúng 5 km; không trừ mã tháng khi đã miễn tự động; không giảm ship vượt phí thực tế | Người dùng; mốc đúng 5 km và xử lý mã là Đề xuất |
| V23 | Đề xuất cấp mã theo tháng lịch Việt Nam, hết hạn đầu tháng kế tiếp, không cộng dồn; nâng hạng cấp bù đến hạn mức hạng mới, chống cấp lại do chạy tác vụ lặp | Đề xuất |
| V24 | Khoảng cách do máy chủ tính từ địa chỉ/tọa độ đã kiểm tra, so sánh trước làm tròn hiển thị. Chưa xác định khoảng cách thì chưa cấp báo giá freeship; ngoài bán kính vẫn từ chối giao | Đề xuất, bám Mã nguồn |

Đặc tả thêm cách chuẩn hóa mã, phân biệt hết hạn/hết lượt/không sở hữu/chưa đăng nhập/thiếu giá trị đơn/sai loại đơn/sai món/đang giữ ở đơn khác, và thông điệp tiếng Việt cho mỗi trường hợp. Với mã riêng, thông báo không được làm lộ danh tính người sở hữu.

## Công thức tính tiền cần thống nhất

Các điểm nguồn chưa quy định được chọn tạm dưới đây; phải đánh dấu Đề xuất và cho người dùng điều chỉnh.

- `S`: tiền hàng trước ưu đãi, tính từ giá món và topping do máy chủ xác định. **Đề xuất MVP:** gồm đồ uống như các hàng bán khác; nếu muốn chiết khấu hạng chỉ dành cho món ăn, cần tách cơ sở đủ điều kiện. Phí giao luôn tách riêng.
- `r`: tỷ lệ hạng; `Dt = floor(S × r)` là giảm theo hạng, đơn vị VNĐ.
- `A = S - Dt`: tiền hàng sau chiết khấu hạng.
- Phân bổ `Dt` về từng dòng và từng thành phần món/topping theo tỷ lệ, chia phần lẻ theo thứ tự ổn định để tổng phân bổ đúng `Dt`. `E` là tổng tiền sau hạng của phần đủ điều kiện voucher; nếu không giới hạn thì `E = A`.
- Kiểm tra đơn tối thiểu trên `E` trước voucher/điểm theo V07. Ghi rõ ngưỡng là của voucher, không mặc định mọi voucher đều có cùng ngưỡng.
- Voucher phần trăm: `Dv = min(floor(E × tỷ_lệ), mức_giảm_tối_đa, E)`.
- Voucher cố định: `Dv = min(mức_giảm_cố_định, E)`.
- Voucher một món: `Dv` bằng giá của **một suất món gốc sau phần chiết khấu hạng đã phân bổ**, không gồm topping, không vượt 100.000đ; điều kiện giá món gốc trước ưu đãi là `< 100.000đ`. Đề xuất tự chọn suất hợp lệ có lợi nhất, hiển thị suất được chọn; cho đổi lựa chọn nếu cần. Không nhân giảm với toàn bộ số lượng của dòng.
- `F`: phí giao từ dịch vụ hiện có; `Da` là miễn phí giao tự động của Vàng/Kim Cương: bằng `F` khi đơn giao hợp lệ, xác định được khoảng cách và thuộc nhóm gần, còn lại bằng 0.
- Voucher hàng hóa có `Ds = 0`. Mã freeship hạng trong ví có `Dv = 0`, `Ds = F - Da` khi đúng phạm vi; không giữ/tiêu mã nếu `Da = F`. Với mã giảm ship khác có trần công bố: `Ds = min(F - Da, trần_freeship)`.
- `R = A - Dv + F - Da - Ds`: số thanh toán còn lại trước điểm. `Da + Ds <= F`; tự động miễn ship có thể dùng cùng một voucher hàng hóa, nhưng không dùng hai mã trong ví.
- **Đề xuất:** trần điểm tính trên `R`, bao gồm phí giao còn lại: `points_cap = floor(R × 0,5 / 100)`; `points_max = min(points_cap, available_unexpired_points)`.
- Số điểm nhập phải là số nguyên không âm, không vượt `points_max`; nếu vượt thì báo số tối đa, không tự âm thầm đổi số điểm khách đã yêu cầu.
- `Dp = points_requested × 100`; `payable_amount = R - Dp`.

Bổ sung hợp đồng phần 2: chụp phân bổ từng suất/thành phần/ship gồm tiền sau ưu đãi, điểm nguyên và tiền mặt/chuyển khoản. Không phân bổ 100đ điểm vào một thành phần trị giá dưới 100đ. Nếu cần, trần điểm tại báo giá còn bị giới hạn bởi tổng `floor(component_net_amount / 100)` của các thành phần; phải thông báo trước xác nhận, không sửa đơn đã trả. Thứ tự khóa thống nhất và thuật toán phân bổ/hoàn được đối chiếu với `02_THIET_KE_HUY_DOI_TRA_HOAN_TIEN.md`.

Ví dụ bắt buộc:

| Khoản | Giá trị |
|---|---|
| Tiền hàng `S` | 300.000đ |
| Hạng Bạc 5%, `Dt` | 15.000đ |
| Sau hạng `A`, toàn bộ đủ điều kiện `E` | 285.000đ |
| Voucher 20%, tối đa 50.000đ, `Dv` | 50.000đ |
| Phí giao `F`, không giảm ship | 25.000đ |
| Trước điểm `R` | 260.000đ |
| Dùng 100 điểm, `Dp` | 10.000đ |
| Cần thanh toán | **250.000đ** |

Trần điểm của ví dụ là 1.300 điểm, tương đương 130.000đ, nếu số dư cho phép. Không tính điểm tích lũy mới vào số dư dùng ngay của chính đơn chưa hoàn tất.

Trường hợp `payable_amount = 0` phải có luồng tất toán nội bộ và nhật ký nguồn ưu đãi, chỉ một lần; không yêu cầu khách chuyển khoản 0đ hoặc giả mạo webhook ngân hàng. Nêu cách chuyển sang `PAID` và chạy nghiệp vụ kho hiện có mà không ghi nhận đã thu tiền ngân hàng. Nếu cần thêm kiểu tất toán hoặc trường dữ liệu thì ghi rõ đó là thiết kế mới.

## Liên kết với yêu cầu loyalty từ Markdown

Phần 1 phải hỗ trợ sử dụng các gói sau, không triển khai toàn bộ cơ chế xét hạng ở đây:

| Hạng phát quà | Voucher cần hỗ trợ | Tổng ưu đãi tối đa |
|---|---|---|
| Đồng | 1 mã 20%, tối đa 100.000đ | 100.000đ |
| Bạc | 3 mã 20%, mỗi mã tối đa 100.000đ | 300.000đ |
| Vàng | 1 mã một món dưới 100.000đ; 2 mã 25%, mỗi mã tối đa 150.000đ | 400.000đ |
| Kim Cương | 3 mã một món dưới 100.000đ; 1 mã 30%, tối đa 200.000đ; 3 mã 25%, mỗi mã tối đa 150.000đ | 950.000đ |

- Quyền freeship theo bảng riêng bên dưới thay cho mô tả chung trước đây; quà sinh nhật/hotline VIP giữ theo nguồn, giá trị chưa rõ vẫn là cấu hình chờ chốt.
- Thiết kế giao diện lấy `tier`, tỷ lệ, số dư hợp lệ và giữ/tiêu/giải phóng điểm từ module loyalty tương lai.
- Phần 1 phải thiết kế ví điểm, lô điểm, giao dịch và phân bổ tối thiểu để trừ/giữ điểm và đổi voucher. Nguồn cộng điểm/xét hạng đầy đủ thuộc phần bổ sung. Khi trình diễn chưa có dữ liệu thật, gắn nhãn dữ liệu mẫu; không trả số dư giả như thật.
- 10.000đ thực trả = 1 điểm chỉ khi đơn `COMPLETED`; 12 tháng hết hạn và FIFO thuộc phần bổ sung. Nêu giao diện sự kiện hoàn tất và khả năng chống cộng lặp. Phạm vi tiền tích điểm có tính ship hay không vẫn cần chốt ở phần bổ sung.
- Việc phát gói khi nâng hạng do `evaluateAndUpgradeTier(userId)` sở hữu; phần 1 chỉ định nghĩa dữ liệu cần nhận và khóa chống phát trùng theo sự kiện.

## Đổi điểm lấy voucher

Thiết kế thêm luồng 7 bước: mở danh mục → xem giá điểm/điều kiện → chọn phần thưởng → xác nhận trừ điểm → máy chủ khóa và kiểm tra → trừ điểm FIFO đồng thời cấp mã → trả voucher trong ví cùng số dư mới. Nếu một bước ghi dữ liệu thất bại phải rollback cả trừ điểm và cấp mã; cùng khóa yêu cầu trả lại cùng kết quả.

| Phần thưởng mẫu đề xuất | Giá điểm | Hạn và điều kiện đề xuất |
|---|---|---|
| Voucher giảm 10.000đ | 100 điểm | 30 ngày, không có đơn tối thiểu, giảm tối đa tiền hàng đủ điều kiện |
| Voucher giảm 20.000đ | 200 điểm | Như trên |
| Voucher giảm 50.000đ | 500 điểm | Như trên |

Đây là giá mẫu theo tỷ lệ 1 điểm = 100đ, chưa phải tỷ lệ người dùng đã chốt. Giá, hạn, số lượng tổng/mỗi người, hạng được đổi và phiên bản danh mục cấu hình riêng. Trần 50% dùng điểm trực tiếp không giới hạn giao dịch đổi voucher; voucher từ điểm vẫn chịu quy tắc một voucher/đơn. Đề xuất cho áp cùng điểm trực tiếp còn dư; nếu muốn một trần chung cho mọi ưu đãi mua bằng điểm phải ghi thành chính sách mới cần chốt.

Không giảm `total_qualifying_spend` khi đổi điểm. Không hoàn điểm khi voucher đã đổi bị hết hạn; hết hạn 30 ngày sau đổi có thể kéo dài thời gian sử dụng lợi ích từ điểm gần hết hạn, đây là đánh đổi chính sách phải nêu. Hủy đơn chưa trả giải phóng voucher về ví nếu còn hạn, không hoàn cả điểm đã mua lẫn voucher. Lỗi cấp mã rollback điểm; bồi hoàn ngoại lệ dùng giao dịch đảo có tham chiếu và không lặp.

## Freeship theo hạng và phát mã tháng

| Hạng | Khoảng cách dưới 5 km | Đúng 5 km | Khoảng cách trên 5 km | Mã phát mỗi tháng |
|---|---|---|---|---|
| Bạc | Dùng mã nếu chọn | Dùng mã nếu chọn | Dùng mã nếu chọn, trong phạm vi giao | 2 mã dùng trong phạm vi giao hợp lệ, phạm vi này là đề xuất |
| Vàng | Miễn tự động, không trừ mã | Đề xuất miễn tự động | Dùng mã giao xa nếu chọn | 3 mã giao xa |
| Kim Cương | Miễn tự động, không trừ mã | Đề xuất miễn tự động | Dùng mã giao xa nếu chọn | 10 mã giao xa |

Mã tháng miễn toàn bộ phí giao chuẩn máy chủ tính; không tự đặt trần tiền hoặc thu phần phí trên 5 km. Khoảng cách trên bán kính giao vẫn không phục vụ. Nếu thiếu khoảng cách, giải thích chưa xác nhận quyền lợi và yêu cầu khách xem lại giá trước đặt đơn.

Đề xuất kỳ `YYYY-MM` theo `Asia/Ho_Chi_Minh`, cấp đầu tháng hoặc bù lần truy cập đầu, hết hạn 00:00 ngày đầu tháng sau. Tác vụ và truy cập đồng thời phải dùng cùng khóa cấp `(user, period, program_version)`; dùng số thứ tự suất trong kỳ để không sinh trùng mã. Nâng hạng giữa tháng chỉ cấp chênh lệch đến tổng mục tiêu 2/3/10, đã dùng vẫn tính trong số đã cấp. Ví dụ từ Bạc đã nhận 2 lên Vàng nhận thêm 1 mã giao xa; lên Kim Cương trong cùng tháng nhận thêm 7. Mã cũ giữ điều kiện lúc cấp; không tự sửa lịch sử hoặc cấp lại khi dao động hạng. Đây là chính sách cấp bù đề xuất, phải nêu rõ với người dùng.

Đối chiếu `compute_delivery_fee`: hiện trả khoảng cách làm tròn hai chữ số; thiết kế cần giữ thêm khoảng cách máy chủ trước làm tròn để phân nhóm, tránh 5,004 km bị coi là 5 km. Phương pháp đo của MVP bám Haversine hiện có và phải công bố là khoảng cách ước tính, không khẳng định là quãng đường chạy xe.

## Mô hình dữ liệu đề xuất

Đưa ra ERD và từ điển trường theo Django hiện có, đủ ràng buộc nhưng tránh tạo lại `User` hoặc `Order`.

| Thực thể | Trường và trách nhiệm chính |
|---|---|
| `Voucher` mới | Mã chuẩn hóa duy nhất; tên; loại; tỷ lệ/số tiền; trần; ngưỡng tối thiểu; ngày bắt đầu/kết thúc; trạng thái; hạn mức toàn cục/mỗi user; phạm vi món/loại đơn/thanh toán; nguồn chiến dịch; phiên bản chính sách |
| `UserVoucher` mới | Chủ sở hữu; voucher; thời điểm cấp/hết hạn riêng; nguồn và mã sự kiện cấp; quyền khả dụng/đã dùng/hết hạn/thu hồi; bảo đảm không cấp trùng theo nguồn và sự kiện |
| `VoucherRedemption` mới | Đơn; voucher; quyền trong ví; người dùng; `RESERVED`, `CONSUMED`, `RELEASED`, `EXPIRED`, `REVERSED`; thời điểm giữ/hạn giữ/tiêu/giải phóng; số giảm; khóa xử lý lặp; tham chiếu giao dịch đảo |
| `RewardCatalog`, `PointVoucherExchange` mới | Phần thưởng/giá điểm/hạn/số lượng/phạm vi; lần đổi, user, điểm đã trừ, voucher đã cấp, bản chụp giá điểm và khóa chống lặp |
| `MonthlyShippingGrant` mới | User, kỳ tháng, phiên bản chương trình, hạn mức mục tiêu lớn nhất và số đã cấp; các suất cấp duy nhất; chống cộng cả gói hạng thấp và cấp lại khi chạy tác vụ |
| `Order` mở rộng | Giữ nghĩa của `total_amount` là tiền hàng gốc; bổ sung `tier_discount_amount`, `voucher_discount_amount`, `auto_shipping_discount_amount`, `voucher_shipping_discount_amount`, `shipping_discount_amount` bằng tổng hai khoản ship, `points_used`, `points_discount_amount`, `payable_amount`, khoảng cách/phiên bản/bản chụp ưu đãi; hạn thanh toán nếu chọn cơ chế giữ |
| Chi tiết phân bổ ưu đãi theo dòng | Gắn `OrderItem`; phần món/topping, tiền gốc và các khoản giảm phân bổ, số lượng và quy tắc làm tròn; phục vụ giải thích và hoàn một phần ở phần 2 |
| `LoyaltyAccount`, `PointLot`, `PointTransaction`, `PointAllocation` tối thiểu | Theo dõi điểm khả dụng/đang giữ, lô tích lũy và hạn, tiêu FIFO, liên kết trừ/giữ/đảo với lần đổi voucher hoặc đơn; mở rộng nguồn cộng điểm trong phần bổ sung |

```mermaid
erDiagram
    User ||--o{ UserVoucher : owns
    User ||--|| LoyaltyAccount : has
    LoyaltyAccount ||--o{ PointLot : owns
    LoyaltyAccount ||--o{ PointTransaction : records
    PointTransaction ||--o{ PointAllocation : allocates
    PointLot ||--o{ PointAllocation : tracks
    User ||--o{ PointVoucherExchange : exchanges
    RewardCatalog ||--o{ PointVoucherExchange : defines
    PointVoucherExchange o|--|| UserVoucher : issues
    User ||--o{ MonthlyShippingGrant : receives
    MonthlyShippingGrant o|--o{ UserVoucher : grants
    Voucher ||--o{ UserVoucher : grants
    User ||--o{ Order : places
    Order ||--o{ OrderItem : contains
    Voucher ||--o{ VoucherRedemption : tracks
    UserVoucher ||--o{ VoucherRedemption : authorizes
    Order ||--o{ VoucherRedemption : records_attempts
    OrderItem ||--o{ OrderDiscountAllocation : allocates
```

ERD cho phép lưu lịch sử nhiều lần thử/đảo, nhưng ràng buộc nghiệp vụ chỉ cho **một voucher đang giữ hoặc đã tiêu thụ hợp lệ trên một đơn**. Phân biệt trạng thái quyền trong ví với trạng thái một lần giữ; tránh hai cột trạng thái không có nguồn quyết định thống nhất.

Chỉ ra unique/check constraint, chỉ mục tra mã, ví theo user, giữ quá hạn và truy đơn. Giới hạn chiến dịch là điều kiện qua nhiều dòng nên phải có khóa/cập nhật nguyên tử, không chỉ kiểm tra bằng form hoặc một CHECK đơn giản. Ràng buộc chủ ví phải khớp chủ đơn, giá trị giảm không âm và không vượt cơ sở áp dụng.

Đơn cũ: thiết kế backfill `payable_amount = total_amount + delivery_fee`, các khoản giảm bằng 0; báo cáo/hiển thị phải phân biệt tiền hàng gốc và số thực trả. Không thiết kế thêm dashboard khi cập nhật các nơi đang hiển thị tiền.

## API và dịch vụ ở mức khái niệm

Các đường dẫn sau là **đề xuất mới**, cần đối chiếu `C:\Users\HP\Quanlypho\pho_app\urls.py` trước khi dùng:

| Giao diện | Mục đích |
|---|---|
| `GET /api/me/vouchers/` | Xem ví của người dùng hiện tại; có thể kèm tình trạng đủ điều kiện theo giỏ và lý do |
| `GET /api/rewards/` | Xem danh mục voucher đổi điểm, giá điểm, điều kiện, số lượng và phiên bản |
| `POST /api/me/reward-exchanges/` | Đổi điểm lấy voucher trong giao dịch có khóa chống lặp; trả mã đã cấp và số dư mới |
| `POST /api/checkout/quote/` | Nhận ID món, số lượng, topping, loại đơn/địa chỉ, mã hoặc quyền trong ví, điểm yêu cầu; trả giá máy chủ và từng khoản giảm; chưa giữ lượt |
| `POST /api/me/vouchers/claim/` nếu cần | Nhận mã công khai vào ví, có hạn mức và chống cấp trùng; bỏ endpoint này nếu chọn cơ chế nhận khi tạo đơn và giải thích lựa chọn |
| POST tạo đơn hiện có `/thuc-don/dat-mon/` | Mở rộng để xác minh báo giá/phiên bản, giữ voucher và điểm, chụp giá, chống tạo đơn trùng; giữ tương thích form hiện tại |
| `calculateOrderCheckout` / `calculate_order_checkout` | Một hàm tính tiền thuần hoặc dịch vụ chung cho quote, tạo đơn và đối chiếu; nêu rõ hai tên cùng hợp đồng |
| `reserve_benefits`, `consume_benefits`, `release_benefits` | Giữ, tiêu thụ, giải phóng có giao dịch và chống xử lý lặp; phần 2 bổ sung hợp đồng đảo sau thanh toán |
| `exchange_points_for_voucher`, `ensure_monthly_shipping_grant` | Trừ điểm/cấp mã nguyên tử; cấp đúng 2/3/10 mã tháng, tính phần cấp bù, chạy lặp an toàn |

Đặc tả request/response mẫu, mã lỗi ổn định, HTTP status phù hợp và quyền từng vai trò. Với xác thực session Django, các POST từ giao diện phải có CSRF. Không tin `user_id`, tỷ lệ, giá hoặc số dư từ client. Không cần tự thêm DRF chỉ để có vài endpoint JSON.

Response báo giá cần có: tiền hàng, giảm hạng, voucher đã chọn, giảm hàng, phí giao gốc, giảm ship tự động, giảm ship bằng mã và tổng giảm ship, khoảng cách/phương pháp tính, điểm tối đa, điểm đã chọn, giảm điểm, `payable_amount`, thời điểm/phiên bản báo giá và lỗi theo trường. Phiên bản giúp phát hiện thay đổi; báo giá không là cam kết giữ lượt.

Chỉ rõ thay đổi cần thiết để `_vietqr_image_url`, webhook, chi tiết đơn, xác nhận tiền mặt và mô phỏng thanh toán cùng đọc số phải trả đã chụp từ đơn. Sau tạo đơn không tự tính lại số thanh toán từ cấu hình voucher hiện tại.

## Xử lý đồng thời và vòng đời ưu đãi

Đối chiếu `04_THIET_KE_TAI_KHOAN_DIA_CHI_LOYALTY.md` cho nguồn điểm/xét hạng và ngữ cảnh chuyển tài khoản; request trình duyệt có vault/slot trước RequestKey khi cần, User trước ví, nhiều ví theo user ID tăng dần. Không tạo hệ thống ví/điểm thứ hai hoặc lấy nguồn điểm tương lai làm số dư dùng ngay.

- Tách trạng thái đơn, thanh toán và voucher; không gọi đơn `COMPLETED` chỉ vì ngân hàng báo đã trả.
- Thiết kế `transaction.atomic`, thứ tự khóa thống nhất giữa đơn, hạn mức voucher, quyền trong ví, điểm và các khóa bàn/kho hiện có; chỉ ra cách tránh tranh chấp, không giữ khóa trong lúc gọi dịch vụ ngoài.
- Hai đơn tranh lượt cuối: chỉ một đơn giữ thành công; đơn còn lại nhận thông báo và giá để khách xác nhận lại. Hai request cùng khóa tạo đơn trả về một đơn; cùng khóa nhưng payload khác phải bị từ chối.
- Callback thành công, callback thất bại, thao tác hủy và tiến trình hết hạn phải kiểm tra trạng thái dưới khóa, tránh vừa giải phóng vừa tiêu thụ. Callback trùng không tạo tác dụng phụ mới.
- Mô tả tiến trình giải phóng giữ quá hạn trong MVP bằng tác vụ có thể chạy lặp an toàn; tránh chỉ dựa vào đồng hồ trên trình duyệt.
- Đồng bộ phần 3 tại `03_THIET_KE_TON_KHO_GIAO_HANG.md`: giữ kho cùng giao dịch và hạn với ưu đãi, BOM được chụp, signal PAID chuyển giữ thành xuất một lần; không xuất thêm ở bếp/giao hàng. Thứ tự khóa bổ sung nhóm giữ kho/giao nhận và BOM trước nguyên liệu; không tự khôi phục giữ đã hết hạn khi tiền tới muộn.
- Voucher hết hạn trong lúc đang giữ dùng quy tắc V16. Nếu điểm cũng được giữ, phải chốt cách bảo đảm hạn điểm cùng module loyalty; không tự kéo dài hạn toàn bộ ví.
- Không tự hoàn tiền ngân hàng trong phần này. Sự kiện thanh toán muộn, lệch tiền hoặc kho không thể xác nhận cần trạng thái/lịch sử đối soát để phần 2 xử lý.
- Nêu điểm nghẽn khi nhiều người dùng cùng một chiến dịch; ưu tiên giải pháp khóa/hạn mức phù hợp MVP, nêu hướng tối ưu sau nếu có số liệu.

## Wireframe khu vực thanh toán

Tích hợp vào dialog giỏ hàng đang có, dùng phong cách giao diện hiện tại. Bản chữ dưới đây là bố cục đề xuất; trạng thái hạng và điểm có thể là dữ liệu mẫu khi trình bày thiết kế.

```text
GIỎ HÀNG CỦA BẠN
Danh sách món, topping, số lượng
Hình thức nhận món và địa chỉ nếu giao hàng
Phương thức thanh toán

ƯU ĐÃI
Hạng Bạc · tự động giảm 5%
Mã voucher  [Nhập mã ưu đãi          ] [Áp dụng]
[Chọn từ ví voucher]
[Đổi điểm lấy voucher]
Đã chọn: PHO20 · giảm 20%, tối đa 50.000đ   [Bỏ]
Thông tin điều kiện / lỗi tại đây

Điểm khả dụng: ... điểm
Điểm muốn dùng [100]     Dùng tối đa ... điểm
100 điểm = 10.000đ; tối đa 50% phần còn lại

Tiền hàng                         300.000đ
Ưu đãi hạng Bạc                    -15.000đ
Voucher PHO20                      -50.000đ
Phí giao hàng                       25.000đ
Giảm phí giao                            0đ
Dùng 100 điểm                      -10.000đ
TỔNG THANH TOÁN                    250.000đ

[Xác nhận đặt món · 250.000đ]
Lượt voucher được giữ khi tạo đơn thành công.
```

Thiết kế trạng thái: chưa đăng nhập, ví rỗng, đang kiểm tra, áp thành công, không đủ điều kiện, mã đang giữ ở đơn khác, điều kiện thay đổi và mất kết nối. Ví hiển thị giá trị, hạn, điều kiện và lý do chưa dùng được; gợi ý mã tiết kiệm nhất dựa trên báo giá thật, không tự chọn thay mã khách đang dùng.

Thêm wireframe danh mục đổi điểm, màn hình xác nhận số điểm trừ/số dư còn lại/điều kiện voucher, kết quả có nút về ví; thiếu điểm hoặc hết quà có lỗi tại phần thưởng. Thể hiện đúng số mã tháng còn lại, điều kiện khoảng cách và nhãn “Freeship theo hạng” riêng với “Mã freeship”. Không chỉ hiện một dòng “Giảm phí giao” mà thiếu lý do nguồn quyền lợi.

Có nhãn trường thật, điều khiển bằng bàn phím, focus rõ, vùng bấm tối thiểu 44px, thông báo động đọc được bằng screen reader. Lỗi nằm gần trường và có tổng hợp lỗi khi gửi form thất bại. Khi mở ví trong dialog, quản lý focus và tránh dialog lồng khó đóng; giữ cấu trúc hiện có nếu có thể. Trên điện thoại không tràn ngang; giữ chỗ thông báo để tổng tiền/nút xác nhận không nhảy bất ngờ.

Trong lúc kiểm tra/đặt đơn, nút có phản hồi đang xử lý và chống bấm lặp; lỗi không làm mất món hoặc địa chỉ. Trước khi tạo đơn phải có báo giá đã xác nhận, tránh vừa nhận response cũ vừa ghi đè tổng tiền của giỏ mới.

## Kịch bản nghiệm thu thiết kế

Đưa ra bảng dữ liệu đầu vào, kết quả mong đợi và quy tắc được kiểm chứng. Ít nhất bao phủ:

1. Ví dụ 300.000đ + Bạc + voucher 20% trần 50.000đ + ship 25.000đ + 100 điểm cho kết quả **250.000đ**, cả QR và webhook cùng số này.
2. Với dữ liệu trên, 1.300 điểm được chấp nhận nếu đủ số dư; 1.301 điểm bị từ chối vì vượt trần. Không dùng điểm mới sẽ tích từ chính đơn.
3. Mã sai, chưa hiệu lực, đúng thời điểm hết hạn và bị thu hồi: không thay lựa chọn voucher hợp lệ trước đó và có thông báo cụ thể.
4. Đơn tối thiểu 100.000đ nhưng sau hạng còn 95.000đ: bị từ chối theo chính sách đề xuất V07, giải thích rõ cơ sở tính.
5. Voucher giới hạn món chỉ tính phần đủ điều kiện; đơn có đồ uống/topping ngoài phạm vi không được giảm các phần đó.
6. Một mã hết hạn trước lúc tạo giữ bị từ chối; một mã được giữ hợp lệ trước hạn vẫn dùng được trong hạn giữ theo V16.
7. Hai đơn tranh một lượt cuối và hai đơn cùng dùng một quyền trong ví: chỉ một giữ thành công, không có số dư/lượt âm.
8. Nhấn đặt hai lần, gửi lại cùng idempotency key, webhook lặp: một đơn, một lần tiêu voucher/điểm và một lần xuất kho.
9. Hủy/timeout trước thanh toán: giải phóng một lần. Thanh toán đến sau timeout: ghi nhận đối soát, không tự tiêu quyền đã được người khác dùng.
10. Hai mã một voucher món và một freeship: chỉ được chọn một. Freeship trần 20.000đ với phí giao 25.000đ chỉ giảm 20.000đ.
11. Voucher một món với dòng có số lượng hai: giảm đúng một suất gốc sau hạng, không giảm hai suất hoặc topping. Món giá đúng 100.000đ không đáp ứng điều kiện “dưới 100.000đ”.
12. Voucher cố định lớn hơn cơ sở đủ điều kiện: giảm tối đa cơ sở, không có tiền âm hoặc tiền thừa được trả lại.
13. Tổng bằng 0: tất toán nội bộ có nhật ký, không sinh chuyển khoản 0đ và không giả webhook.
14. Giả mạo giá, hạng, chủ ví hoặc điểm từ client: máy chủ bỏ qua/từ chối phù hợp; người này không xem/dùng ví của người khác.
15. Giỏ thay đổi khi request báo giá cũ đang chạy: chỉ response đúng phiên bản mới được hiển thị; giá thay trước tạo đơn cần khách xác nhận lại.
16. Đơn cũ không ưu đãi vẫn hiển thị/thu tiền đúng; khách vãng lai, tiền mặt, VietQR, tại bàn, giao hàng và giỏ xếp hàng vẫn có đường đi hợp lệ.
17. Đổi 200 điểm lấy voucher 20.000đ từ 1.000 điểm: còn 800, có đúng một mã. Request lặp cùng khóa trả mã đó; lỗi cấp mã không mất điểm.
18. Điểm hết hạn hoặc đang giữ không dùng đổi voucher; hai request đổi và checkout đồng thời không chi cùng số điểm. Dùng mã đã đổi không trừ lại 200 điểm.
19. Bạc nhận đúng 2, Vàng đúng 3, Kim Cương đúng 10 mã trong tháng; chạy lại tác vụ/truy cập đồng thời không tăng số lượng. Nâng Bạc → Vàng → Kim Cương trong một tháng đề xuất cấp thêm 1 rồi 7.
20. Vàng/Kim Cương dưới 5 km được miễn ship không tốn mã; đúng 5 km theo đề xuất; 5,004 km thuộc nhóm giao xa dù hiển thị 5,00. Bạc không tự miễn khi chưa chọn mã.
21. Vàng dùng một voucher món kèm freeship tự động được; một voucher món kèm mã freeship tháng bị từ chối vì hai mã; không tiêu mã nếu phí đã miễn tự động.
22. Đổi tháng theo giờ Việt Nam, mã cũ hết hạn nhưng một lần giữ hợp lệ vẫn theo V16; mã mới không được cấp lặp. Đơn ngoài phạm vi hoặc chưa rõ khoảng cách không được tự miễn ship.

Đây là kịch bản nghiệm thu của thiết kế. Chưa chạy hay khẳng định kiểm thử tính năng thật trong giai đoạn soạn prompt.

## Đầu ra yêu cầu theo thứ tự

1. Tóm tắt vấn đề, người dùng, phạm vi MVP và giá trị bổ sung.
2. Bảng truy vết yêu cầu về Người dùng/Word/Markdown/mã nguồn/đề xuất; nêu điều gì cần xác minh lại.
3. Luồng 5–8 bước và Mermaid đã hoàn thiện, gồm nhánh lỗi và vòng đời giữ.
4. Bảng ít nhất bốn quy tắc; đối chiếu đầy đủ các quy tắc V01–V24, thêm luồng đổi điểm và phát mã tháng; chỉ sửa đề xuất khi có lý do rõ ràng.
5. Công thức, ví dụ tính tiền, xử lý số lẻ, tổng 0 và các trường hợp không hợp lệ.
6. ERD, trường chính, ràng buộc, lịch sử ưu đãi và phân bổ theo dòng; cách chuyển tiếp đơn cũ.
7. API/dịch vụ khái niệm với ví dụ JSON; giao dịch và xử lý lặp/đồng thời; các điểm cần đổi khi triển khai, không viết mã nguồn lúc này.
8. Wireframe và trạng thái giao diện checkout/ví voucher/đổi điểm lấy voucher, bám dialog giỏ hàng hiện có.
9. Tiêu chí nghiệm thu và giải thích ít nhất hai quyết định có đánh đổi, như cơ sở đơn tối thiểu và thời điểm giữ lượt.
10. Kế hoạch triển khai riêng phần 1 theo bước: xác minh mã → chốt chính sách → schema/migration dự kiến → ví điểm tối thiểu/đổi voucher → phát mã tháng → dịch vụ tính tiền → giữ/tiêu thụ → tích hợp đơn/thanh toán → giao diện → kiểm thử phù hợp. Liệt kê file dự kiến sửa và phụ thuộc còn chờ, chưa thực hiện kế hoạch này.
11. Phiếu hoàn thành tương đương mẫu Word và danh sách ngắn những điểm còn mở: mốc đúng 5 km, cấp bù giữa tháng, giá điểm/hạn voucher đổi, thời gian giữ, cơ sở chiết khấu/đơn tối thiểu và điểm có trả ship không. Bản thiết kế kết quả lưu tại `C:\Users\HP\Quanlypho\docs\th4\01_THIET_KE_KHUYEN_MAI_VOUCHER.md`.
12. **Dừng lại sau phần 1**, kết thúc bằng: **“Bạn muốn bổ sung hoặc điều chỉnh gì ở phần Khuyến mãi/voucher? Có yêu cầu nào còn thiếu không? Khi bạn chốt phần này, mình mới chuyển sang phần 2.”**
