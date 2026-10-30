# Prompt thiết kế Figma cho Phở Nhà

## 1. Vai trò và mục tiêu

Bạn là chuyên gia thiết kế sản phẩm số và UX/UI. Hãy thiết kế trên Figma bộ giao diện hoàn chỉnh cho Phở Nhà, một hệ thống quản lý quán phở kết hợp đặt món trực tuyến. Mục tiêu là mở rộng giao diện dự án hiện có thành trải nghiệm thống nhất, rõ ràng và đủ chi tiết để phát triển. Thiết kế bằng tiếng Việt, ưu tiên hành vi thực tế của khách đặt món và nhân viên vận hành. Tạo màn hình có cấu trúc, nội dung, tương tác và trạng thái; không chỉ vẽ vài thẻ thông tin trang trí.

Phạm vi gồm năm nhóm: khuyến mãi/voucher; hủy đơn, đổi trả, hoàn tiền; tồn kho và giao hàng; trợ lý AI và gợi ý sản phẩm; tài khoản, sổ địa chỉ và khách hàng thân thiết. Khuyến mãi/voucher đã có bản thiết kế nghiệp vụ, cần thể hiện đầy đủ để lấy góp ý. AI là hạng mục thiết kế bổ sung, chưa được xem là tính năng đã triển khai. Không tạo Dashboard tổng quan mới. Màn hình quản lý trong từng nghiệp vụ vẫn cần có. Không đưa thông tin sinh viên lên giao diện.

## 2. Phong cách và nhận diện

Giữ nhận diện Phở Nhà với cảm giác ấm áp, sạch, gần gũi và chuyên nghiệp. Dùng đỏ nâu #9B3B2F làm màu chính, #802D24 cho trạng thái nhấn, #F7EAE6 cho nền nhấn nhẹ. Chữ chính #292824, chữ phụ #74736C, nền quản lý #F7F8FA, nền khách hàng #FCFBF8, thẻ trắng và đường viền #E9E9E5. Thành công dùng #287354 trên nền #EDF6F0; cảnh báo #94651E trên #FFF6E7; thông tin #3F6C8E trên #EDF3F9. Hạng thành viên có sắc độ riêng nhưng không làm thay đổi hệ màu toàn hệ thống.

Dùng Be Vietnam Pro, hỗ trợ dấu tiếng Việt rõ ràng. Tiêu đề chính khoảng 28–32px trên desktop, 24px trên mobile; tiêu đề khu vực 18–20px; nội dung chính 14–16px. Hạn chế chữ nhỏ trong thông tin tiền, điều kiện và lỗi. Dùng hệ khoảng cách 4, 8, 12, 16, 24, 32px; thẻ bo góc 12–14px, trường nhập và nút bo 8px. Bóng đổ nhẹ, chủ yếu dùng đường viền để phân nhóm. Biểu tượng nét đồng nhất, không dùng emoji thay biểu tượng chức năng. Ảnh món phở phải có cùng cách cắt và tỷ lệ.

## 3. Bố cục và responsive

Thiết kế desktop 1440px, tablet 768px và mobile 390px; kiểm tra khả năng thu nhỏ đến 320px. Khách hàng dùng header có logo, điều hướng và menu tài khoản. Nội dung rộng tối đa khoảng 1230px. Khu vận hành dùng sidebar rộng 248px, thanh trên cùng cao khoảng 76px, breadcrumb và vùng nội dung có khoảng đệm nhất quán. Không tự sáng tạo một bộ khung khác cho từng module. Trên mobile, sidebar mở thành ngăn kéo; điều hướng tài khoản và bộ lọc có thể cuộn trong vùng riêng.

