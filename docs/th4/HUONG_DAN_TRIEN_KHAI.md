# Triển khai các chức năng TH4

Đã triển khai trực tiếp vào Django: khuyến mãi/voucher; hủy đơn, xử lý món lỗi, hoàn tiền và giao bù; giữ nguyên liệu/giao nhận; tài khoản, sổ địa chỉ và khách hàng thân thiết. Phạm vi giữ nguyên các điều chỉnh của người dùng: không thêm Dashboard và không hiển thị thông tin sinh viên. Giao diện trợ lý đã được bổ sung theo yêu cầu ngày 26/10/2026; hiện dùng gợi ý từ thực đơn, chưa kết nối mô hình AI. Xem `06_TICH_HOP_GIAO_DIEN_TU_ZIP.md` để đối chiếu bản giao diện mới.

## Chạy và sử dụng

```powershell
python manage.py migrate --noinput
python manage.py runserver
```

Các migration `0015`–`0019` đã áp dụng thành công vào database dự án trong lượt triển khai này. Không chạy lại lệnh tạo hoặc reset dữ liệu demo trên database đang có lịch sử giao dịch. Migration chỉ bổ sung bảng/trường/cấu hình; không xuất lại kho cho đơn cũ đã thanh toán.

| Đường dẫn | Vai trò | Chức năng |
|---|---|---|
| `/thuc-don/` | Khách hàng/khách tại quán | Giỏ món, báo giá máy chủ, chọn ví voucher/nhập mã, đổi điểm, chọn địa chỉ |
| `/tai-khoan/` | Đã đăng nhập | Hồ sơ, ảnh, mật khẩu, địa chỉ; khách hàng có điểm, hạng, đổi voucher, điểm danh, referral và lịch sử đơn |
| `/dang-nhap/?switch=1` | Chủ trình duyệt | Thêm tài khoản hoặc chuyển sang phiên đã xác thực còn hạn |
| `/don/<id>/ho-tro/` | Chủ đơn/phiên khách thật, nhân viên | Hủy đơn, yêu cầu món lỗi, theo dõi hoàn tiền hoặc giao bù |
| `/thu-ngan/ho-tro/` | Thu ngân/quản lý | Tiếp nhận yêu cầu và cập nhật lượt giao, giao thất bại/giao lại/kết quả giao |
| `/quan-ly/khuyen-mai/` | Quản lý | Mã khuyến mãi, quà đổi điểm và cấu hình hạng |
| `/quan-ly/ton-kho/` | Quản lý | Tồn sổ/đang giữ/khả dụng, hoàn nguyên liệu chưa dùng, hao hụt, xử lý chênh lệch kiểm kê |

Các màn hình bàn, bếp, thu ngân sẵn có tiếp tục dùng chung nghiệp vụ và số tiền theo đơn. Đơn giao bù có giá thanh toán bằng 0, dùng kho riêng và không tích điểm lần hai.

## Cấu hình thực tế cần điền

Sao chép giá trị phù hợp từ `.env.example` sang môi trường triển khai. Không có số tài khoản/hotline hay quà sinh nhật giả được sử dụng thay thông tin thật.

| Biến | Mặc định / ý nghĩa |
|---|---|
| `VIETQR_BANK_ID`, `VIETQR_ACCOUNT_NO`, `VIETQR_ACCOUNT_NAME` | Ngân hàng nhận tiền thực tế. Thiếu ngân hàng/số tài khoản thì không tạo QR |
| `PAYMENT_WEBHOOK_SECRET` | Bí mật HMAC của nguồn callback tin cậy |
| `RESTAURANT_LAT`, `RESTAURANT_LNG`, `DELIVERY_MAX_KM` | Vị trí quán và phạm vi giao |
| `DELIVERY_BASE_FEE`, `DELIVERY_FEE_PER_KM` | Phí nền và phí mỗi km làm tròn lên |
| `CHECKOUT_HOLD_MINUTES` | 15 phút giữ kho, voucher và điểm |
| `SAVED_ACCOUNT_DAYS` | 7 ngày từ lần xác thực mật khẩu, không gia hạn chỉ vì chuyển tài khoản |
| `CHECKIN_BASE_POINTS`, `REVIEW_POINTS`, `REFERRAL_POINTS` | 1 điểm/ngày; 5 điểm/đánh giá đủ điều kiện bất kể số sao; 50 điểm/người giới thiệu và người mới |
| `ISSUE_REPORT_HOURS`, `TIER_VOUCHER_DAYS` | 2 giờ tiếp nhận sự cố tự động; 90 ngày cho gói voucher lên hạng |
| `VIP_HOTLINE` | Chỉ hiển thị từ Vàng khi đã điền số thật |
| `BIRTHDAY_STANDARD_VOUCHER`, `BIRTHDAY_SPECIAL_VOUCHER` | Mã mẫu voucher sinh nhật đã tạo. Để trống sẽ chưa phát quà tương ứng |

