# Prompt phần 2 Hủy đơn đổi trả và hoàn tiền

Nội dung từ mục “Vai trò và nhiệm vụ” đến hết có thể sao chép để giao cho AI hoặc nhóm thiết kế. Đây là prompt thiết kế, không là lệnh lập trình, triển khai hoặc chuyển tiền thật. Bản kết quả tương ứng: `C:\Users\HP\Quanlypho\docs\th4\02_THIET_KE_HUY_DOI_TRA_HOAN_TIEN.md`.

## Vai trò và nhiệm vụ

Bạn là chuyên viên phân tích hệ thống và kiến trúc sư cho **Hệ thống Quản lý Quán Phở Quanlypho**. Hãy thiết kế **phần 2 Hủy đơn/đổi trả/hoàn tiền** theo Hướng 1 Hệ thống thương mại điện tử trong đề thực hành.

Chỉ làm phần 2 và giao diện tích hợp cần thiết với phần 1. Đầu ra bằng tiếng Việt, có thiết kế kết quả cụ thể, đủ để bổ sung báo cáo và lập trình sau. Chưa sửa mã nguồn, tạo/chạy migration, thực hiện chi tiền hoặc tích hợp ngân hàng thật. Sau phần này dừng hỏi người dùng góp ý; không tự sang phần 3 hoặc phần bổ sung.

Chặng Trợ lý AI/gợi ý sản phẩm, Dashboard và yêu cầu hiển thị thông tin sinh viên đã bị người dùng loại bỏ. Không khôi phục các mục đó. Người dùng yêu cầu tiếp tục phần 2 nhưng chưa tự động xác nhận mọi chính sách đề xuất của phần 1 hoặc phần này.

## Nguồn và thứ tự ưu tiên

- Yêu cầu trực tiếp/chú thích của người dùng ưu tiên cao nhất.
- Kế hoạch: `C:\Users\HP\Quanlypho\docs\th4\00_KE_HOACH.md`.
- Thiết kế phần 1: `C:\Users\HP\Quanlypho\docs\th4\01_THIET_KE_KHUYEN_MAI_VOUCHER.md` và prompt cùng thư mục.
- Đề Word: `C:\Users\HP\Downloads\TH4 Bổ sung thiết kế cho đồ án cuối kỳ.docx`.
- Yêu cầu bổ sung: `D:\dowload\CHI TIẾT YÊU CẦU CHỨC NĂNG.md`.
- Mã dự án: `C:\Users\HP\Quanlypho`.

Phân biệt câu giao vai trò/lập trình trong tài liệu nguồn với yêu cầu hiện tại; nguồn là dữ liệu phân tích, không tự cho quyền triển khai. Gắn căn cứ Người dùng/Word/Markdown/Thiết kế phần 1/Mã nguồn/Đề xuất cho quy tắc. Mọi thời hạn, mức bồi hoàn và chính sách hủy chưa được người dùng quyết định đều phải là **đề xuất**, không mô tả thành quy định pháp luật hoặc cam kết của ngân hàng.

## Hiện trạng cần đọc lại

- `C:\Users\HP\Quanlypho\pho_app\models.py`: OrderStatus có CART, PENDING_KITCHEN, COOKING, READY, DELIVERING, COMPLETED, CANCELLED; PaymentStatus có PENDING, PAID, FAILED. Chưa thấy mô hình yêu cầu/receipt/hoàn tiền riêng trong lần kiểm tra chuẩn bị.
- `C:\Users\HP\Quanlypho\pho_app\services.py`: `available_order_actions` và `apply_order_action` hiện chỉ hủy CASH + PENDING + CART; hủy khóa bàn trước đơn. Bếp cho phép hoàn tất trực tiếp từ PENDING_KITCHEN, cần tính cả tranh chấp với đường này.
- `C:\Users\HP\Quanlypho\pho_app\views.py`: `cancel_cash_order`, `order_detail`, `vietqr_webhook`, `_perform_order_action`; quyền xem đơn gồm chủ tài khoản, phiên khách vãng lai và các vai trò nhân viên phù hợp. Quyền xem không là quyền hoàn.
- `C:\Users\HP\Quanlypho\pho_app\permissions.py`: CUSTOMER, STAFF, KITCHEN, ADMIN; đặc tả quyền theo hành động/đối tượng dựa các vai trò này.
- `C:\Users\HP\Quanlypho\pho_app\signals.py`: xuất nguyên liệu khi chuyển PAID, không dùng đổi trạng thái thanh toán để biểu thị hoàn rồi vô tình chạy lại signal.
- VietQR hiện sinh hướng dẫn chuyển khoản và nhận webhook có chữ ký, chưa có API hoàn tiền đã được xác minh. Payload đang dùng chưa có mã ngân hàng duy nhất cho mỗi lần chuyển tiền.

