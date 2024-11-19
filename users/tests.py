from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core import mail
from .models import User, Wallet, ActivationCode, Transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
import jwt
from datetime import datetime, timedelta


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.valid_payload = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'Testpassword123',
            'phone_number': '08012345678'
        }
        self.invalid_payload = {
            'username': '',
            'email': 'invalid-email',
            'password': '',
            'phone_number': ''
        }

    def test_register_valid_user(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'true')
        self.assertIn('Registration successful', response.data['message'])

        # Check that the user was created
        self.assertTrue(User.objects.filter(email=self.valid_payload['email']).exists())

        # Check that the wallet was created
        user = User.objects.get(email=self.valid_payload['email'])
        self.assertTrue(Wallet.objects.filter(user=user).exists())

        # Check that the activation code was created
        self.assertTrue(ActivationCode.objects.filter(user=user).exists())

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Account Activation', mail.outbox[0].subject)
        self.assertIn('Use the following code to activate your account', mail.outbox[0].body)

    def test_register_invalid_user(self):
        """Test registration with invalid payload."""
        response = self.client.post(self.register_url, self.invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Ensure no user is created
        self.assertFalse(User.objects.filter(email=self.invalid_payload['email']).exists())

        # Ensure no email is sent
        self.assertEqual(len(mail.outbox), 0)


class UserWalletFundingViewTestCase(TestCase):

    def setUp(self):
        # Create a test user with the required fields (email, phone_number)
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            phone_number='1234567890',
            password='password123'
        )

        # Create a wallet for the test user
        self.wallet = Wallet.objects.create(
            user=self.user,
            account_number='1234567890',
            balance=100.00,
            ledger_balance=100.00,
            status=Wallet.ACTIVE  # Assume status is ACTIVE
        )

        payload = {
            'user_id': self.user.id,
            'email': self.user.email,
            'exp': datetime.utcnow() + timedelta(days=1)
        }

        # Simulate JWT token generation (mock or use a real library for generating a token)
        self.token = jwt.encode(payload, 'secret', algorithm='HS256')

        # Use the token in cookies
        self.client.cookies['jwt'] = self.token

        # URL to fund the wallet
        self.url = reverse('user_wallet_funding')

        # Set the Authorization header or JWT token cookie
        self.client.cookies['jwt'] = self.token


class UserWalletWithdrawalViewTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            phone_number='1234567890',
            password='password123'
        )

        # Create a wallet for the test user with an initial balance of 100
        self.wallet = Wallet.objects.create(
            user=self.user,
            account_number='1234567890',
            balance=100.00,  # Set an initial balance
            ledger_balance=100.00,  # Set the ledger balance
            status=Wallet.ACTIVE  # Ensure the wallet is active
        )

        # Generate JWT token with expiration
        payload = {
            'id': self.user.id,  # Ensure the key matches what the view expects
            'email': self.user.email,
            'exp': datetime.utcnow() + timedelta(days=1)  # Token expiration set for 1 day
        }
        self.token = jwt.encode(payload, 'secret', algorithm='HS256')

        # Use the token in cookies
        self.client.cookies['jwt'] = self.token

        # URL for the withdrawal endpoint
        self.url = reverse('withdraw_fund')

    def test_withdraw_funds(self):
        # Set the withdrawal amount
        withdrawal_amount = 50.00

        # Make a POST request to withdraw funds
        response = self.client.post(self.url, data={'amount': withdrawal_amount}, format='json')

        # Reload the wallet from the database to check updated balance
        self.wallet.refresh_from_db()

        # Assert the response is successful (assuming 200 status code for successful withdrawal)
        self.assertEqual(response.status_code, 201)

        # Check if the response contains the correct message
        self.assertEqual(response.data['message'], 'Transaction is pending approval')

    def test_withdraw_insufficient_balance(self):
        # Set a withdrawal amount greater than the wallet balance
        withdrawal_amount = 150.00

        # Make a POST request to withdraw funds
        response = self.client.post(self.url, data={'amount': withdrawal_amount}, format='json')

        # Assert the response indicates insufficient funds
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Insufficient Fund.')

    def test_withdraw_zero_funds(self):
        # Set the withdrawal amount to 0
        withdrawal_amount = 0.00

        # Make a POST request to withdraw funds
        response = self.client.post(self.url, data={'amount': withdrawal_amount}, format='json')

        # Assert the response indicates that withdrawal of zero is not allowed
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Amount must be greater than 0.')

    def test_withdraw_funds_wallet_inactive(self):
        # Set the wallet status to INACTIVE
        self.wallet.status = Wallet.INACTIVE
        self.wallet.save()

        # Set the withdrawal amount
        withdrawal_amount = 50.00

        # Make a POST request to withdraw funds
        response = self.client.post(self.url, data={'amount': withdrawal_amount}, format='json')

        # Assert that the response indicates the wallet is inactive
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Wallet is not active. Cannot fund the wallet.')

