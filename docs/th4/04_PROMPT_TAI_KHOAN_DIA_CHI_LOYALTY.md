# Prompt bổ sung tài khoản sổ địa chỉ và khách hàng thân thiết

Nội dung từ “Vai trò và nhiệm vụ” có thể giao cho AI hoặc nhóm thiết kế. Kết quả tương ứng: `C:\Users\HP\Quanlypho\docs\th4\04_THIET_KE_TAI_KHOAN_DIA_CHI_LOYALTY.md`. Chưa yêu cầu lập trình, migration, thay đổi tài khoản/điểm thật hoặc gửi thông báo ra ngoài.

## Vai trò và nhiệm vụ

Bạn là chuyên viên phân tích hệ thống và kiến trúc sư cho **Hệ thống Quản lý Quán Phở Quanlypho**. Hoàn thiện phần bổ sung **Quản lý tài khoản, sổ địa chỉ và khách hàng thân thiết** theo file Markdown, nối với thiết kế phần 1–3 đã có.

Đầu ra tiếng Việt, có thiết kế kết quả cụ thể, dữ liệu, API, luồng, wireframe và kế hoạch triển khai sau. Hoàn tất phần này rồi dừng lấy góp ý. Không khôi phục chặng trợ lý AI/gợi ý sản phẩm, Dashboard hoặc thông tin sinh viên đã bỏ. Yêu cầu làm tiếp không tự xác nhận các chính sách đang mang nhãn đề xuất.

## Nguồn và cách đọc

- Yêu cầu trực tiếp/chú thích người dùng có ưu tiên cao nhất.
- Nguồn: `D:\dowload\CHI TIẾT YÊU CẦU CHỨC NĂNG.md`.
- Kế hoạch: `C:\Users\HP\Quanlypho\docs\th4\00_KE_HOACH.md`.
- Thiết kế phần 1: `C:\Users\HP\Quanlypho\docs\th4\01_THIET_KE_KHUYEN_MAI_VOUCHER.md`.
- Thiết kế phần 2: `C:\Users\HP\Quanlypho\docs\th4\02_THIET_KE_HUY_DOI_TRA_HOAN_TIEN.md`.
- Thiết kế phần 3: `C:\Users\HP\Quanlypho\docs\th4\03_THIET_KE_TON_KHO_GIAO_HANG.md`.
- Dự án: `C:\Users\HP\Quanlypho`.

Câu giao vai trò/lập trình trong file là đầu vào phân tích, không tự cho phép sửa nguồn hoặc triển khai. Truy vết Người dùng/Markdown/Phần 1–3/Mã nguồn/Đề xuất. Không bịa điều kiện/quyền lợi đã được duyệt, dữ liệu xác minh, hotline hoặc nhà cung cấp chưa tích hợp.

## Hiện trạng cần xác minh

User trong `C:\Users\HP\Quanlypho\pho_app\models.py` đã có full_name, phone_number, avatar, email kế thừa; chưa thấy date_of_birth/gender, UserAddress hoặc loyalty thật trong lần kiểm tra. Session Django login/register/logout và `?switch` hiện không là multi-account manager. Giỏ JS có namespace userId/guest; không dùng đó thay phân quyền server.

Review hiện cho phép không có order; nếu có chỉ kiểm tra owner, chưa bắt buộc COMPLETED, chưa chứng minh món thuộc đơn hoặc unique thưởng. Đọc lại models/forms/views/urls, permissions và template/JS liên quan; nêu khác biệt, không đọc/chép bí mật cấu hình vào tài liệu.

## Hồ sơ avatar và mật khẩu