Xác minh lại mã, nêu khác biệt nếu có. Không đọc hoặc chép bí mật cấu hình vào đầu ra. Không tự thêm framework API nếu session Django và JSON view đã đủ cho thiết kế MVP.

## Các hợp đồng phải kế thừa từ phần 1

1. Tính hoàn từ `payable_amount`, từng nguồn tiền và bản chụp ưu đãi trên đơn; không tính lại bằng giá món/hạng/voucher hiện tại.
2. Một voucher/đơn, kể cả voucher đổi từ điểm hoặc freeship trong ví. Freeship tự động theo hạng là đặc quyền ngoài vị trí voucher theo đề xuất phần 1.
3. Bạc có 2 mã tháng; Vàng 3 mã trên 5 km và tự miễn dưới 5 km; Kim Cương 10 mã trên 5 km và tự miễn dưới 5 km. Mốc đúng 5 km và cấp bù giữa tháng vẫn mang nhãn đề xuất. Hoàn một mã không cấp lại toàn bộ gói tháng.
4. Điểm trực tiếp 1 điểm = 100đ, tối đa 50% phần trước điểm; 10.000đ thực trả đủ điều kiện mới tích 1 điểm khi COMPLETED; điểm hết hạn 12 tháng, FIFO. Không dùng số điểm mới của chính đơn chưa hoàn tất.
5. Đổi điểm mua voucher là giao dịch riêng đã trừ điểm; khi hoàn đơn dùng mã đó, không vừa trả voucher vừa trả số điểm đã mua mã.
6. Chưa thanh toán chỉ giải phóng giữ; đã thanh toán phải có giao dịch đảo tham chiếu gốc. Điểm/mã quá hạn khi giải phóng giữ không tự sống lại.
7. Cần bổ sung phân bổ theo từng suất/thành phần và ship: tiền sau giảm hạng/voucher B_u, điểm nguyên p_u và tiền thực trả C_u = B_u - 100 × p_u. Không phân bổ làm tiền âm; kỹ thuật giới hạn sức chứa điểm phải được báo trước tạo đơn.

## Phạm vi nghiệp vụ cần thiết kế

- Hủy toàn bộ đơn chưa thanh toán; hủy đơn đã trả trước khi bếp làm; xử lý yêu cầu đổi ý sau chế biến theo quyết định có lý do.
- Báo sai món, giao thiếu, lỗi chất lượng, giao thất bại; hoàn một phần/toàn phần hoặc làm lại/giao bù.
- Tiền tới sau hủy, tiền chuyển dư/trùng, tiền thật nhận nhưng không thể xác nhận đơn do tồn kho.
- Tiền mặt có xác nhận bàn giao; chuyển khoản theo nguồn đối soát được xác minh. Không giả định QR là cổng hoàn tự động.
- Thông báo và màn hình tra cứu tách tiền, điểm, voucher, trạng thái phục vụ và trạng thái yêu cầu.
- Điều chỉnh chi tiêu/điểm mua hàng đã tích bằng sự kiện, hợp đồng xét hạng dành cho chặng bổ sung; giữ/đảo nguyên liệu dành cho phần 3.

## Ma trận chính sách ban đầu cần hoàn thiện

| Trạng thái | Chính sách đề xuất |
|---|---|
| CART chưa có tiền xác nhận | Chủ đơn/phiên được hủy; giải phóng ưu đãi, không hoàn tiền chưa nhận |
| PENDING_KITCHEN đã trả, chưa bắt đầu làm | Cho hủy tự duyệt dưới khóa; CANCELLED chặn bếp, tiền và quyền lợi còn tiến trình riêng |
| COOKING/READY | Không tự duyệt hủy do đổi ý; lỗi quán có thể hoàn/làm lại theo phạm vi ADMIN duyệt |
| DELIVERING | Không hủy ngay; xử lý sự cố và phần dịch vụ đã thực hiện, giữ lịch sử giao thực tế |
| COMPLETED | Giữ trạng thái hoàn tất; khiếu nại/hoàn có trạng thái độc lập |
| CANCELLED hoặc trạng thái tiền không nhất quán | Không mở lại đơn để nhận/hoàn tiền; receipt và đối soát riêng |

