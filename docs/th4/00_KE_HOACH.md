# Kế hoạch thiết kế bổ sung cho Quanlypho

## Phạm vi và cách thực hiện

Thiết kế theo Hướng 1 Hệ thống thương mại điện tử, áp dụng vào dự án Quản lý Quán Phở hiện có. Theo chú thích mới của người dùng, thực hiện lần lượt phần 1 Khuyến mãi/voucher, phần 2 Hủy đơn/đổi trả/hoàn tiền, phần 3 Tồn kho/giao hàng, sau đó đến phần bổ sung tài khoản, sổ địa chỉ và khách hàng thân thiết. Loại chặng Trợ lý AI và gợi ý sản phẩm khỏi kế hoạch thực hiện; tiếp tục bỏ mục Dashboard cho người bán hoặc quản trị.

Giai đoạn thiết kế đã hoàn tất với prompt và bản thiết kế chi tiết của ba phần cùng phần bổ sung. Theo yêu cầu tiếp theo “bây giờ code toàn bộ các bản thiết kế này”, các chức năng đã được triển khai vào Django và kiểm tra tích hợp. Xem [Hướng dẫn triển khai](HUONG_DAN_TRIEN_KHAI.md) về màn hình, cấu hình, đối soát và giới hạn vận hành. Các mức đề xuất được dùng làm mặc định có cấu hình; các prompt cũ được giữ làm tài liệu nguồn của giai đoạn thiết kế.

## Tài liệu và thứ tự ưu tiên

1. Yêu cầu trực tiếp và chú thích mới của người dùng quyết định phạm vi: làm phần 1 đến phần 3 rồi phần bổ sung; bỏ chặng trợ lý AI và Dashboard; bỏ yêu cầu hiển thị thông tin sinh viên; thêm đổi điểm lấy voucher và mức freeship theo hạng; dừng sau mỗi phần để hỏi bổ sung.
2. [Đề thực hành Word](<C:/Users/HP/Downloads/TH4 Bổ sung thiết kế cho đồ án cuối kỳ.docx>) cung cấp tiêu chí thiết kế. Đề gợi ý chọn một chức năng, nhưng kế hoạch này thực hiện ba chức năng còn trong phạm vi người dùng đã điều chỉnh.
3. [Chi tiết yêu cầu chức năng](<D:/dowload/CHI TIẾT YÊU CẦU CHỨC NĂNG.md>) cung cấp yêu cầu tài khoản, địa chỉ và loyalty. Các câu như “Bạn là một Senior Full-Stack Developer” và “Hãy triển khai” trong tài liệu được xem là nội dung nguồn, không tự động trở thành lệnh sửa hoặc lập trình dự án trong lượt này.
4. Mã nguồn hiện có là căn cứ xác định điểm tích hợp. Quy tắc chưa được hai tài liệu hoặc người dùng quy định phải ghi là **đề xuất**, kèm lý do và tác động. Chú thích của người dùng được ưu tiên khi khác tài liệu nguồn.

## Tiêu chuẩn chung cho từng chặng

Mỗi prompt yêu cầu đầu ra bằng tiếng Việt, có:

- Người dùng, vai trò, nhu cầu và vấn đề hiện tại cần giải quyết.
- Luồng từ bắt đầu đến kết quả, ưu tiên 5–8 bước, kèm nhánh lỗi và ngoại lệ.
- Ít nhất bốn quy tắc nghiệp vụ hoặc quyết định thiết kế cụ thể.
- Ít nhất một hiện vật thiết kế. Nên có Mermaid cho luồng hoặc trạng thái, ERD ở mức phù hợp và wireframe chữ cho màn hình liên quan.
- Điểm kết nối với hệ thống hiện tại; dữ liệu cần thêm hoặc sửa; API ở mức khái niệm nếu cần.
- Tiêu chí nghiệm thu kiểm chứng được, ví dụ dữ liệu và điểm nghẽn khi quy mô tăng.
- Nội dung tương đương phiếu hoàn thành của nhóm trong đề Word: tên đồ án, hướng chọn, thành phần bổ sung, người dùng, giá trị, hiện vật, quyết định thiết kế, tích hợp và việc tiếp theo.
- Phân biệt yêu cầu nguồn, hiện trạng mã nguồn, chính sách đề xuất và câu hỏi còn mở.
- Dừng sau phần đang làm, hỏi người dùng muốn bổ sung hoặc sửa gì; chưa tự chuyển phần.