Mọi trang có tiêu đề, mô tả ngắn, hành động chính và đường quay lại hợp lý. Nội dung dài chia tab hoặc nhóm có tiêu đề. Không bày tất cả biểu mẫu lên một trang dài. Tạo hộp thoại hoặc trang riêng cho tác vụ cần tập trung. Bảng rộng được cuộn trong khung, không kéo ngang toàn trang. Khi chuyển tab, giữ bộ lọc và trạng thái phù hợp; khi gửi biểu mẫu, quay lại đúng phần đang làm. Nút cố định trên mobile phải chừa vùng an toàn và không che nội dung cuối.

## 4. Thư viện thành phần

Tạo thư viện dùng chung gồm nút chính, phụ, văn bản, biểu tượng; trường nhập, textarea, select, checkbox, radio, bộ chọn ngày, tải ảnh; tab, thanh tìm kiếm, bộ lọc, breadcrumb, phân trang, badge trạng thái, thẻ món, thẻ voucher, bảng dữ liệu, timeline, thanh tiến độ, toast, banner và hộp thoại xác nhận. Mỗi thành phần có trạng thái mặc định, hover, focus, nhấn, vô hiệu hóa, đang xử lý và lỗi khi phù hợp. Đặt tên theo chức năng; dùng Auto Layout, component, instance, variant và style hoặc variable nhất quán.

Mỗi trường nhập có nhãn nhìn thấy được, dấu bắt buộc khi cần, gợi ý ngắn và lỗi sát trường. Không dùng placeholder thay nhãn. Nút thao tác quan trọng có phản hồi đang xử lý để tránh bấm lặp. Hộp thoại có tiêu đề, mô tả, nút đóng, hành động phụ và chính. Thiết kế focus bàn phím rõ, vùng chạm tối thiểu 44px, độ tương phản chữ thông thường hướng đến 4,5:1. Trạng thái phải có chữ hoặc biểu tượng kèm màu. Có màn hình rỗng, skeleton, mất kết nối và thử lại.

## 5. Khuyến mãi và ví voucher

Thiết kế ví voucher trong khu tài khoản với các nhóm khả dụng, đang giữ cho đơn, đã dùng và hết hạn. Có bộ lọc giảm tiền món, freeship, quà lên hạng và đổi từ điểm. Mỗi voucher là một thẻ thống nhất: mức giảm nổi bật ở bên trái; tên chương trình, đơn tối thiểu, mức giảm tối đa, phạm vi món, khoảng cách áp dụng, hạn dùng và nút sử dụng ở bên phải. Thẻ hết hạn hoặc chưa đủ điều kiện vẫn giải thích được lý do; không chỉ làm mờ toàn bộ nội dung.

Hộp chi tiết voucher trình bày điều kiện theo thứ tự dễ đọc: giá trị, đối tượng, món áp dụng, thời gian, số lượt, cách kết hợp và trường hợp không áp dụng. Phân biệt mã chiến dịch nhập tay với voucher cá nhân trong ví. Tại checkout, khách chọn một voucher hoặc nhập một mã; lựa chọn mới thay lựa chọn cũ và cập nhật tổng tiền. Có phản hồi cho mã sai, chưa tới hạn, hết hạn, hết lượt, đơn chưa đủ tiền và món không thuộc chương trình. Không dùng thông báo chung chung như “Có lỗi”.

## 6. Đổi điểm và tính tiền

Thiết kế danh mục đổi điểm thành các thẻ quà gồm ưu đãi nhận được, điểm cần đổi, điều kiện, số ngày sử dụng và trạng thái còn quà. Dùng dữ liệu mẫu: 100 điểm đổi voucher 10.000đ, 200 điểm đổi 20.000đ, 500 điểm đổi 50.000đ; hạn mẫu 30 ngày. Ghi đây là cấu hình minh họa trong chú thích thiết kế. Trước xác nhận, hiển thị số điểm bị trừ, số dư còn lại và voucher nhận vào ví. Có trạng thái thiếu điểm, hết quà, đang đổi, thành công và thất bại không mất điểm.

