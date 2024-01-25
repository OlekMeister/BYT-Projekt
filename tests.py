import unittest
from flask import Flask
from flask_testing import TestCase
from your_app_file import app, db, Customer, Vehicle, Service, ServiceHistory, ExternalNotification

class TestApp(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
        return app

    def setUp(self):
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register_customer(self):
        response = self.client.post('/register', data=dict(
            name='John Doe',
            contact_info='john@example.com'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        customer = Customer.query.filter_by(name='John Doe').first()
        self.assertIsNotNone(customer)

    def test_login_customer(self):
        customer = Customer(name='Test User', contact_info='test@example.com')
        db.session.add(customer)
        db.session.commit()

        response = self.client.post('/login', data=dict(
            name='Test User'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello, Test User!', response.data)

    def test_schedule_service(self):
        customer = Customer(name='Test User', contact_info='test@example.com')
        db.session.add(customer)
        db.session.commit()

        vehicle = Vehicle(make='Toyota', model='Camry', year=2020, customer_id=customer.id)
        db.session.add(vehicle)
        db.session.commit()

        self.client.post('/login', data=dict(name='Test User'), follow_redirects=True)

        response = self.client.post('/schedule_service', data=dict(
            vehicle=vehicle.id,
            description='Oil Change',
            scheduled_time='2022-01-01T10:00'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        service = Service.query.filter_by(description='Oil Change').first()
        self.assertIsNotNone(service)
        self.assertEqual(service.status, 'Scheduled')

    def test_service_history(self):
        customer = Customer(name='Test User', contact_info='test@example.com')
        db.session.add(customer)
        db.session.commit()

        vehicle = Vehicle(make='Toyota', model='Camry', year=2020, customer_id=customer.id)
        db.session.add(vehicle)
        db.session.commit()

        service = Service(description='Oil Change', vehicle_id=vehicle.id, status='Completed')
        db.session.add(service)
        db.session.commit()

        history_entry = ServiceHistory(service_id=service.id, description='Replaced oil filter')
        db.session.add(history_entry)
        db.session.commit()

        self.client.post('/login', data=dict(name='Test User'), follow_redirects=True)

        response = self.client.get(f'/service_history/{service.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Replaced oil filter', response.data)

    def test_external_notifications(self):
        customer = Customer(name='Test User', contact_info='test@example.com')
        db.session.add(customer)
        db.session.commit()

        vehicle = Vehicle(make='Toyota', model='Camry', year=2020, customer_id=customer.id)
        db.session.add(vehicle)
        db.session.commit()

        service = Service(description='Oil Change', vehicle_id=vehicle.id, status='Completed')
        db.session.add(service)
        db.session.commit()

        notification = ExternalNotification(service_id=service.id, message='Your service is completed')
        db.session.add(notification)
        db.session.commit()

        self.client.post('/login', data=dict(name='Test User'), follow_redirects=True)

        response = self.client.get(f'/external_notifications/{service.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your service is completed', response.data)

    def test_invalid_login(self):
        response = self.client.post('/login', data=dict(
            name='Nonexistent User'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_duplicate_registration(self):
        customer = Customer(name='Test User', contact_info='test@example.com')
        db.session.add(customer)
        db.session.commit()

        response = self.client.post('/register', data=dict(
            name='Test User',
            contact_info='test@example.com'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'That username already exists', response.data)

    def test_responsive_design(self):
        response = self.client.get('/', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Responsive Design Test Passed', response.data)

if __name__ == '__main__':
    unittest.main()