Giá trị đề xuất trong bản thiết kế được dùng làm mặc định. Đổi hạng, điều kiện, phí hoặc mẫu voucher chỉ áp dụng cho giao dịch/báo giá sau; đơn và quyền lợi đã phát giữ bản chụp.

Quyền lợi tháng: Bạc 2 mã; Vàng miễn giao khoảng cách ≤5km và 3 mã >5km; Kim Cương miễn giao ≤5km và 10 mã >5km. Đúng 5km được xếp vào vùng gần theo mặc định thiết kế. Dùng khoảng cách gốc để phân loại, không dùng số hiển thị đã làm tròn. Nâng nhiều hạng trong tháng chỉ phát bù đến tổng quyền lợi hạng mới, tính cả mã đã sử dụng.

## Callback thanh toán và đối soát

`POST /thanh-toan/vietqr/webhook/`, JSON UTF-8; header `X-Payment-Signature` là HMAC-SHA256 dạng hex của **đúng byte request body** với secret đã cấu hình.

```json
{
  "order_code": "PHO-...",
  "amount": 44000,
  "status": "paid",
  "transaction_id": "MA_GIAO_DICH_THAT_TU_NGAN_HANG"
}
```

`transaction_id` phải do nguồn ngân hàng xác thực cung cấp. Gửi lại cùng mã là callback lặp; một mã giao dịch khác chuyển cho cùng đơn là một khoản thu khác, phải lưu để đối soát. Callback thiếu mã giao dịch bị từ chối, không lấy mã đơn để giả làm mã giao dịch ngân hàng.

HTTP 200: đã phân bổ hoặc callback của khoản đã phân bổ. HTTP 202: đã giữ chứng từ nhận tiền nhưng cần đối soát (tiền đến muộn, sai số tiền, đơn đã thanh toán, kho đang có sự cố). Không mở lại đơn đã hết hạn và không xuất kho lần hai. Thông báo thất bại thanh toán không tự chứng minh rằng sẽ không có tiền đến sau.

Hiện dùng **đối soát hoàn tiền thủ công**. Quản lý thực hiện lệnh chi tại ngân hàng, ghi mã lệnh tại màn hình hỗ trợ rồi xác nhận kết quả bằng chứng từ. `UNKNOWN` giữ ngân sách và chặn gửi lại; chỉ khi xác minh thất bại cuối mới cho lệnh thử khác. Tiền mặt có phiếu thu và phiếu chi nội bộ. Công cụ mô phỏng chỉ hoạt động khi `DEBUG=True`; chứng từ ghi rõ `SIMULATED`.

Đối với đơn cũ chỉ có cờ PAID mà chưa có phiếu thu, quản lý cần nhập chứng từ thực tế trước khi duyệt hoàn. Không tạo giả mã giao dịch từ dữ liệu cũ.

## Tác vụ định kỳ

```powershell
python manage.py process_commerce --limit 1000
```

Đặt lệnh này chạy mỗi phút bằng bộ lập lịch của môi trường triển khai. Lệnh hết hạn đơn/điểm, phát quyền lợi đến kỳ và xử lý lại sự kiện đang chờ. Sự kiện hoàn tất/hoàn tiền cũng được xử lý sau khi giao dịch gốc commit; bản ghi sự kiện còn lại để thử lại khi lỗi. Nút xử lý ở màn hình hỗ trợ dùng cho vận hành thủ công. Không tạo tác vụ trên máy người dùng trong lượt code này.