Checkout hiển thị lần lượt tiền món, giảm theo hạng, giảm voucher, phí giao, miễn giao theo hạng hoặc voucher giao, điểm sử dụng và tổng phải trả. Không hiển thị hàng giảm bằng không nếu gây nhiễu. Chiết khấu hạng tự động; tối đa một voucher mỗi đơn; điểm dùng sau ưu đãi, 1 điểm bằng 100đ và tối đa 50% số tiền còn lại. Đổi điểm lấy voucher chỉ trừ điểm lúc đổi, không trừ lại khi dùng mã. Ví dụ đơn 55.000đ, voucher 10.000đ và 10 điểm phải hiển thị tổng 44.000đ.

## 7. Quản lý chương trình ưu đãi

Thiết kế trang Khuyến mãi & đổi điểm trong khung vận hành, chia tab Mã chiến dịch, Quà đổi điểm và Hạng thành viên. Có tìm kiếm theo mã hoặc tên, lọc đang chạy, sắp diễn ra, hết hạn và đã tắt. Bảng thể hiện chương trình, loại giảm, thời gian, giới hạn và trạng thái. Tạo hoặc sửa bằng hộp thoại có nhóm thông tin, giá trị, điều kiện và thời gian. Bao gồm mã, tên, loại, giá trị, trần giảm, đơn tối thiểu, món áp dụng, lượt tổng, lượt mỗi khách và bật/tắt. Lỗi giữ nguyên dữ liệu đã nhập. Giải thích rằng sửa cấu hình không thay quyền lợi đã phát hoặc giá đơn cũ.

## 8. Hủy đơn và báo sự cố

Trang chi tiết đơn có nhóm hành động hỗ trợ dễ thấy nhưng không lấn át trạng thái đơn. Thiết kế luồng hủy trước chế biến và báo món lỗi, giao thiếu, giao nhầm hoặc giao không thành công. Với món ăn, “đổi trả” được diễn đạt bằng làm lại, giao bù hoặc hoàn phần được duyệt; không dùng quy trình gửi trả hàng nguyên kiện của sản phẩm thông thường. Khách chọn lý do, phần món, số suất và phương án mong muốn. Hiển thị phần đã nằm trong yêu cầu khác để tránh gửi trùng.

Biểu mẫu hỗ trợ chia bước: xác định nhu cầu, chọn phần cần xử lý, mô tả và xem lại. Hủy toàn bộ đơn không yêu cầu chọn từng món. Đơn đã chế biến hoặc đang giao có thông báo cần cửa hàng kiểm tra. Báo sự cố sau hoàn tất dùng cửa sổ tiếp nhận mẫu hai giờ, ghi rõ chính sách mẫu trong annotation. Cho nhập mô tả và thông tin bằng chứng; phương án tải ảnh nếu chưa triển khai được đánh dấu đề xuất. Trước gửi, khách biết yêu cầu chưa đồng nghĩa được duyệt và thấy giá trị dự tính dựa trên phần đã trả.

## 9. Hoàn tiền và tiến độ hỗ trợ

Thiết kế trang theo dõi yêu cầu với mã yêu cầu, mã đơn, thời gian, lý do, phần món, phương án và timeline. Các trạng thái gồm chờ xét duyệt, cần bổ sung nếu được áp dụng, đã duyệt, từ chối có lý do, chờ đối soát hoàn, hoàn tiền thành công, đang cập nhật quyền lợi, đang giao bù và hoàn tất. Tách trạng thái yêu cầu khỏi trạng thái đơn và thanh toán. Đơn hủy vẫn có thể đang chờ hoàn; không dùng một badge “Đã hủy” để thay toàn bộ thông tin tài chính.

Thông tin hoàn tách tiền thực trả, điểm đã dùng được phục hồi, điểm thưởng bị điều chỉnh và voucher được khôi phục khi đủ điều kiện. Không trình bày giảm giá thành tiền mặt được nhận. Hoàn một phần dựa trên giá trị phân bổ của đơn gốc, không dựa giá thực đơn mới. Voucher đổi từ điểm không vừa được trả lại mã vừa được hoàn điểm mua mã. Khi kết quả chuyển tiền chưa rõ, hiển thị đang xác minh và không đưa nút tạo lệnh chi mới. Đơn giao bù có liên kết theo dõi và giá thanh toán bằng không.