## Thứ tự thực hiện

| Chặng | Nội dung | Đầu ra của prompt | Điều kiện kết thúc chặng |
|---|---|---|---|
| 1 | Khuyến mãi và voucher | Luồng áp dụng và đổi điểm lấy voucher; freeship tự động và mã freeship theo hạng; điều kiện, hạn và hạn mức; cộng gộp hạng + một voucher + điểm; thiết kế dữ liệu; wireframe; ví dụ tính tiền | Giá cuối nhất quán giữa báo giá, tạo đơn và VietQR; đổi điểm/cấp mã không bị lặp; hạn mức freeship đúng; xử lý mã sai, hết lượt, hết hạn; dừng lấy phản hồi |
| 2 | Hủy đơn, đổi trả và hoàn tiền | Ma trận quyền theo trạng thái; sơ đồ yêu cầu và hoàn tiền; làm lại/giao bù món; sổ tiền đã nhận và hạn mức hoàn; hoàn một phần theo suất; hoàn điểm/voucher/freeship; thông báo và màn hình tra cứu | Tách trạng thái đơn, tiền đã nhận, yêu cầu và giao dịch hoàn; không hoàn vượt tiền thực nhận hoặc xử lý trùng; chống vừa giao bù vừa hoàn cùng suất; dừng lấy phản hồi |
| 3 | Tồn kho và giao hàng | Bản chụp BOM/đơn vị tính; giữ nguyên liệu khi tạo đơn; chuyển giữ thành xuất tại PAID; hết hạn/hủy/hoàn nguyên liệu/giao bù; giao nhận thành công/thất bại; khoảng cách, phí và freeship; đồng bộ trạng thái | Giữ đồng thời không vượt khả dụng; xuất/đảo có tham chiếu một lần; không nhập lại món đã chế biến; bàn giao chưa hoàn tất; COMPLETED có sự kiện giao thật; dừng lấy phản hồi |
| Bổ sung | Chi tiết yêu cầu chức năng từ Markdown đã điều chỉnh | Hồ sơ/avatar/mật khẩu, phiên nhiều tài khoản, địa chỉ mặc định nguyên tử; mua hàng/đánh giá/điểm danh/giới thiệu; FIFO/hết hạn/nợ điểm; xét hạng/phát quà; sinh nhật/VIP; ERD/API và ba tab tài khoản; dùng lại voucher/đổi điểm/freeship phần 1 | Truy vết đủ yêu cầu; cách ly tài khoản và dữ liệu đơn; số dư/quà không lặp; chính sách chưa rõ có nhãn đề xuất; dừng lấy phản hồi |

## Ranh giới giữa các phần

**Phần 1** định nghĩa cách tính tiền, voucher, đổi điểm lấy voucher, phát mã freeship theo tháng, freeship tự động theo khoảng cách và vòng đời giữ/tiêu thụ ưu đãi. Thiết kế sổ điểm tối thiểu phục vụ trừ/giữ điểm, còn nguồn cộng điểm, xét hạng đầy đủ, đăng nhập, sổ địa chỉ, điểm danh và giới thiệu thuộc chặng bổ sung.