## Các bảo đảm và giới hạn vận hành

- Báo giá từ máy chủ, tiền VietQR/phiếu thu và phân bổ hoàn tiền dùng cùng số thực trả đã lưu. Tiền hàng gốc vẫn được bảo toàn riêng. Một đơn dùng tối đa một voucher; ưu đãi giao gần theo hạng không chiếm chỗ voucher.
- Điểm được lưu theo lô FIFO, hết hạn 12 tháng; phân biệt khả dụng/đang giữ/đã tiêu/hết hạn/thu hồi. Có điểm cần bù khi thưởng nguồn bị đảo sau khi đã tiêu. Các ràng buộc DB kiểm tra bảo toàn lô điểm và `tiền mặt + 100 × điểm = giá trị phân bổ`.
- Signal chuyển PAID là đầu vào duy nhất xuất kho. Giữ kho không trừ tồn sổ, snapshot BOM có phiên bản. Công thức thay đổi không làm đổi lượng xuất của đơn đang giữ.
- Định lượng hiện theo công thức tiêu chuẩn của món/topping. Các tùy chọn khẩu vị miễn phí không tự suy ra lượng nguyên liệu khác từ tên như “nhiều bánh”; cần cấu hình công thức biến thể riêng nếu cửa hàng muốn theo dõi chênh lệch này. Đây là quy tắc tiêu chuẩn mặc định được phép trong thiết kế, không phải công thức đã được xác nhận từ cửa hàng.
- Món phở/topping/đồ uống mới mặc định cần BOM. Nếu thực sự không theo dõi kho, quản lý chọn rõ `UNTRACKED` khi sửa món/topping. Các đồ uống/topping cũ vốn không có BOM được migration ghi nhận `UNTRACKED` để bảo toàn hành vi cũ; nên rà soát sau nâng cấp.
- Đơn cũ đã PAID không bị tính xuất kho lại. Đơn cũ đang chờ thanh toán được kiểm tra lại tồn hiện tại khi xác nhận. Chưa có chứng cứ định lượng lịch sử thì không giả tạo liên kết xuất kho quá khứ.
- Đơn vị nguyên liệu đã có công thức/lịch sử không được chỉ đổi nhãn. Hệ thống giữ đơn vị gốc cho các bản ghi đã dùng; chuyển đổi đơn vị lịch sử cần một đợt chuyển dữ liệu có kiểm toán riêng.
- Nhập kho hỗ trợ bảng quy đổi g/gram ↔ kg và ml ↔ l/lít, lưu cả lượng nhập và lượng tồn chuẩn vào nhật ký. Không đổi thể tích sang khối lượng; từ chối quy đổi gây mất độ chính xác thay vì tăng khống lượng nhập.
- Giao hàng yêu cầu tên/điện thoại/địa chỉ và tọa độ hợp lệ. Tọa độ do khách chọn, chưa có nhà cung cấp geocoding hoặc GPS người giao. Chỉ xác nhận giao thực tế mới phát sự kiện hoàn tất/tích điểm.
- Khoản hoàn tiền đã xác nhận và việc cập nhật điểm/voucher tách bằng sự kiện; thử lại quyền lợi không chi tiền lần hai. Phần món đã giữ cho hoàn tiền không đồng thời giao bù.
- Chuyển tài khoản dùng vault và slot phía máy chủ. Không lưu mật khẩu/token trong localStorage. Các tab chia sẻ tài khoản đang hoạt động; kiểm tra generation chặn tab cũ gửi nhầm dữ liệu. Đăng nhập/switch không mang quyền xem đơn khách vãng lai sang tài khoản khác.
- Bản triển khai cho một quán dùng một khóa giao dịch PostgreSQL chung trước các khóa dòng để thống nhất đường ghi cũ/mới. Điều này ưu tiên tính nhất quán nhưng giới hạn thông lượng. Khi mở nhiều quán cần chia khóa theo quán và đo tải trước khi mở rộng; không gọi ngân hàng hay dịch vụ mạng trong khóa.