## 10. Màn hình nhân viên xử lý

Tạo danh sách hỗ trợ có tìm kiếm mã đơn, bộ lọc trạng thái và thẻ yêu cầu mở rộng. Phần thu gọn cho biết mã đơn, loại, tóm tắt, thời gian và trạng thái; mở ra mới thấy bằng chứng, phần món và biểu mẫu xử lý. Quản lý có nút duyệt, từ chối và tạo giao bù theo điều kiện. Thu ngân chỉ thấy hành động được phép. Khoản hoàn có số tiền, chứng từ nguồn, mã lệnh và kết quả đối soát. Xác nhận thành công phải nhập bằng chứng. Nếu trạng thái đã đổi ở nơi khác, thông báo tải lại và giữ nội dung người dùng đang nhập khi có thể.

## 11. Tồn kho và định lượng

Thiết kế trang kho với tab Nguyên liệu, Định lượng món, Lịch sử xuất nhập và Sự cố kho. Bảng nguyên liệu gồm tên, đơn vị, tồn theo sổ, đang giữ, khả dụng và ngưỡng tối thiểu. Giải thích ngắn “Khả dụng = tồn theo sổ − đang giữ”. Dùng tên nguyên liệu thật như bánh phở, thịt bò, nước dùng; số lượng có đơn vị g hoặc ml. Có tìm kiếm, lọc cần nhập, hết hàng, đang giữ và đang khóa. Khách hàng chỉ thấy món còn hoặc tạm hết, không thấy số tồn nguyên liệu nội bộ.

Nhập kho dùng hộp thoại chọn nguyên liệu, số lượng và đơn vị; hiển thị quy đổi trước xác nhận nếu nhập kg sang g hoặc lít sang ml. Thêm định lượng chọn món chính hoặc topping, rồi nguyên liệu và lượng cho một đơn vị bán. Không cho hai loại sản phẩm cùng được chọn trong một dòng. Màn hình chi tiết thể hiện nguyên liệu đã giữ cho đơn, hạn giữ mẫu 15 phút và kết quả thanh toán. Giữ hàng không phải xuất kho; hủy chưa trả giải phóng giữ. Đơn thanh toán chuyển lượng giữ thành xuất, không trừ hai lần.

## 12. Sự cố kho và giao hàng

Thiết kế trạng thái hết hàng giữa lúc khách xem và xác nhận: nêu món thiếu, số lượng có thể đặt và hai hướng giảm số lượng hoặc chọn món khác. Khi giữ hết hạn, yêu cầu xem lại giá và tồn trước đặt lại. Hoàn nguyên liệu chỉ áp dụng phần đã xuất nhưng chưa dùng, có xác nhận từ bếp. Món đã chế biến ghi hao hụt. Biểu mẫu chọn mã đơn thay nhập ID kỹ thuật; chỉ hiện nguyên liệu thuộc phiếu xuất. Sự cố kiểm kê có nguyên liệu bị khóa, lý do, lượng cam kết và kết quả xử lý.

Giao hàng có bảng hoặc thẻ lọc chờ bàn giao, đang giao, sự cố và hoàn tất. Thẻ chứa mã đơn, người nhận, điện thoại, địa chỉ, ghi chú, phí, khoảng cách, người giao và lịch sử lượt giao. Phân biệt sẵn sàng bàn giao, đã bàn giao và người nhận đã nhận món. Thất bại cần lý do; có hướng giao lại hoặc mang về cửa hàng. Khách xem timeline và liên hệ hỗ trợ. Không vẽ vị trí tài xế chạy trực tiếp như dữ liệu thật khi chưa có tích hợp; bản đồ minh họa phải có nhãn tương ứng.