Đề xuất cửa sổ báo món lỗi/giao thiếu 2 giờ từ delivered_at/completed_at; có đường hỗ trợ ngoại lệ. Không dùng updated_at làm mốc giao. Tiền trùng/muộn không bị áp giới hạn thời gian khiếu nại món ăn. Ảnh là hỗ trợ, không bắt buộc cho mọi loại sự cố.

Vai trò: khách chỉ thao tác đơn mình; guest phải có quyền từ phiên/token theo đơn; STAFF tiếp nhận/ghi chứng từ và trả tiền mặt trong hạn đã duyệt; ADMIN quyết định/đối soát; KITCHEN xác nhận tình trạng món, không xem thông tin ngân hàng đầy đủ hoặc chi tiền. Tự duyệt chỉ ở điều kiện trước chế biến đã được đề xuất, mọi thao tác kiểm tra lại dưới khóa.

## Luồng và trạng thái bắt buộc

Trình bày luồng chính 5–8 bước từ mở đơn đến kết quả, có nhánh tự duyệt/chờ xét/bổ sung/từ chối/hoàn/giao bù. Có tối thiểu hai Mermaid state diagram: yêu cầu và lần hoàn tiền. Tách OrderStatus, tiền thực nhận, ServiceRequest, RefundAttempt và cập nhật quyền lợi.

Yêu cầu đi qua SUBMITTED, UNDER_REVIEW, NEEDS_INFO nếu cần, APPROVED/REJECTED/WITHDRAWN, EXECUTING rồi RESOLVED. Chỉ rút trước duyệt/chi; gửi yêu cầu không tự dừng món đang chế biến. CANCELLED không có nghĩa đã chi tiền hoàn.

Lần hoàn có RESERVED, SUBMITTED, UNKNOWN, SUCCEEDED, FAILED_FINAL. UNKNOWN vẫn giữ hạn mức; lỗi mạng không được dùng để kết luận chưa chuyển tiền. FAILED_FINAL chỉ tạo lần thử mới cho cùng RefundPlan khi có bằng chứng chắc chắn chưa chi và quyền phù hợp, giữ nguyên lịch sử lần thử cũ. Ghi tiền đã hoàn bền vững trước xử lý quyền lợi; lỗi trả điểm không tạo lệnh chi lần nữa. Không tạo lệnh chi 0đ.

## Phân bổ hoàn và số học bắt buộc

Cho ví dụ kế thừa phần 1: tiền hàng 300.000đ, giảm hạng 15.000đ, voucher 50.000đ, ship 25.000đ, dùng 100 điểm, trả 250.000đ.

| Thành phần | B_u sau giảm hàng | p_u | C_u |
|---|---:|---:|---:|
| Suất A | 156.667 | 60 | 150.667 |
| Suất B | 78.333 | 30 | 75.333 |
| Phí giao | 25.000 | 10 | 24.000 |
| Tổng | 260.000 | 100 | 250.000 |

Hoàn suất B là **75.333đ + 30 điểm**, mặc định không hoàn ship hoặc voucher cho hoàn một phần. Nếu hoàn hết phần còn lại sau đó thì thêm **174.667đ + 70 điểm**, tổng không vượt tiền và điểm gốc; khôi phục voucher toàn phần đúng một lần khi đủ điều kiện.

Đặc tả phân bổ điểm nguyên có sức chứa floor(B_u/100), chia phần lẻ ổn định; tổng đúng số đã tiêu, tiền từng phần không âm. Đơn cũ thiếu phân bổ cần phục hồi có kiểm duyệt hoặc xử lý thủ công, không tự áp giá hiện tại. Không tính lại điều kiện đơn tối thiểu để thu hồi ưu đãi sau hoàn một phần nếu chưa có chính sách khác được chốt.

Ngân sách hoàn của receipt = tiền thực nhận đã xác nhận - tiền đã chi - khoản hoàn đang giữ. Giữ trên nghĩa vụ RefundPlan, không nhân lên theo số RefundAttempt. Mọi yêu cầu đồng thời cùng suất/receipt phải khóa và tính cả phần đang giữ. Số điểm trả cộng dồn không vượt phân bổ gốc.