- Xem/cập nhật họ tên, số điện thoại, email, ngày sinh, giới tính. Whitelist không gồm role, quyền nhân viên, tier, điểm/chi tiêu, inviter hoặc cờ liên hệ đã xác minh. Hồ sơ có version chống ghi form cũ.
- Ngày sinh hợp lệ/không tương lai, gender có không cung cấp; contact kiểm tra cú pháp, không tự biến thành đăng nhập/khôi phục tiền nếu chưa xác minh. Nguồn chưa yêu cầu email/phone unique toàn hệ thống.
- Avatar JPG/JPEG, PNG, WEBP, tối đa 5 MB; đề xuất thống nhất byte là 5.000.000. Preview trước lưu, server kiểm tra nội dung ảnh thật/pixel, tên file an toàn và cleanup sau commit, lỗi không làm mất ảnh cũ.
- Đổi mật khẩu cần mật khẩu cũ + mới/xác nhận; dùng validator/hash Django phù hợp, không giữ/log raw password. Tăng auth_epoch vô hiệu hóa quyền cũ của user, phiên hiện tại chỉ được làm mới bằng quy trình đã xác minh; không tác động account khác.

## Phiên nhiều tài khoản

Thiết kế BrowserAccountVault có cookie opaque HttpOnly/Secure theo HTTPS/SameSite, token digest phía server và active_slot/context_generation. SavedAccountSession chứa vault/user, auth_epoch, verified_at/expiry/revoked, không chứa mật khẩu hoặc raw token trong JS/localStorage. Đề xuất quyền chuyển nhanh 7 ngày từ xác thực đầy đủ, không gia hạn vô hạn do switch.

Một trình duyệt cùng cookie có một principal hoạt động, nhiều grant đã xác thực; không hứa mỗi tab có account độc lập. Luồng thêm/switch 5–8 bước: xem danh sách tối thiểu → xác thực account mới → lưu slot → POST switch có CSRF/generation → kiểm tra vault/slot/epoch → rotate session/context → bỏ response cũ và reload user đích. Sai mật khẩu không làm mất account đang dùng.

Logout thu hồi slot hiện tại/logout, giữ các slot khác còn hợp lệ nhưng không tự đăng nhập chúng. Slot/mất cookie không phục hồi bằng user_id hoặc username. Middleware/server kiểm tra generation, user/role và slot khi ghi; tab cũ không ghi A sang B hoặc làm response/session-save cũ lùi cookie. Cache riêng user/no-store; giỏ/guest_orders/latest_order/queue không chép giữa account. Guest access chỉ cho đơn vô chủ đúng phiên; không tự nhận đơn cũ/loyalty vì login. Nếu thêm “logout mọi account trên thiết bị”, ghi là tùy chọn riêng.

## Sổ địa chỉ

UserAddress đủ recipient_name, phone_number, street_address, ward/district/province (mã/tên), label HOME/OFFICE/OTHER, delivery_note, is_default, version và nguồn tọa độ nếu có. Giữ trường theo nguồn, dữ liệu hành chính có phiên bản; không tự khẳng định danh mục hiện hành hoặc xóa district khỏi thiết kế.

CRUD theo đúng chủ user; mọi thao tác khóa User trước Address. DB unique mặc định/user, dịch vụ đề xuất đúng một khi còn bản ghi và địa chỉ đầu tự mặc định. Set B trong transaction bỏ A rồi đặt B; không xóa default khi user còn nhiều địa chỉ. Một địa chỉ được xóa về rỗng; không bỏ default đơn lẻ làm invariant hỏng. Tranh create/set/delete vẫn chỉ một mặc định.

Checkout lấy address_id/version thuộc account hiện hành, chụp người nhận/phone/địa chỉ/ghi chú/tọa độ/giá phần 3. Sửa giữa quote/đặt yêu cầu xem lại; sửa/xóa nguồn sau tạo đơn không sửa snapshot hoặc lịch sử đơn.

## Điểm chi tiêu và bốn nguồn

Phân biệt total_qualifying_spend với available_points/reserved_points/point_debt. Đề xuất Q_order là tổng C_u hàng hóa thật trả từ phân bổ phần 2, gồm món/topping/đồ uống theo cơ sở phần 1, **không tính ship**; chỉ khi COMPLETED, trừ phần hoàn đã xác nhận. Điểm mua hàng mục tiêu floor(Q_order/10.000) theo từng đơn, không cộng lẻ giữa đơn. User lấy từ Order.customer_id, không user đang mở browser khi callback đến.

