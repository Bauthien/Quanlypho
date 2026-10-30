from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from pho_app.models import MenuItem, Order, OrderItem, Review, User


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CustomerReviewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(username='reviewer', role=User.Role.CUSTOMER)
        cls.admin = User.objects.create_user(username='admin_reviewer', role=User.Role.ADMIN)
        cls.dish = MenuItem.objects.create(name='Phở Tái Bò', base_price=55000, is_active=True)
        cls.other_dish = MenuItem.objects.create(name='Phở Gà Ta', base_price=50000, is_active=True)
        cls.order = Order.objects.create(
            customer=cls.customer,
            order_code='PHO-REV-01',
            order_status='COMPLETED',
            purpose='REGULAR',
            total_amount=55000,
        )
        OrderItem.objects.create(order=cls.order, menu_item=cls.dish, quantity=1, item_price=55000)

    def setUp(self):
        self.client.force_login(self.customer)

    def test_customer_can_review_dish_without_order(self):
        """Khách hàng có thể đánh giá món ăn trực tiếp không cần đơn hàng."""
        response = self.client.post(reverse('submit_review'), {
            'menu_item_id': str(self.dish.pk),
            'order_id': '',
            'rating': '5',
            'comment': 'Nước dùng rất thanh ngọt, thịt mềm thơm!',
        }, follow=True)
        self.assertRedirects(response, reverse('reviews_list'))
        self.assertContains(response, 'Cảm ơn bạn đã gửi đánh giá!')

        # Verify DB
        review = Review.objects.get(customer=self.customer, menu_item=self.dish)
        self.assertIsNone(review.order)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Nước dùng rất thanh ngọt, thịt mềm thơm!')
        self.assertTrue(review.is_published)

    def test_customer_can_update_existing_dish_review(self):
        """Đánh giá lại món sẽ cập nhật bản ghi cũ và tăng revision."""
        Review.objects.create(customer=self.customer, menu_item=self.dish, order=None, rating=4, comment='Khá ngon')
        response = self.client.post(reverse('submit_review'), {
            'menu_item_id': str(self.dish.pk),
            'order_id': '',
            'rating': '5',
            'comment': 'Lần này ngon xuất sắc!',
        }, follow=True)
        self.assertRedirects(response, reverse('reviews_list'))
        self.assertContains(response, 'Đã cập nhật đánh giá của bạn thành công!')

        review = Review.objects.get(customer=self.customer, menu_item=self.dish)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Lần này ngon xuất sắc!')
        self.assertEqual(review.revision, 2)

    def test_cannot_submit_without_item_and_order(self):
        """Không được gửi đánh giá rỗng (không chọn món và không chọn đơn)."""
        response = self.client.post(reverse('submit_review'), {
            'menu_item_id': '',
            'order_id': '',
            'rating': '5',
            'comment': 'Không có mục tiêu đánh giá',
        }, follow=True)
        self.assertRedirects(response, reverse('review_form'))
        self.assertContains(response, 'Vui lòng chọn món ăn hoặc đơn hàng')
        self.assertEqual(Review.objects.count(), 0)

    def test_dish_not_in_order_falls_back_to_standalone_dish_review(self):
        """Nếu chọn món không có trong đơn, tự động ghi nhận đánh giá món độc lập không lỗi."""
        response = self.client.post(reverse('submit_review'), {
            'menu_item_id': str(self.other_dish.pk),  # other_dish không có trong order
            'order_id': str(self.order.pk),
            'rating': '4',
            'comment': 'Phở gà ngon',
        }, follow=True)
        self.assertRedirects(response, reverse('reviews_list'))
        self.assertContains(response, 'độc lập')

        review = Review.objects.get(customer=self.customer, menu_item=self.other_dish)
        self.assertIsNone(review.order)

    def test_reviews_list_hides_unpublished_reviews(self):
        """Đánh giá bị ẩn (is_published=False) không hiển thị cho khách hàng."""
        Review.objects.create(customer=self.customer, menu_item=self.dish, rating=1, comment='Nội dung nhạy cảm', is_published=False)
        Review.objects.create(customer=self.customer, menu_item=self.other_dish, rating=5, comment='Nội dung chuẩn', is_published=True)

        response = self.client.get(reverse('reviews_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Nội dung nhạy cảm')
        self.assertContains(response, 'Nội dung chuẩn')

    def test_admin_can_toggle_review_visibility(self):
        """Quản lý có thể bật/tắt hiển thị đánh giá."""
        review = Review.objects.create(customer=self.customer, menu_item=self.dish, rating=1, comment='Cần kiểm duyệt', is_published=True)

        self.client.force_login(self.admin)
        toggle_url = reverse('admin_review_toggle_publish', args=[review.pk])
        response = self.client.post(toggle_url, follow=True)
        self.assertRedirects(response, reverse('review_list_all'))
        self.assertContains(response, 'Đã ẩn đánh giá')

        review.refresh_from_db()
        self.assertFalse(review.is_published)

        # Bật lại
        response = self.client.post(toggle_url, follow=True)
        review.refresh_from_db()
        self.assertTrue(review.is_published)

    def test_standalone_good_dish_review_counts_toward_tier_progress(self):
        """Đánh giá món độc lập từ 4 sao và dài >= 20 ký tự được tính vào good_review_count."""
        from pho_app.loyalty import account_for
        account = account_for(self.customer)
        self.assertEqual(account.good_review_count, 0)

        # Gửi đánh giá món độc lập có độ dài >= 20 ký tự
        self.client.post(reverse('submit_review'), {
            'menu_item_id': str(self.dish.pk),
            'order_id': '',
            'rating': '5',
            'comment': 'Nước dùng rất thanh ngọt, thịt bò mềm thơm tuyệt hảo!',
        })
        account.refresh_from_db()
        self.assertEqual(account.good_review_count, 1)

    def test_customer_can_delete_own_review(self):
        """Khách hàng có thể tự xóa đánh giá của mình trong tài khoản."""
        review = Review.objects.create(customer=self.customer, menu_item=self.dish, rating=5, comment='Rất hài lòng về chất lượng món')
        from pho_app.loyalty import account_for
        account = account_for(self.customer)
        account.good_review_count = 1
        account.save()

        response = self.client.post(reverse('customer_review_delete', args=[review.pk]), follow=True)
        self.assertRedirects(response, f"{reverse('account')}?tab=reviews")
        self.assertContains(response, 'Đã xóa đánh giá của bạn thành công')
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

        account.refresh_from_db()
        self.assertEqual(account.good_review_count, 0)

    def test_admin_can_delete_review(self):
        """Quản lý có thể xóa đánh giá bất kỳ từ trang admin reviews."""
        review = Review.objects.create(customer=self.customer, menu_item=self.dish, rating=1, comment='Đánh giá thử nghiệm')
        self.client.force_login(self.admin)

        response = self.client.post(reverse('admin_review_delete', args=[review.pk]), follow=True)
        self.assertRedirects(response, reverse('review_list_all'))
        self.assertContains(response, 'Đã xóa vĩnh viễn đánh giá')
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_account_page_renders_my_reviews_tab(self):
        """Trang tài khoản khách hàng hiển thị tab và danh sách 'Đánh giá của tôi'."""
        Review.objects.create(customer=self.customer, menu_item=self.dish, rating=5, comment='Tô phở đậm đà đúng điệu')
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Đánh giá của tôi')
        self.assertContains(response, 'Tô phở đậm đà đúng điệu')
        self.assertContains(response, 'Phở Tái Bò')

    def test_review_with_image_upload(self):
        """Khách hàng có thể đính kèm ảnh chụp món ăn khi gửi đánh giá."""
        tiny_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04'
            b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
            b'\x01\x00\x3b'
        )
        image = SimpleUploadedFile('pho_bowl.gif', tiny_gif, content_type='image/gif')
        response = self.client.post(reverse('submit_review'), {
            'menu_item_id': str(self.dish.pk),
            'order_id': '',
            'rating': '5',
            'comment': 'Ảnh chụp thực tế bát phở rất hấp dẫn!',
            'image': image,
        }, follow=True)
        self.assertRedirects(response, reverse('reviews_list'))
        review = Review.objects.get(customer=self.customer, menu_item=self.dish)
        self.assertTrue(bool(review.image))
        self.assertIn('pho_bowl', review.image.name)

        response = self.client.get(reverse('reviews_list'))
        self.assertContains(response, review.image.url)

    def test_admin_can_reply_to_review(self):
        """Quản lý có thể phản hồi đánh giá và khách hàng nhìn thấy phản hồi của quán."""
        review = Review.objects.create(
            customer=self.customer,
            menu_item=self.dish,
            rating=5,
            comment='Phở ngon xuất sắc, phục vụ chu đáo!',
            is_published=True
        )
        self.client.force_login(self.admin)
        reply_url = reverse('admin_review_reply', args=[review.pk])
        response = self.client.post(reply_url, {
            'store_reply': 'Phở Nhà chân thành cảm ơn quý khách. Hẹn gặp lại bạn!',
        }, follow=True)
        self.assertRedirects(response, reverse('review_list_all'))
        self.assertContains(response, 'Đã gửi phản hồi đến đánh giá')

        review.refresh_from_db()
        self.assertEqual(review.store_reply, 'Phở Nhà chân thành cảm ơn quý khách. Hẹn gặp lại bạn!')
        self.assertEqual(review.replied_by, self.admin)
        self.assertIsNotNone(review.replied_at)

        self.client.force_login(self.customer)
        cust_resp = self.client.get(reverse('reviews_list'))
        self.assertContains(cust_resp, 'Phản hồi từ Phở Nhà')
        self.assertContains(cust_resp, 'Phở Nhà chân thành cảm ơn quý khách')

    def test_menu_view_includes_ratings_in_payload(self):
        """Thực đơn trả về điểm đánh giá trung bình và số lượng đánh giá cho từng món."""
        cust2 = User.objects.create_user(username='reviewer2', role=User.Role.CUSTOMER)
        Review.objects.create(customer=self.customer, menu_item=self.dish, rating=5, comment='Ngon 1', is_published=True)
        Review.objects.create(customer=cust2, menu_item=self.dish, rating=4, comment='Ngon 2', is_published=True)
        cust3 = User.objects.create_user(username='reviewer3', role=User.Role.CUSTOMER)
        Review.objects.create(customer=cust3, menu_item=self.dish, rating=1, comment='Ẩn', is_published=False)

        response = self.client.get(reverse('menu'))
        self.assertEqual(response.status_code, 200)
        menu_payload = response.context['menu_payload']
        dish_data = next((item for item in menu_payload if item['id'] == self.dish.pk), None)
        self.assertIsNotNone(dish_data)
        self.assertEqual(dish_data['review_count'], 2)
        self.assertEqual(dish_data['avg_rating'], 4.5)