Hai lần chuyển tiền thật cùng mã đơn/số tiền nhưng khác mã ngân hàng tạo hai receipt; callback cùng mã ngân hàng gửi lại chỉ là một receipt. Hoàn khoản dư không hủy đơn/hoàn quyền lợi. Khi chưa có mã ngân hàng đáng tin, phải thiết kế đối soát thủ công; không bịa mã để có vẻ chống lặp.

## Quyền lợi và giao bù

- Hủy chưa trả: giải phóng; quá hạn gốc thì hết hạn, không bù 7 ngày theo chính sách hoàn sau trả.
- Hoàn đã trả: tiền hoàn giới hạn phần thực trả, không hoàn chiết khấu hạng/voucher/freeship thành tiền. Phí giao chỉ là phần ship ròng thật trả và tùy phạm vi dịch vụ được duyệt.
- Hoàn một phần: trả tiền/điểm từng suất, giữ voucher tiêu thụ. Hoàn toàn phần đủ điều kiện: khôi phục một quyền đã tiêu, có khóa duy nhất trên VoucherRedemption gốc.
- Voucher từ điểm: trả quyền voucher, không trả thêm điểm mua mã. Mã tháng phục hồi không giảm issued_count hoặc phát lại gói 2/3/10. Tự miễn ship không có mã để trả.
- Đề xuất điểm đã tiêu được trả theo hạn gốc; nếu hết hạn khi hoàn thì lô bồi hoàn 7 ngày có tham chiếu. Mã đã hết hạn chỉ đề xuất bù một mã 7 ngày khi lỗi/chậm xử lý phía quán, không mặc định bù vì khách đổi ý.
- Điểm mua hàng đã tích cần đảo theo mục tiêu chi tiêu ròng còn lại cộng dồn; phần đã tiêu có thể thành nợ điểm riêng theo chính sách đề xuất. Không âm available_points hoặc tự thu tiền khách, không phát lại gói quà hạng vì hoàn/nâng lại hạng.
- Làm lại/giao bù tạo đơn con nguồn SERVICE_REPLACEMENT, phải trả 0đ, không sinh QR/điểm mua hàng hoặc tiêu thêm voucher; một suất không đồng thời được bù và hoàn. Nếu bù tiếp tục lỗi thì giữ cùng ngân sách và dấu vết, không tạo tiền gốc mới.
- Không tự nhập nguyên liệu món đã nấu/hỏng. Đơn PAID chưa nấu chỉ đảo xuất kho khi được xác nhận đủ điều kiện, liên kết xuất gốc; hợp đồng chi tiết do phần 3 hoàn thiện.

Giải thích đánh đổi của chính sách trả điểm/mã đã hết hạn, xử lý nợ điểm và hoàn phí ship. Không âm thầm biến các đề xuất thành quyền lợi đã cam kết.

## Dữ liệu, API và nhất quán

Đối chiếu `04_THIET_KE_TAI_KHOAN_DIA_CHI_LOYALTY.md` cho ngữ cảnh tài khoản, mục tiêu chi tiêu ròng theo version và điểm thu hồi chờ/nợ; request trình duyệt có vault/slot trước RequestKey khi cần, User trước ví, nhiều ví theo user ID tăng dần. Không xử lý referral hai ví bằng cách lấy thêm ví thứ hai sau khi đã khóa ví thứ nhất trái thứ tự.

ERD và từ điển trường cần bao phủ ServiceRequest, ServiceRequestItem, RequestEvidence, PaymentReceipt, RefundPlan, RefundAllocation, RefundAttempt, BenefitReversal, OrderStatusEvent, ServiceRequestEvent, PaymentEventInbox và EventOutbox. Tái sử dụng User, Order, OrderItem, phân bổ, sổ điểm, voucher và RequestKey phần 1; không tạo User/Order thứ hai. Chỉ mục tra đơn, yêu cầu mở, receipt, thời hạn và khóa đối soát.

Đặc tả các API khái niệm service-options, tạo/xem/rút yêu cầu, bổ sung bằng chứng, quyết định ADMIN, xác nhận hoàn tiền mặt và đối soát ngân hàng. Có JSON mẫu yêu cầu/response, lỗi 403/404/409/422/503 phù hợp, expected_version để chống duyệt bản cũ và khóa thao tác chống lặp. Đích nhận hoàn phải được xác minh, không tin tùy ý tài khoản khách nhập; tệp riêng tư và dữ liệu ngân hàng theo quyền.