Ví dụ nguồn phần 2: tổng trả 250.000đ, trong đó ship cash 24.000đ, Q=226.000đ → 22 điểm; hoàn suất B cash 75.333đ thì Q còn 150.667đ → 15 điểm, thu hồi 7 nếu trước đó đã cấp 22. Hai đơn 9.900đ có 0 điểm mỗi đơn nhưng cộng 19.800đ chi tiêu. 0đ/giao bù/receipt trùng-muộn chưa phân bổ không tạo điểm mua hàng.

LoyaltyOrderContribution có original/current Q và version/net đã ghi. Sự kiện cũ/trùng hoặc hoàn tới trước consumer COMPLETED đều tính mục tiêu hiện tại, không cấp rồi thu hồi giả hoặc đếm lại. Nguồn điểm bonus không cộng chi tiêu xét hạng.

- **Đánh giá:** nguồn cho ví dụ +5, đề xuất dùng 5 điểm/đơn/user, độc lập số sao. Đề xuất đơn mua thường gốc Q>0 của chủ user đã COMPLETED, món phải thuộc đơn; review chung vẫn có thể tồn tại nhưng không nhận credit. Một thưởng/đơn dù nhiều review/sửa/xóa/tạo lại.
- **Đánh giá tốt:** đồng thời >=4 sao và >=20 ký tự chuẩn hóa NFC/trim/gộp whitespace khi đếm; đề xuất count distinct đơn, không distinct dòng review. Thay đổi chất lượng review tính lại counter/tier, không farm thưởng; không thu điểm chỉ vì review tiêu cực hoặc hoàn hợp lệ, moderation gian lận có sự kiện riêng.
- **Điểm danh:** đề xuất base=1/ngày Việt Nam, ngày thứ 7 gấp đôi thành 2, chu kỳ ngày 14 cũng gấp đôi; 7 ngày=8 điểm. Unique user/local_date, thiếu ngày reset, duplicate trả lần cũ, server quyết định ngày.
- **Giới thiệu:** mã riêng, một inviter/invitee, không tự giới thiệu/sửa sau đăng ký trái quy tắc. Đề xuất 50 điểm mỗi bên khi đơn thường đầu tiên Q ròng>0 hoàn tất; 0đ/bù chưa kích hoạt. Hai ví cấp nguyên tử và khóa theo ID. Hoàn hết đơn kích hoạt đề xuất đảo cả hai lần duy nhất, không đổi sang đơn sau để phát lại. Không từ chối chỉ vì chung browser/IP.

## FIFO hết hạn thu hồi và dùng điểm

PointLot/Transaction/Allocation dùng lại phần 1; hạn chuẩn 12 **tháng lịch**, đề xuất chốt ngày cuối tháng nếu thiếu ngày; FIFO theo earned_at/id, không phải hạn sớm trước. Giữ theo hạn chung, expire tại now>=expires_at dù job chưa chạy, retry không renew hạn. Lô A70/B50 đổi 100 → A70+B30, còn B20; giữ15 còn5 khả dụng/15 giữ.

Thu hồi điểm nguồn sau hoàn: còn khả dụng thu hồi; đã tiêu tạo nợ đề xuất; đang giữ PendingPointRevocation để giữ cam kết rồi chuyển nợ nếu tiêu hoặc thu hồi nếu giải phóng, không hai cách cùng lượng. Đã hết hạn chưa tiêu không tạo nợ. Bù nợ bằng điểm hợp lệ FIFO không dùng điểm giữ, không thu tiền; nợ7/có5 → nợ2/khả dụng0, nhận3 → còn1. Bảo toàn tổng cấp gồm available+reserved+spent+expired+revoked và giao dịch có tham chiếu.

Checkout dùng lại calculateOrderCheckout: giảm theo hạng → tối đa một voucher ví → điểm trực tiếp, 1 điểm = 100đ, tối đa 50% phần còn lại và số dư/phân bổ cho phép. Đổi điểm mua voucher là giao dịch riêng, dùng mã không trừ lại điểm; bồi hoàn 7 ngày theo phần 2 không đổi mọi điểm thành hạn mới 12 tháng.