## 13. Trợ lý AI

Thiết kế trợ lý AI dưới dạng nút nổi gọn ở khu khách hàng, mở thành panel trên desktop và màn hình hội thoại trên mobile. Nút không che giỏ hàng hoặc hành động thanh toán. Có lời chào ngắn, nhãn “Trợ lý AI”, nút đóng, bắt đầu hội thoại mới và chuyển hỗ trợ cửa hàng. Gợi ý câu hỏi đầu gồm chọn phở theo ngân sách, tìm món còn phục vụ, giải thích voucher, quyền lợi hạng và hướng dẫn xem đơn. Dùng bố cục hội thoại dễ đọc, không biến thành trang quảng cáo hoặc màn hình phân tích kỹ thuật.

Trợ lý hỏi làm rõ nhu cầu bằng lựa chọn ngắn: số người, ngân sách, khẩu vị, muốn món chính hay đồ uống, ăn tại quán hay giao. Câu trả lời về giá, tồn, phí, voucher và đơn phải dựa dữ liệu được phép và có liên kết xem chi tiết hoặc thời điểm cập nhật. Khi thiếu dữ liệu, hiển thị chưa xác nhận được và đề xuất kiểm tra lại. Không bịa giá, mã, chính sách hoặc trạng thái đơn. Với thành phần và dị ứng, chỉ cung cấp thông tin đã xác nhận và hướng khách kiểm tra với cửa hàng khi chưa rõ; không cam kết an toàn từ suy đoán.

## 14. Gợi ý món và quyền riêng tư AI

Thiết kế thẻ gợi ý ngay trong chat với ảnh, tên món, giá hiện tại, trạng thái phục vụ và lý do phù hợp. Có xem chi tiết, chọn tùy chỉnh và thêm vào giỏ. Gợi ý phải tính cả topping và phụ phí đã chọn khi so ngân sách. Món hết được thay bằng lựa chọn tương đương, có giải thích. Cá nhân hóa lịch sử đặt chỉ dùng khi khách đồng ý; luôn có chế độ gợi ý không dùng lịch sử. Tra cứu đơn yêu cầu đăng nhập hoặc phiên có quyền, không lộ đơn khác chỉ từ mã nhập vào.

AI chỉ giải thích, tìm kiếm và đề xuất. Áp voucher, dùng điểm, đặt món hoặc gửi yêu cầu hoàn phải chuyển qua màn hình nghiệp vụ và bước xác nhận tương ứng. Không để câu trả lời trong chat tự tạo giao dịch. Vẽ các tình huống đang tìm dữ liệu, trả lời từng phần, bị gián đoạn, dịch vụ không khả dụng, ngoài phạm vi, không có món phù hợp và chuyển nhân viên. Với ngân sách 150.000đ cho hai người, tạo một hội thoại mẫu chọn hai món còn bán, giải thích tổng dự tính và hỏi khách có muốn mở giỏ để xem phí giao.

## 15. Hồ sơ và nhiều tài khoản

Trang tài khoản có các tab Hồ sơ cá nhân, Sổ địa chỉ, Thành viên & điểm và Đơn của tôi. Hồ sơ hiển thị họ tên, điện thoại, email, ngày sinh, giới tính; phần bảo mật tách riêng. Avatar tròn, có chọn ảnh, xem trước và lưu; chấp nhận JPG, PNG, WEBP tối đa 5MB. Có lỗi tệp không hợp lệ, quá dung lượng, ngày sinh tương lai và email sai. Đổi mật khẩu gồm mật khẩu hiện tại, mật khẩu mới và nhập lại; có hiện/ẩn và hướng dẫn dễ hiểu. Không cho chỉnh vai trò, hạng hoặc số dư ngay trong hồ sơ.