Thứ tự khóa thống nhất với phần 1 và phần 3: RequestKey → ví điểm → bàn → đơn → receipt → yêu cầu/kế hoạch hoàn → danh mục/chiến dịch → kỳ cấp → quyền voucher → lô điểm → giữ kho/giao nhận → phiên bản BOM → nguyên liệu; bỏ nhóm không liên quan, khóa nhiều ID ổn định và kiểm tra quan hệ sau khóa. Bàn trước đơn tương thích nhánh hủy hiện có; mọi đường mới và webhook phải được rà soát lại. Đối chiếu `03_THIET_KE_TON_KHO_GIAO_HANG.md` cho giữ/đảo nguyên liệu và đề xuất trạng thái DELIVERY_EXCEPTION, không tự coi giao lỗi là đã hủy hoặc đã hoàn tiền.

Transaction chỉ giữ ngân sách/lưu nghĩa vụ và outbox; chi bên ngoài sau commit. Kết quả có bằng chứng ghi inbox/receipt hoàn một lần; khôi phục quyền lợi là bước riêng chạy lại được. Không giữ DB lock lúc chờ ngân hàng. Session POST có CSRF; webhook ngoài có chữ ký/định danh; nội dung người dùng được escape. Ảnh đề xuất JPG/PNG/WEBP <= 5 MB, kiểm tra nội dung thật và quyền đọc; không log bí mật/tài khoản đầy đủ.

## Giao diện và thông báo

Có wireframe tạo yêu cầu và màn hình tra cứu timeline: trạng thái đơn, phương án, tiền đã trả/đang hoàn/đã xác nhận, điểm/mã đang cập nhật và đích nhận che bớt. Giao diện nhân viên theo từng đơn, không có KPI/dashboard. Thông báo trong ứng dụng sau commit, chống phát trùng; không thực hiện gửi email/SMS hay nhắn ra ngoài trong giai đoạn thiết kế.

Có trạng thái đang gửi, chờ duyệt, cần bổ sung, từ chối có lý do, UNKNOWN, tiền đã xong nhưng điểm đang chờ, giao bù và hoàn tất. Nhãn trường rõ, bàn phím/focus, vùng bấm phù hợp, lỗi cạnh trường và tổng hợp lỗi; không mất dữ liệu khi thất bại. Không có nút “Hoàn lại lần nữa” khi giao dịch chưa rõ kết quả, không báo thành công chỉ vì lệnh đã gửi.

## Đầu ra theo thứ tự

1. Nhu cầu, vai trò, phạm vi và hiện trạng đã kiểm tra; tách yêu cầu/đề xuất.
2. Ma trận quyền và trạng thái; tối thiểu bốn quy tắc cụ thể, bao gồm ngoại lệ quan trọng.
3. Luồng 5–8 bước và hai sơ đồ trạng thái yêu cầu/hoàn.
4. Cách hoàn toàn phần/một phần, ngân sách theo receipt, phân bổ tiền/điểm và ví dụ số học trên.
5. Quy tắc voucher/điểm/freeship, nguồn tích lũy và hợp đồng kho/giao bù; xử lý tiền dư/muộn riêng.
6. ERD, trường/ràng buộc, dữ liệu cũ, API/JSON và transaction/khóa/idempotency.
7. Wireframe và thông báo, trạng thái lỗi và quyền tệp/chứng từ.
8. Bảng nghiệm thu tối thiểu cho hủy tranh bếp, hoàn lặp, hai request cùng suất, UNKNOWN, lỗi trả điểm sau chi tiền, chuyển trùng/muộn, mã đổi điểm, mã tháng 2/3/10, 0đ, điểm hết hạn, nợ điểm, khách vãng lai và đơn cũ.
9. Kế hoạch triển khai riêng phần 2 theo từng bước và tệp dự kiến sửa, chưa thực hiện mã nguồn; phiếu hoàn thành tương đương đề Word.
10. Danh sách ngắn chính sách còn cần góp ý; **dừng sau phần 2**, kết thúc bằng: **“Bạn muốn bổ sung hoặc điều chỉnh gì ở phần Hủy đơn/đổi trả/hoàn tiền? Có yêu cầu nào còn thiếu không? Mình sẽ dừng ở đây trước khi chuyển sang phần 3.”**