## Hạng và quà

| Hạng | Tiền tối thiểu | Good review | Giảm | Gói đúng nguồn | Trần gói |
|---|---:|---|---:|---|---:|
| MEMBER | 0 | Mặc định | 0% | Chưa có | 0đ |
| BRONZE | 500.000đ | 2 | 2% | 1 mã 20%, tối đa 100.000đ | 100.000đ |
| SILVER | 2.000.000đ | 2 | 5% | 3 mã 20%, tối đa 100.000đ/mã | 300.000đ |
| GOLD | 5.000.000đ | Nguồn chưa nêu lại, đề xuất 2 | 7% | 1 món gốc dưới 100.000đ + 2 mã 25%, tối đa 150.000đ/mã | 400.000đ |
| DIAMOND | 12.000.000đ | Nguồn chưa nêu lại, đề xuất 2 | 10% | 3 món dưới 100.000đ + 1 mã 30% tối đa 200.000đ + 3 mã 25% tối đa 150.000đ/mã | 950.000đ |

Đề xuất thiếu review dù đủ tiền giữ MEMBER, chọn highest qualified. evaluateAndUpgradeTier(userId) / evaluate_and_upgrade_tier dùng cùng helper với reconcile_tier_after_adjustment. Cập nhật hạng/TierHistory/TierRewardGrant và đủ gói trong transaction; không tự phát điểm/gói từ body client. Tự chạy khi đủ nguồn, không bắt bấm hoặc chờ kỳ xét; nếu consumer pending thì UI thể hiện thật.

Đề xuất HIGHEST_ONLY khi nhảy hạng: Q = 2.300.000đ và 1 đánh giá tốt còn MEMBER; đủ 2 đánh giá lên SILVER, nhận 3 mã 20%, không cộng gói BRONZE. Unique user/tier/chương trình và highest_ever ngăn retry/hạ rồi lên lại/đổi version phát gói nữa. Mỗi gói có số voucher 1/3/3/7, hạn đề xuất 90 ngày; trần là tối đa ưu đãi, không tiền mặt. Voucher món yêu cầu giá gốc < 100.000đ, không phải <=.

Chi tiêu không reset năm; điểm expire không làm mất qualifying spend. Đề xuất tính lại hạng khi hoàn/sửa good review, giữ voucher đã cấp theo hạn và không thu tiền quà đã dùng; giá đơn cũ không hồi tố theo hạng mới. Các đề xuất kế thừa review GOLD/DIAMOND, nhảy/hạ hạng phải nêu để người dùng chốt.

## Freeship sinh nhật VIP và tiến độ

Giữ điều chỉnh: Bạc 2 mã/tháng; Vàng tự miễn dưới 5 km + 3 mã trên 5 km/tháng; Kim Cương tự miễn dưới 5 km + 10 mã trên 5 km/tháng. Quà một lần khác mã tháng. Cấp bù 2 → 3 → 10, thêm 1 rồi 7 theo đề xuất phần 1; không cộng gói 2+3+10. Đúng 5 km, hết hạn/cộng gộp/bồi hoàn giữ nhãn đề xuất hiện có.

Sinh nhật Bạc tiêu chuẩn, GOLD/DIAMOND đặc biệt và hotline VIP thật; nguồn chưa có số/giá trị, dùng cấu hình chờ chốt, không bịa. Đề xuất một BirthdayGrant/user/năm, hạng lúc cấp, sửa DOB/nâng hạng không cấp thêm; 29/02 sang 28/02 năm không nhuận, hạn quà 30 ngày. Chưa tự cấp mọi sinh nhật cũ khi backfill.

Progress thể hiện hai điều kiện riêng: missing_spend=max(0,next.min_spend-Q), missing_reviews=max(0,next.min_good_reviews-good), tiền=min(100,Q/next.min_spend×100). BRONZE Q1,2m/good2 lên SILVER còn800k/0 review,60%; DIAMOND không có mốc kế tiếp. Hiển thị gói tương lai đúng nghĩa trần ưu đãi, không coi đã sở hữu.