Menu tài khoản ở header hiển thị avatar, tên và tài khoản đang dùng. Danh sách phiên cho chuyển nhanh, thêm tài khoản và đăng xuất tài khoản hiện tại. Phiên hết hạn dẫn tới xác thực lại. Sau chuyển, tên, giỏ và dữ liệu cá nhân phải đổi đồng bộ. Tab cũ có thông báo tài khoản đã thay đổi và yêu cầu tải lại trước thao tác nhạy cảm. Không mô tả việc lưu mật khẩu vào trình duyệt để chuyển nhanh. Các thao tác bảo mật có phản hồi rõ nhưng không lộ chi tiết kỹ thuật như token, khóa phiên hoặc cấu trúc máy chủ.

## 16. Sổ địa chỉ

Danh sách địa chỉ dùng thẻ Nhà riêng, Văn phòng hoặc Khác, có người nhận, điện thoại, địa chỉ đầy đủ, ghi chú và badge Mặc định. Hành động gồm thêm, sửa, xóa và đặt mặc định. Chỉ một địa chỉ mặc định cho mỗi tài khoản. Khi còn nhiều địa chỉ, không cho xóa địa chỉ mặc định trước khi chọn địa chỉ khác; giải thích ngay cạnh hành động. Form chia thông tin người nhận, địa chỉ và vị trí giao. Bao gồm số nhà/đường, Phường/Xã, Quận/Huyện nếu hệ dữ liệu yêu cầu và Tỉnh/Thành phố; tránh tạo bộ chọn địa danh mẫu như dữ liệu hành chính thật.

Cho chọn vị trí nhận món bằng bản đồ đề xuất hoặc lấy vị trí hiện tại có sự cho phép. Có trạng thái từ chối quyền vị trí, không xác định được khoảng cách và ngoài phạm vi giao. Không buộc khách hiểu tọa độ kỹ thuật trong luồng chính. Checkout điền sẵn địa chỉ mặc định, cho chọn địa chỉ khác và nhập mới. Khi đổi địa chỉ phải cập nhật phí, freeship và báo giá. Sửa hoặc xóa địa chỉ đã lưu không thay địa chỉ của đơn cũ. Bản chụp địa chỉ đơn được trình bày riêng trong chi tiết đơn hàng.

## 17. Điểm, nguồn thưởng và lịch sử

Khu thành viên tách rõ điểm khả dụng và tổng chi tiêu xét hạng. Hiển thị thêm điểm đang giữ, sắp hết hạn và điểm cần bù nếu phát sinh. Mua hàng tích 1 điểm cho mỗi 10.000đ thực trả tiền món sau ưu đãi khi đơn hoàn tất; phí giao không tích điểm theo chính sách thiết kế hiện có. Điểm có hạn 12 tháng và dùng điểm tích trước. Lịch sử có nguồn, thời gian, số cộng/trừ, hạn và liên kết đơn. Bộ lọc gồm mua hàng, đánh giá, điểm danh, giới thiệu, đổi voucher, dùng điểm, hết hạn và điều chỉnh hoàn tiền.

Thiết kế điểm danh bảy ô ngày, ngày thứ bảy nhận gấp đôi. Ví dụ cấu hình một điểm/ngày, hai điểm ngày thứ bảy; mức này ghi là mẫu trong annotation. Đánh giá có sao và nội dung; phần thưởng mẫu năm điểm cho đánh giá đủ điều kiện, không yêu cầu đánh giá tích cực để nhận thưởng. “Đánh giá tốt” xét hạng là từ bốn sao và bình luận ít nhất hai mươi ký tự. Mã giới thiệu có sao chép, chia sẻ và trạng thái chờ đơn đầu hoàn tất; ví dụ thưởng năm mươi điểm mỗi bên, không hiển thị đã nhận khi chưa đủ điều kiện.

## 18. Hạng và đặc quyền