**Phần 2** quyết định chính sách hủy/hoàn, rồi dùng các giao diện giải phóng hoặc đảo giao dịch ưu đãi từ phần 1. Với món ăn, phân biệt hủy trước chế biến, lỗi món, giao thiếu và yêu cầu sau giao; không mặc định áp dụng mô hình trả hàng nguyên kiện. Ghi nhận tiền chuyển đến muộn/trùng bằng giao dịch nhận tiền riêng, tránh mở lại đơn đã hủy hoặc hoàn trùng do nhầm callback lặp với hai lần chuyển tiền thật. Chi tiết giữ/hoàn nguyên liệu và trạng thái giao nằm ở hợp đồng dành cho phần 3.

**Phần 3** quyết định cơ chế giữ nguyên liệu và giao nhận. Tạo giữ khi xác nhận đơn, không giữ chỉ vì xem giỏ/báo giá; chuyển giữ thành xuất qua đầu mối PAID hiện có, không trừ thêm ở bếp hoặc lúc giao. Dùng cùng hạn giữ với voucher/điểm, bản chụp BOM và phí/khoảng cách, giao nhận có lịch sử riêng. Giao lỗi không tự hoàn tiền hoặc hoàn nguyên liệu; giao bù xuất riêng và không tích điểm mua hàng lần nữa.

**Phần bổ sung** sở hữu hồ sơ tài khoản, phiên chuyển tài khoản, địa chỉ, nguồn và sổ điểm, xét hạng/phát quà. Tái sử dụng hợp đồng tính tiền/voucher của phần 1, quy tắc đảo giao dịch phần 2 và sự kiện hoàn tất phần 3. Có xác minh ngữ cảnh tài khoản cho request và sự kiện nhiều ví được xử lý theo thứ tự khóa toàn cục. Chi tiết nằm trong `04_THIET_KE_TAI_KHOAN_DIA_CHI_LOYALTY.md`.

## Danh mục yêu cầu cần bảo toàn ở chặng bổ sung

Danh mục sau là bảng đối chiếu yêu cầu nguồn và chú thích mới. Thiết kế/prompt chi tiết chặng bổ sung đã được soạn trong bộ tệp `04_*`; các lựa chọn ngoài nguồn vẫn ghi đề xuất. Đổi điểm lấy voucher và freeship tiếp tục dùng thiết kế phần 1, không tạo hệ thống thứ hai.

### Tài khoản và xác thực

- Hồ sơ: họ tên, điện thoại, email, ngày sinh, giới tính; đổi mật khẩu có kiểm tra mật khẩu cũ.
- Avatar: JPG, PNG hoặc WEBP; tối đa 5 MB; xem trước khi lưu.
- Nhiều tài khoản trên cùng thiết bị/trình duyệt: thêm tài khoản, chuyển nhanh giữa các phiên đã xác thực, đăng xuất phiên hiện tại. Thiết kế phải cách ly dữ liệu, giỏ hàng và phiên; không lưu mật khẩu để chuyển tài khoản.

### Sổ địa chỉ

- Một tài khoản có nhiều địa chỉ với tên người nhận, điện thoại, địa chỉ chi tiết, Phường/Xã, Quận/Huyện, Tỉnh/Thành phố, nhãn Nhà riêng/Văn phòng/Khác, ghi chú và cờ mặc định.
- Có thêm, sửa, xóa và chọn địa chỉ mặc định; chỉ một địa chỉ mặc định trong phạm vi một tài khoản.
- Khi có nhiều hơn một địa chỉ, không cho xóa địa chỉ mặc định trước khi chọn địa chỉ khác làm mặc định.
- Cần làm rõ cách ánh xạ các trường địa chỉ trong tài liệu với dữ liệu địa chỉ dự án dùng ở thời điểm triển khai; giữ bản chụp địa chỉ trên đơn cũ.

### Điểm và nguồn tích lũy

