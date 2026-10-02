import os
import shutil
import tempfile
import time
import unittest
from app import app
import config


class UrbanKitchenTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Save original working directory
        cls.original_cwd = os.getcwd()
        cls.temp_dir = tempfile.TemporaryDirectory()

        # Copy all CSV files to the temporary isolated directory
        for filename in ["user.csv", "restaurant.csv", "orders.csv", "payments.csv"]:
            src = os.path.join(cls.original_cwd, filename)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(cls.temp_dir.name, filename))

        # Switch working directory to the temporary folder so tests never touch real CSVs
        os.chdir(cls.temp_dir.name)

    @classmethod
    def tearDownClass(cls):
        # Restore original working directory and clean up temporary directory
        os.chdir(cls.original_cwd)
        cls.temp_dir.cleanup()

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Urban Kitchen', response.data)
        self.assertIn(b'Best Catering', response.data)
        self.assertIn(b'Customer Feedback', response.data)
        self.assertIn(b'Artisan Seafood Fettuccine', response.data)

    def test_02_restaurants_page(self):
        response = self.client.get('/restaurants')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Urban Bistro', response.data)

        # Test search filter for dish name
        search_res = self.client.get('/restaurants?q=Pizza')
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b'Artisan Pizzeria', search_res.data)

    def test_03_restaurant_menu(self):
        response = self.client.get('/restaurant/R101')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Truffle Mushroom Bruschetta', response.data)
        self.assertIn(b'Available', response.data)

    def test_04_user_registration_and_login(self):
        # Register a unique test user
        unique_email = f"testuser_{int(time.time() * 1000)}@example.com"
        reg_data = {
            'name': 'Test User',
            'email': unique_email,
            'phone': '9876500000',
            'address': '101 Gourmet Lane',
            'password': 'password123'
        }
        res_reg = self.client.post('/register', data=reg_data, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)

        # Login test user
        login_data = {
            'email': unique_email,
            'password': 'password123'
        }
        res_login = self.client.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Test User', res_login.data)

    def test_05_cart_and_checkout_flow(self):
        # 1. Add item to cart
        add_res = self.client.post('/cart/add', data={
            'restaurant_id': 'R101',
            'food_id': 'F101',
            'quantity': '2'
        }, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)

        # 2. View cart
        cart_res = self.client.get('/cart')
        self.assertEqual(cart_res.status_code, 200)
        self.assertIn(b'Truffle Mushroom Bruschetta', cart_res.data)

        # 3. Log in session
        with self.client.session_transaction() as sess:
            sess['user_id'] = '1000'
            sess['user_email'] = 'muniklalluvadiya@gmail.com'
            sess['user_name'] = 'Munik Lalluvadiya'

        # 4. View checkout
        checkout_view = self.client.get('/checkout')
        self.assertEqual(checkout_view.status_code, 200)
        self.assertIn(b'Finalize Your Order', checkout_view.data)

        # 5. Place order via Cash on Delivery
        place_res = self.client.post('/checkout', data={
            'payment_method': 'Cash on Delivery',
            'delivery_address': 'Zadeshwar, Bharuch'
        }, follow_redirects=True)
        self.assertEqual(place_res.status_code, 200)
        self.assertIn(b'Thank You for Your Order', place_res.data)

    def test_06_delivery_agent_portal(self):
        # Delivery agent login
        agent_data = {
            'agent_id': 'DA-TEST',
            'name': 'Speedy Rider',
            'phone': '9876511111',
            'vehicle': 'KA-05-ZZ-9999'
        }
        login_res = self.client.post('/delivery/login', data=agent_data, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Speedy Rider', login_res.data)
        self.assertIn(b'Available Catering Deliveries', login_res.data)

    def test_07_admin_manager_portal(self):
        # 1. Manager login
        login_res = self.client.post('/admin/login', data={
            'admin_password': config.ADMIN_PASSWORD
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Restaurant & Menu Operations', login_res.data)

        # 2. Toggle availability
        toggle_res = self.client.post('/admin/menu/toggle-availability', data={
            'restaurant_id': 'R101',
            'food_id': 'F101',
            'current_status': 'True'
        }, follow_redirects=True)
        self.assertEqual(toggle_res.status_code, 200)

        # Toggle back to True
        toggle_back = self.client.post('/admin/menu/toggle-availability', data={
            'restaurant_id': 'R101',
            'food_id': 'F101',
            'current_status': 'False'
        }, follow_redirects=True)
        self.assertEqual(toggle_back.status_code, 200)


if __name__ == '__main__':
    unittest.main()