Thiết kế thẻ hạng hiện tại và thanh tiến độ thể hiện đồng thời số tiền cùng số đánh giá tốt còn thiếu. Thành viên mặc định giảm 0%; Đồng từ 500.000đ và hai đánh giá tốt, giảm 2%; Bạc từ 2.000.000đ và hai đánh giá tốt, giảm 5%; Vàng từ 5.000.000đ, giảm 7%; Kim Cương từ 12.000.000đ, giảm 10%. Điều kiện hai đánh giá cho Vàng và Kim Cương là chính sách kế thừa đề xuất, cần ghi trong annotation. Không thông báo đủ tiền là chắc chắn lên hạng khi điều kiện đánh giá còn thiếu.

Thể hiện đúng gói lên hạng: Đồng một mã 20%, trần 100.000đ; Bạc ba mã tương tự, tổng tối đa 300.000đ; Vàng một mã tặng một món dưới 100.000đ và hai mã 25%, mỗi mã trần 150.000đ, tổng tối đa 400.000đ. Kim Cương gồm ba mã tặng món dưới 100.000đ, một mã 30% trần 200.000đ và ba mã 25% trần 150.000đ, tổng tối đa 950.000đ. Đây là giá trị ưu đãi tối đa có điều kiện, không phải tiền mặt được tặng. Món giá đúng 100.000đ không thuộc điều kiện “dưới 100.000đ”.

Bạc có hai mã freeship mỗi tháng. Vàng miễn giao trong phạm vi gần và ba mã giao trên 5km mỗi tháng. Kim Cương miễn giao gần và mười mã giao trên 5km mỗi tháng. Mốc đúng 5km thuộc vùng gần là mặc định đề xuất; biểu diễn khoảng cách rõ quanh ngưỡng. Freeship tự động không chiếm vị trí voucher trong ví. Tách mã tháng khỏi quà lên hạng. Bạc trở lên có khu quà sinh nhật; Vàng và Kim Cương có quyền lợi đặc biệt và hotline VIP khi đã cấu hình. Không bịa số hotline hoặc quà thật khi chưa có dữ liệu.

## 19. Prototype và bàn giao

Tạo prototype xuyên suốt: chọn món, nhận gợi ý AI, mở giỏ, chọn địa chỉ, áp voucher, dùng điểm, xác nhận và theo dõi đơn. Nối tiếp nhánh hủy trước chế biến, báo giao thiếu, xét duyệt, hoàn tiền hoặc giao bù. Có hành trình đổi điểm nhận voucher rồi sử dụng, điểm danh, giới thiệu và kiểm tra điều kiện lên hạng. Khu vận hành nối nhập kho, định lượng, đơn giữ nguyên liệu, bàn giao, giao thất bại và giao lại. Các nút chính phải có đích; không để nguyên mẫu chỉ gồm nhiều frame đứng riêng.

Tổ chức file thành các trang nền tảng, thành phần, khách hàng, vận hành, AI và prototype. Đặt tên frame theo module, màn hình, thiết bị và trạng thái. Tách annotation khỏi nội dung khách nhìn thấy. Chỉ rõ yêu cầu nguồn, chính sách mẫu và chức năng đề xuất. Dữ liệu mẫu phải thống nhất giữa số dư điểm, hạng, mã, khoảng cách, đơn và số hoàn. Trước bàn giao, rà từng màn hình ở desktop/mobile, lỗi nhập liệu, trạng thái rỗng, đang tải, hết hạn, xung đột và thành công. Kết quả cần là bộ giao diện có thể thảo luận, kiểm tra luồng và phát triển tiếp.

Bổ sung một trang riêng kiểm tra tính nhất quán gồm các tình huống có cùng một khách hàng xuyên suốt toàn bộ hành trình. Khi thay địa chỉ, so sánh phí giao trước và sau; khi đổi voucher, kiểm tra điểm và tổng tiền; khi hoàn một phần, giữ nguyên thông tin đơn gốc. Đánh dấu rõ những màn hình chưa có dữ liệu xác thực bằng annotation dành cho nhóm thiết kế, đồng thời chuẩn bị trạng thái hiển thị phù hợp cho người dùng cuối cùng.