- Tách `total_qualifying_spend` dùng xét hạng khỏi `available_points` dùng đổi ưu đãi.
- Mua hàng: 10.000 VNĐ thực trả sau khuyến mãi = 1 điểm, chỉ cộng khi đơn `COMPLETED`; cần chốt phạm vi phí giao hàng và quy tắc làm tròn.
- Dùng điểm trừ tiền trực tiếp: 1 điểm = 100 VNĐ; chỉ trừ tối đa 50% giá trị thanh toán còn lại.
- **Bổ sung theo người dùng:** dùng điểm đổi voucher từ danh mục phần thưởng, trừ điểm và cấp voucher vào ví trong cùng giao dịch. Giá điểm, số lượng, hạn dùng và điều kiện của từng phần thưởng là cấu hình; ví dụ đề xuất 100 điểm đổi voucher 10.000đ, 200 điểm đổi voucher 20.000đ. Không trừ lại điểm khi dùng voucher đã đổi, không tính điểm đã giữ hoặc hết hạn là điểm khả dụng.
- Trần 50% ở nguồn áp dụng cho dùng điểm trực tiếp tại checkout, không áp lên số điểm đổi voucher. Voucher từ điểm vẫn chiếm một vị trí voucher trên đơn; đề xuất cho dùng cùng điểm trực tiếp còn trong ví và phải hiển thị rõ hai giao dịch độc lập.
- Đánh giá: có điểm thưởng, nguồn cho ví dụ +5 điểm. “Đánh giá tốt” dùng xét hạng phải đồng thời từ 4 sao và bình luận ít nhất 20 ký tự.
- Điểm danh mỗi ngày; chuỗi đủ bảy ngày liên tiếp thưởng gấp đôi ở ngày thứ bảy. Mức điểm cơ bản chưa được nguồn quy định.
- Mã giới thiệu riêng; người giới thiệu và người mới nhận thưởng khi người mới hoàn thành đơn đầu tiên. Mức thưởng chưa được nguồn quy định.
- Điểm hết hạn sau 12 tháng từ ngày tích lũy; tiêu theo FIFO. Cần thiết kế xử lý hết hạn trong lúc giữ điểm và đảo điểm sau hoàn.

### Hạng và gói voucher

| Hạng | Điều kiện chi tiêu theo nguồn | Điều kiện đánh giá theo nguồn | Chiết khấu | Gói khi lên hạng | Giá trị ưu đãi tối đa của gói |
|---|---|---|---|---|---|
| Thành viên | Mặc định; nguồn mô tả chi tiêu dưới 500.000đ | Chưa nêu | 0% | Chưa nêu | Chưa nêu |
| Đồng | Từ 500.000đ | Ít nhất 2 đánh giá tốt | 2% | 1 voucher 20%, tối đa 100.000đ | 100.000đ |
| Bạc | Từ 2.000.000đ | Duy trì ít nhất 2 đánh giá tốt | 5% | 3 voucher 20%, mỗi mã tối đa 100.000đ | 300.000đ |
| Vàng | Từ 5.000.000đ | Không nhắc lại rõ điều kiện đánh giá | 7% | 1 voucher một món dưới 100.000đ; 2 voucher 25%, mỗi mã tối đa 150.000đ | 400.000đ |
| Kim Cương | Từ 12.000.000đ | Không nhắc lại rõ điều kiện đánh giá | 10% | 3 voucher một món dưới 100.000đ; 1 voucher 30% tối đa 200.000đ; 3 voucher 25%, mỗi mã tối đa 150.000đ | 950.000đ |

Lưu ý cần chốt: người đủ tiền nhưng chưa đủ đánh giá sẽ thuộc hạng nào; Vàng và Kim Cương có tiếp tục yêu cầu ít nhất hai đánh giá tốt không; vượt nhiều hạng trong một lần nhận gói nào; hoàn tiền có làm giảm hạng hay thu hồi quà không. Không tự biến các điểm chưa rõ thành yêu cầu đã có trong nguồn.

### Đặc quyền và thanh toán

Mức freeship theo chú thích mới của người dùng:

| Hạng | Freeship tự động | Mã freeship phát hằng tháng |
|---|---|---|
| Thành viên, Đồng | Chưa quy định | Chưa quy định |
| Bạc | Chưa có quyền tự động | 2 mã; đề xuất dùng trong toàn phạm vi giao hàng hợp lệ |
| Vàng | Freeship khi khoảng cách dưới 5 km | 3 mã cho khoảng cách trên 5 km |
| Kim Cương | Freeship khi khoảng cách dưới 5 km | 10 mã cho khoảng cách trên 5 km |

- **Đề xuất tại đúng 5 km:** áp quyền freeship tự động cho Vàng/Kim Cương như nhóm gần; các mã đường xa chỉ dùng khi `distance_km > 5`. Đây là điểm biên chưa được người dùng quy định.
- **Đề xuất cộng gộp:** freeship tự động là đặc quyền, không phải voucher và không chiếm vị trí một voucher/đơn. Mã freeship trong ví có chiếm vị trí đó; không đồng thời áp hai mã giảm món và freeship. Không tiêu mã freeship khi phí giao đã được miễn tự động.
- Mã freeship hạng miễn toàn bộ phí giao chuẩn do máy chủ tính, không tự thêm trần tiền khi người dùng chưa yêu cầu. Không mở rộng bán kính giao hàng hiện có. Khoảng cách chưa xác định thì chưa cam kết freeship.
- Đề xuất kỳ tháng theo giờ Việt Nam, mã hết hạn đầu tháng kế tiếp, không cộng dồn số chưa dùng; cấp bù có chống lặp khi nâng hạng. Chi tiết và ví dụ nằm trong bản thiết kế phần 1.
- Bạc trở lên giữ quà sinh nhật; Vàng/Kim Cương giữ quà sinh nhật đặc biệt và hotline CSKH VIP theo nguồn. Số hotline, giá trị quà, cơ chế hạ hạng chưa được quy định; dữ liệu demo phải có nhãn.
- Chiết khấu hạng áp dụng tự động; mỗi đơn dùng tối đa một voucher từ ví; điểm trực tiếp tính sau các ưu đãi, tối đa 50% phần thanh toán còn lại.

### Dữ liệu, nghiệp vụ và giao diện bắt buộc

- Bao phủ các thực thể nguồn yêu cầu: `Users`, `UserAddresses`, `LoyaltyAccounts`, `PointTransactions`, `TierConfigs`, `Vouchers`, `UserVouchers`, `DailyCheckins`. Ánh xạ với `User` đã tồn tại; tái sử dụng danh mục đổi thưởng, lần đổi, phát mã tháng và sổ điểm tối thiểu đã thiết kế ở phần 1; bổ sung thực thể cho đánh giá/referral nếu cần.
- Đặc tả API hồ sơ, avatar, phiên tài khoản và địa chỉ; quy tắc chỉ thao tác dữ liệu thuộc người dùng hiện tại.
- Đặc tả `evaluateAndUpgradeTier(userId)` và `calculateOrderCheckout`; có thể ánh xạ sang tên Python theo quy ước dự án, nhưng phải nêu rõ tương đương.
- Trang tài khoản HTML chia tab Hồ sơ cá nhân, Sổ địa chỉ, Thành viên và Tích điểm. Hiển thị số tiền và số đánh giá tốt còn thiếu để lên hạng, ví voucher, giá trị ưu đãi tối đa của từng gói. Không trình bày giá trị tối đa như tiền mặt được nhận chắc chắn.

## Các hợp đồng tích hợp cần thống nhất