## Kiểm tra lại

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test pho_app --noinput --keepdb
```

Bộ kiểm thử có các luồng tiền/kho, phân bổ hoàn một phần, callback lặp và khoản thu dư, hết hạn giữ, nợ điểm, giới thiệu, lên/hạ hạng, phiên tài khoản, quyền sở hữu và cạnh tranh giữ nguyên liệu trên PostgreSQL. Giao diện được kiểm tra bằng Chromium ở desktop 1440px và mobile 390px với database QA riêng. Ca trình duyệt đã kiểm tra: món 55.000đ − voucher 10.000đ − 10 điểm = 44.000đ; tạo đơn và hủy trước thanh toán, trả lại quyền lợi; không có lỗi JavaScript trong luồng này.

Kết quả kiểm thử đầy đủ sau tích hợp giao diện ZIP ngày 26/10/2026: **168 tests passed**; Django system check không có lỗi, không phát sinh migration. Các ảnh kiểm tra được lưu trong `scratch/th4-*.png` và `scratch/ui-final-*.png`, không đưa vào dữ liệu ứng dụng.

## Giao diện đồng bộ với dự án

Các màn hình mới dùng chung `figma-ui.css`: màu thương hiệu, font Be Vietnam Pro, khung quản lý, thanh điều hướng, nút, thẻ và biểu mẫu. `commerce.css` bổ sung bố cục cho các chức năng TH4; `commerce.js` xử lý tab, bộ lọc, hộp thoại và trạng thái gửi biểu mẫu.

- Tài khoản chia thành Hồ sơ, Sổ địa chỉ, Thành viên & điểm và Đơn của tôi. Khu thành viên có tổng quan, ví voucher, đổi điểm và lịch sử; thẻ voucher hiển thị loại, mức giảm, điều kiện và hạn dùng.
- Khuyến mãi chia mã chiến dịch, quà đổi điểm và hạng. Có tìm kiếm, lọc trạng thái; mở biểu mẫu khi tạo/sửa, tự mở lại biểu mẫu có lỗi và giữ nội dung đã nhập.
- Hỗ trợ có chọn phần món và dự tính giá trị gửi xét duyệt; tiến độ nằm cùng màn hình. Quản lý mở từng yêu cầu để duyệt hoặc đối soát khoản hoàn. Giao nhận và đối soát thu có tab riêng.
- Kho hiển thị tồn thực tế, đang giữ và khả dụng trong cùng bảng. Nhập kho, thêm định lượng, hoàn kho/hao hụt dùng hộp thoại; chọn mã đơn có phiếu xuất thay cho nhập ID thủ công. Lịch sử và sự cố kho có tab riêng.
- Giỏ hàng có vùng nội dung cuộn độc lập, tổng tiền và nút đặt món luôn ở cuối màn hình. Chọn sẵn địa chỉ mặc định; chuyển sang địa chỉ nhập tay sẽ xóa tọa độ cũ. Chỉ hiển thị các khoản giảm thực sự được áp dụng.
- Tab hỗ trợ bàn phím và giữ phần đang mở sau khi gửi biểu mẫu. Các biểu mẫu ưu đãi có ID riêng để nhãn và thông báo lỗi trỏ đúng trường. Ảnh đại diện có xem trước và khôi phục khi bỏ chọn tệp.

Đã kiểm tra 60 tổ hợp trang/kích thước 320, 390, 768 và 1440px bằng Chrome, không tràn ngang toàn trang, không trùng ID và không có lỗi JavaScript/HTTP 500 trong các ca này. Bảng rộng và danh sách tab cuộn trong vùng riêng. Các luồng trình duyệt đã kiểm tra thêm: đổi điểm, thêm địa chỉ, voucher + điểm cho đơn 44.000đ, hủy đơn, lỗi ngày khuyến mãi và sửa lại, tìm kiếm, duyệt hỗ trợ, bàn giao người giao và chọn loại định lượng. Dữ liệu kiểm tra nằm trong database QA tách riêng.
