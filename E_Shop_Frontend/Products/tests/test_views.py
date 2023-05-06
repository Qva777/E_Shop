# python manage.py test E_Shop_Frontend.Products.tests.test_views
import stripe
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from E_Shop_API.E_Shop_Cart.models import Cart, CartProduct
from E_Shop_API.E_Shop_Products.models import Product
from E_Shop_Frontend.Products.views import EmailSender, PaymentProcessor
from E_Shop_API.E_Shop_Users.models import Clients


class TestHelpers(TestCase):
    """ Test Helpers """

    @staticmethod
    def generate_stripe_token():
        """ Generate a Stripe token for testing """
        stripe.api_key = settings.STRIPE_SECRET_KEY

        token = stripe.Token.create(
            card={
                "number": "4242424242424242",  # A valid test card number
                "exp_month": 12,  # Expiration month
                "exp_year": 25,  # Expiration year
                "cvc": "123",  # CVC
            },
        )

        return token.id


class SearchViewTest(TestCase):
    """ Search View Test """

    def setUp(self):
        """ Set up for search view tests """
        self.product = Product.objects.create(
            name='Test Product',
            description='This is a test product description.',
            count=10,
            price=19.99,
            active=True,
        )

    def test_search_view_with_results(self):
        """ Test search view with results """
        response = self.client.get(reverse('search') + '?q=product')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Results for "product"')
        self.assertContains(response, 'Test Product')

    def test_search_view_no_results(self):
        """ Test search view with no results """
        response = self.client.get(reverse('search') + '?q=nonexistent')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('404'))

    def test_search_view_with_no_stock(self):
        """ Test search view with no stock """
        self.product.count = 0
        self.product.save()
        response = self.client.get(reverse('search') + '?q=Test Product')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('404'))

    def test_search_view_with_stock(self):
        """ Test search view with stock """
        response = self.client.get(reverse('search') + '?q=Test Product')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Results for "Test Product"')
        self.assertContains(response, 'Test Product')


class ProductHomeListViewTest(TestCase):
    """ Product Home List View Test """

    def setUp(self):
        """ Set up for product home list view tests """
        self.product1 = Product.objects.create(
            name='Product 1',
            description='Description for Product 1',
            count=5,
            price=10.99,
            active=True,
        )
        self.product2 = Product.objects.create(
            name='Product with Stock',
            description='Description for Product with Stock',
            count=10,
            price=15.99,
            active=True,
        )

    def test_product_home_list_view_with_stock(self):
        """ Test product home list view with stock """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_product_home_list_view_without_stock(self):
        """ Test product home list view without stock """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Product 2')


class TestEmailSender(TestCase):
    """ Test Email Sender """

    def test_send_inline_photo_email(self):
        """ Test sending inline photo email """
        user_email = 'test@example.com'
        email_context = {
            'products': [
                {
                    'id': 1,
                    'image_base64': 'fake_base64_data',
                },
            ],
        }

        with patch('E_Shop_Frontend.Products.views.EmailSender.send_inline_photo_email') as mock_send_email:
            EmailSender.send_inline_photo_email(user_email, email_context)
            mock_send_email.assert_called_once_with(user_email, email_context)


class TestPaymentProcessor(TestCase):
    """ Test Payment Processor """

    def test_process_payment_card_error(self):
        """ Test processing payment with a card error """
        product = MagicMock()
        product.price = 10
        product.count = 1
        token = 'fake_token'
        request = MagicMock()

        with patch('stripe.Charge.create') as mock_charge_create:
            mock_charge_create.side_effect = stripe.error.CardError('Card error message', 'param', 'code')
            result, error = PaymentProcessor.process_payment(product, token, request)

            self.assertFalse(result)
            self.assertEqual(error, 'Card error message')

    def test_process_payment_out_of_stock(self):
        """ Test processing payment for an out-of-stock product """
        product = MagicMock()
        product.price = 10
        product.count = 0
        token = 'fake_token'
        request = MagicMock()

        payment_processor = PaymentProcessor()
        result, error = payment_processor.process_payment(product, token, request)

        self.assertFalse(result)
        self.assertEqual(error, "Product is out of stock.")


class PaymentViewTestCase(TestHelpers):
    """ Payment View Test Case """

    def setUp(self):
        """ Set up for payment view tests """
        self.user = Clients.objects.create_user(username='testuser', password='testpass', email="eeefs@gmail.com")
        self.product = Product.objects.create(name='Test Product', price=10, count=1)
        self.cart = Cart.objects.create(user=self.user)
        self.cart_product = CartProduct.objects.create(cart=self.cart, product=self.product)

    def test_get_payment_page(self):
        """ Test getting the payment page """
        self.client.login(username='testuser', password='testpass')

        stripe_token = self.generate_stripe_token()

        response = self.client.post(reverse('payment_pro', args=[self.product.id]), {'stripeToken': stripe_token})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/payment_success.html')