| Hợp đồng | Chặng quyết định | Chặng sử dụng |
|---|---|---|
| Báo giá gồm tiền hàng, chiết khấu hạng, giảm voucher, phí giao, giảm ship tự động/qua mã, điểm và số thực trả | 1 | 2, 3, bổ sung |
| Giữ, tiêu thụ và giải phóng voucher/điểm; lưu ưu đãi theo đơn; chống xử lý lặp | 1 | 2, bổ sung |
| Đổi điểm lấy voucher, dữ liệu lô điểm FIFO và phát mã freeship tháng đúng 2/3/10 theo hạng | 1 | 2, bổ sung |
| Hoàn một phần/toàn phần; hoàn voucher, điểm và điều chỉnh chi tiêu | 2 | 3, bổ sung |
| Tiền đã nhận, tiền hoàn đang giữ/đã trả; giao bù hoặc hoàn theo suất; lịch sử trạng thái và thông báo | 2 | 1, 3, bổ sung |
| Giữ và xuất nguyên liệu, đơn giao thất bại, giao thành công và sự kiện COMPLETED | 3 | 1, 2, bổ sung |
| Bản chụp BOM, thời hạn giữ chung, đảo xuất chưa sử dụng, phí/khoảng cách và phiên bản giao nhận | 3 | 1, 2, bổ sung |
| Nguồn tích điểm, hạng hiện tại và sự kiện đủ điều kiện phát voucher | Bổ sung | 1, 2 |
| Ngữ cảnh phiên tài khoản, địa chỉ có version, đóng góp chi tiêu theo đơn và nhận thưởng theo mục tiêu hiện tại | Bổ sung | 1, 2, 3 |

Phụ thuộc chưa thiết kế phải thể hiện bằng giao diện hoặc dữ liệu mẫu có nhãn; không khẳng định đã có tính năng thật.

## Hiện trạng dự án đã đối chiếu

- Django; ORM GIS dùng PostgreSQL/PostGIS; HTML template và JavaScript hiện có.
- `User`, `MenuItem`, `Topping`, `Order`, `OrderItem`, `Ingredient`, `Recipe`, `InventoryTransaction`, `Review` đã có trong `pho_app/models.py`.
- Giỏ/checkout nằm trong `pho_app/templates/pho_app/customer/menu.html` và `pho_app/static/pho_app/js/menu.js`; không có trang `customer/cart.html` riêng ở lần kiểm tra này.
- `place_order` tạo đơn, `_vietqr_image_url` sinh QR, `vietqr_webhook` kiểm tra tiền trong `pho_app/views.py`.
- Tiền QR và số tiền webhook mong đợi hiện lấy `order.total_amount + order.delivery_fee`; voucher cần thiết kế thống nhất lại các nơi dùng số tiền này.
- Các trạng thái đơn đã có: `CART`, `PENDING_KITCHEN`, `COOKING`, `READY`, `DELIVERING`, `COMPLETED`, `CANCELLED`. Thanh toán có trạng thái riêng `PENDING`, `PAID`, `FAILED`.
- Kho hiện kiểm tra khả dụng theo định lượng và trừ khi đơn chuyển `PAID` qua signal; phần 3 cần bám cơ chế này.
- Chưa thấy mô hình voucher, loyalty hoặc sổ địa chỉ trong `models.py` đã đọc. Agent triển khai sau này phải kiểm tra lại mã nguồn trước khi thay đổi.

## Tiến độ và điểm dừng

| Chặng | Trạng thái |
|---|---|
| Kế hoạch tổng thể | Đã cập nhật bốn chú thích của người dùng |
| 1 Khuyến mãi và voucher | Đã triển khai báo giá, ví/mã ưu đãi, đổi điểm, phân bổ theo suất và nhất quán thanh toán |
| 2 Hủy đơn, đổi trả và hoàn tiền | Đã triển khai tiếp nhận, duyệt, đối soát hoàn, đảo quyền lợi và giao bù |
| 3 Tồn kho và giao hàng | Đã triển khai giữ/xuất/hoàn kho, snapshot BOM, kiểm kê, lượt giao và hoàn tất thực tế |
| Bổ sung yêu cầu chức năng | Đã hoàn thiện prompt, thiết kế và triển khai tài khoản, địa chỉ, điểm, hạng, referral, điểm danh, đổi voucher |

Người dùng đã yêu cầu triển khai toàn bộ sau giai đoạn thiết kế. Các chặng trên đã có mã nguồn, migration, giao diện và kiểm thử tương ứng; theo dõi cách chạy trong `HUONG_DAN_TRIEN_KHAI.md`.