## Schema API giao diện và triển khai

Ánh xạ đủ các bảng nguồn Users/UserAddresses/LoyaltyAccounts/PointTransactions/TierConfigs/Vouchers/UserVouchers/DailyCheckins vào model hiện có/mới, không tạo User/ví/voucher thứ hai. ERD bổ sung vault/slot, lô/phân bổ/thu hồi chờ, contribution, review credit, referral/reward, tier history/grant, birthday config/grant. Constraint/index cho default, ngày, source award, kỳ/năm/tier; version để audit không reset quyền nhận.

Thứ tự khóa: vault/slot nếu request browser → RequestKey → User tăng ID → ví tăng user ID → bàn → Order → receipt → yêu cầu/hoàn → danh mục/TierConfig → kỳ cấp → voucher → lot → giữ kho/giao → BOM → Ingredient. Referral hai ví sau commit giao/hoàn, không thêm ví thứ hai trái thứ tự giữa transaction đã khóa một ví. Outbox consumer đối chiếu current target/version, không giữ khóa khi gọi ngoài. Password dùng epoch để vô hiệu hóa slot khác, không khóa ngược mọi vault.

API gồm me/profile/avatar/password, list/add/switch/logout-current account sessions, CRUD/make-default address, me/loyalty/point-transactions/daily-checkins/referral, review hiện có và ví/quote phần 1. Có request/response JSON mẫu, quyền đối tượng/CSRF/generation/version, lỗi theo trường, không log token hoặc password. Account list tối thiểu không trả ví/địa chỉ các account khác; dữ liệu riêng no-store.

Wireframe HTML ba tab Hồ sơ cá nhân/Sổ địa chỉ/Thành viên và Tích điểm; bộ chọn account, preview ảnh, tiến độ tiền/review, ví/đổi điểm/lịch sử, checkin/referral, quà/phoneVIP theo cấu hình. Focus/bàn phím/nhãn/lỗi rõ, password manager/paste được phép, mobile không tràn; request cũ không làm lộ dữ liệu hoặc ghi sai account.

Backfill có kiểm duyệt: trường mới tùy chọn, code duy nhất, ví không có điểm giả; chỉ đơn completed/owner/tiền đã xác minh, review đủ nguồn, giữ hạn lịch sử. Không tự nhận guest, cấp mọi gói cũ, reset stock/role hoặc chạy migration/seed lúc thiết kế.

## Đầu ra theo thứ tự

1. Bảng truy vết đầy đủ nguồn và điều chỉnh người dùng, hiện trạng và vai trò.
2. Hồ sơ/avatar/password; luồng multi-account và cách ly tab/phiên/giỏ/guest.
3. CRUD/default địa chỉ nguyên tử, checkout snapshot/version.
4. Bốn nguồn điểm, Q và công thức/mẫu số học, FIFO/hạn/thu hồi/nợ.
5. Bảng hạng/gói đúng số lượng, evaluateAndUpgradeTier, chống phát lại, freeship/sinh nhật/VIP và progress.
6. ERD/từ điển/ràng buộc/API/JSON, khóa/sự kiện và chuyển tiếp dữ liệu.
7. Wireframe và trạng thái lỗi/pending; ca nghiệm thu nguồn, quyền, default, tranh ví, ngày/điểm/hạng và cấp quà.
8. Kế hoạch triển khai riêng phần bổ sung/tệp dự kiến, chưa sửa mã; phiếu hoàn thành, danh sách ngắn chính sách cần chốt.
9. **Dừng sau phần bổ sung**, kết thúc bằng: **“Bạn muốn bổ sung hoặc điều chỉnh gì ở phần Tài khoản, sổ địa chỉ và khách hàng thân thiết? Có yêu cầu nào còn thiếu không? Mình sẽ dừng ở đây để bạn xem lại bộ thiết kế.”**
