from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, InvestmentPlanSerializer, InvestmentSubscriptionSerializer, WalletSerializer
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import User, InvestmentPlan, InvestmentSubscription, ActivationCode
import jwt, datetime
from .utils import generate_activation_email
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from .models import Wallet, Transaction
from rest_framework.exceptions import NotFound
from datetime import timedelta
from django.utils.timezone import now
from decimal import Decimal
import random
from django.core.exceptions import ObjectDoesNotExist


# from datetime import datetime, timezone


# from datetime import datetime


# Create your views here.


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            user = serializer.save()
            # serializer.save()
            # activation_link = generate_activation_email(user, request)
            #
            # # Send activation email
            # send_mail(
            #     subject='Activate your account',
            #     message=f'Click the link to activate your account: {activation_link}',
            #     from_email='onyinye@advokc.ng',  # Replace with your Postmark-verified email
            #     recipient_list=[user.email],
            #     fail_silently=False,
            # )

            code = str(random.randint(100000, 999999))

            activation_code = ActivationCode.objects.create(user=user, code=code)

            # Create the link to your frontend
            # frontend_url = 'http://localhost:3000'  # Change to your frontend URL
            # activation_link = f"{frontend_url}/activate-account/{activation_code.code}/"

            # Send the email (for simplicity, you can use Django's built-in send_mail)
            send_mail(
                'Account Activation',
                f'Use the following code to activate your account: {code}. It is valid for 5 minutes.',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
            phone_number = request.data.get('phone_number')

            account_number = phone_number[-10:]

            # Create a wallet for the user with the generated account number
            wallet = Wallet.objects.create(
                user=user,
                account_number=account_number,
                balance=0.00,
                previous_balance=0.00,
                status=Wallet.ACTIVE
            )

            return Response(
                {'status': 'true', 'message': 'Registration successful. Check your email for activation link.'},
                status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    def get(self, request, uid, token):
        user = get_object_or_404(User, pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'message': 'Account activated successfully.'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found')

        if not user.check_password(password):
            raise AuthenticationFailed('Password is incorrect')

        if not user.is_active:
            return Response({
                'status': 'false',
                'message': 'Your account is not activated. Please check your email and activate your account.',
            }, status=400)

        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret', algorithm='HS256')

        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)

        response.data = {
            'status': 'true',
            'message': 'Login was successful',
            'jwt': token,
        }

        return response


class UserView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Authenticated')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Authenticated')

        user = User.objects.filter(id=payload['id']).first()

        serializer = UserSerializer(user)

        return Response(serializer.data)


class LogOutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response


class InvestmentPlanListView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):

        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Authenticated')
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Authenticated')

        user = User.objects.filter(id=payload['id']).first()

        # Only allow users with the role of "INVESTOR" to view this endpoint
        if user.role != 'INVESTOR':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        investment_plans = InvestmentPlan.objects.all()

        serializer = InvestmentPlanSerializer(investment_plans, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class InvestmentPlanView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Not Authenticated')
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Not Authenticated')

        user = User.objects.filter(id=payload['id']).first()

        # Only allow users with the role of "INVESTOR" to view this endpoint
        if user.role != 'INVESTOR':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        investment_plan = InvestmentPlan.objects.filter(id=id).first()
        if not investment_plan:
            raise NotFound(f"InvestmentPlan with id {id} not found")

        serializer = InvestmentPlanSerializer(investment_plan)

        # Check if the user has an active subscription to the investment plan
        subscription = InvestmentSubscription.objects.filter(
            user=user,
            investment_plan=investment_plan,
            status='Active'  # Check for active subscriptions only
        ).first()

        # Serialize the investment plan
        serializer = InvestmentPlanSerializer(investment_plan)

        # Add subscription details to the response
        response_data = serializer.data
        response_data['is_subscribed'] = subscription is not None
        response_data['subscription_details'] = {
            'subscription_date': subscription.subscription_date if subscription else None,
            'amount_invested': subscription.amount_invested if subscription else None,
            'status': subscription.status if subscription else None,
            'date_of_returns': subscription.date_of_returns if subscription else None,
        }

        return Response(response_data, status=status.HTTP_200_OK)
        # return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeToInvestmentPlanView(APIView):

    def post(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Not Authenticated')
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Not Authenticated')

        user = User.objects.filter(id=payload['id']).first()

        if not user:
            raise AuthenticationFailed('User not found')

        # Retrieve investment plan ID and amount invested from the request
        investment_plan_id = request.data.get('investment_plan')
        amount_invested = request.data.get('amount_invested')

        if not investment_plan_id or not amount_invested:
            return Response({'status': 'false', 'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        investment_plan = InvestmentPlan.objects.filter(id=investment_plan_id).first()
        if not investment_plan:
            return Response({'status': 'false', 'error': 'Investment Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the amount invested is within the allowed range
        min_investment = investment_plan.min_investment_amount
        max_investment = investment_plan.max_investment_amount

        if amount_invested < min_investment or amount_invested > max_investment:
            return Response({
                'status': 'false',
                'error': f"Amount invested must be between {min_investment} and {max_investment}."
            }, status=status.HTTP_400_BAD_REQUEST)

        existing_subscription = InvestmentSubscription.objects.filter(
            user=user,
            investment_plan=investment_plan,
            status='Active'
        ).first()

        if existing_subscription:
            return Response({'status': 'false', 'error': 'You have already subscribed to this plan.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Calculate the due date for returns
        subscription_date = now()
        duration = investment_plan.duration_in_months or 0
        date_of_returns = subscription_date + timedelta(days=duration * 30)

        # Prepare the data for subscription
        data = {
            'user': user.id,
            'investment_plan': investment_plan.id,
            'amount_invested': amount_invested,
            'status': 'Active',
            'date_of_returns': date_of_returns,
        }

        # Use the serializer to save the subscription
        serializer = InvestmentSubscriptionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserWalletDetailsView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Authenticated')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Authenticated')

        user = User.objects.filter(id=payload['id']).first()

        if not user:
            raise AuthenticationFailed('User not found')

        wallet = Wallet.objects.get(user_id=user.id)

        if not wallet:
            return Response({'status': 'false', "error": "No wallets found for this user."}, status=404)

        serializer = WalletSerializer(wallet)

        return Response(serializer.data)


class UserWalletFundingView(APIView):
    def post(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Authenticated')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Authenticated')

        user = get_user_model().objects.filter(id=payload['id']).first()

        if not user:
            raise AuthenticationFailed('User not found')

        # Fetch the user's wallet
        wallet = Wallet.objects.get(user_id=user.id)

        if not wallet:
            return Response({'status': 'false', "error": "No wallet found for this user."}, status=404)

        # Check if the wallet status is active
        if wallet.status != 'active':
            return Response({'status': 'false', 'error': 'Wallet is not active. Cannot fund the wallet.'},
                            status=400)

        # Get the amount from the request body and validate it
        amount = request.data.get('amount')

        try:
            amount = Decimal(amount)
            if amount <= 0:
                return Response({'status': 'false', 'error': 'Amount must be greater than 0.'}, status=400)
        except (ValueError, TypeError):
            return Response({'status': 'false', 'error': 'Invalid amount.'}, status=400)

        # Create a pending transaction
        transaction = Transaction.objects.create(
            wallet=wallet,
            transaction_type=Transaction.DEPOSIT,
            amount=amount,
            balance_after_transaction=wallet.ledger_balance + amount,  # Ledger balance is updated
            status=Transaction.PENDING
        )

        # wallet.ledger_balance += amount
        # wallet.save()

        return Response(
            {'status': 'true', 'message': 'Transaction is pending approval', 'transaction_id': transaction.id},
            status=status.HTTP_201_CREATED
        )


class UserFetchTransactionView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Authenticated')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Authenticated')

        user = User.objects.filter(id=payload['id']).first()

        if not user:
            raise AuthenticationFailed('User not found')

        # Fetch the user's wallet
        wallet = Wallet.objects.filter(user_id=user.id).first()

        if not wallet:
            raise AuthenticationFailed('Wallet not found')

        # Fetch all transactions associated with the wallet
        transactions = Transaction.objects.filter(wallet_id=wallet.id)

        # Serialize the transaction data
        transaction_data = [
            {
                'transaction_id': transaction.id,
                'transaction_type': transaction.transaction_type,
                'amount': str(transaction.amount),
                'status': transaction.status,
                'balance_after_transaction': str(transaction.balance_after_transaction),
                'created_at': transaction.created_at,
            }
            for transaction in transactions
        ]

        return Response(
            {'status': 'true', 'transactions': transaction_data},
            status=status.HTTP_200_OK
        )


class UserWalletWithdrawalView(APIView):
    def post(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Authenticated')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Authenticated')

        user = get_user_model().objects.filter(id=payload['id']).first()

        if not user:
            raise AuthenticationFailed('User not found')

        # Fetch the user's wallet
        wallet = Wallet.objects.get(user_id=user.id)

        if not wallet:
            return Response({'status': 'false', "error": "No wallet found for this user."}, status=404)

        # Check if the wallet status is active
        if wallet.status != 'active':
            return Response({'status': 'false', 'error': 'Wallet is not active. Cannot fund the wallet.'},
                            status=400)

        # Get the amount from the request body and validate it
        amount = request.data.get('amount')

        try:
            amount = Decimal(amount)
            if amount <= 0:
                return Response({'status': 'false', 'error': 'Amount must be greater than 0.'}, status=400)
        except (ValueError, TypeError):
            return Response({'status': 'false', 'error': 'Invalid amount.'}, status=400)

        if wallet.balance < amount:
            return Response({'status': 'false', 'error': 'Insufficient Fund.'}, status=400)

        # Create a pending transaction
        transaction = Transaction.objects.create(
            wallet=wallet,
            transaction_type=Transaction.WITHDRAWAL,
            amount=amount,
            # balance_after_transaction=wallet.ledger_balance + amount,  # Ledger balance is updated
            status=Transaction.PENDING
        )

        # wallet.ledger_balance += amount
        # wallet.save()

        return Response(
            {'status': 'true', 'message': 'Transaction is pending approval', 'transaction_id': transaction.id},
            status=status.HTTP_201_CREATED
        )


class TokenVerificationView(APIView):
    def get(self, request):
        # Retrieve the token from cookies
        token = request.COOKIES.get('jwt')

        if not token:
            return Response({'status': 'false', 'message': 'Token not provided.'}, status=401)

        try:
            # Decode the token to check validity
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])

            # Check if the token has expired
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                raise jwt.ExpiredSignatureError

            return Response({'status': 'true', 'message': 'Token is valid.'}, status=200)

        except jwt.ExpiredSignatureError:
            return Response({'status': 'false', 'message': 'Token has expired.'}, status=401)
        except jwt.InvalidTokenError:
            return Response({'status': 'false', 'message': 'Invalid token.'}, status=401)


class ValidateActivationCodeView(APIView):

    def post(self, request):
        # Get the code from request data
        code = request.data.get('code')

        # Check if the code is provided
        if not code:
            return Response({'status': 'false', 'message': 'Code is required', 'error': 'Code is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Try to fetch the activation code from the database
            activation_code = ActivationCode.objects.get(code=code)
        except ObjectDoesNotExist:
            return Response({'status': 'false', 'message': 'Invalid Code', 'error': 'Invalid Code.'},
                            status=status.HTTP_404_NOT_FOUND)

        # Check if the activation code is expired
        if activation_code.is_expired:
            return Response({'status': 'false', 'message': 'Code has expired', 'error': 'Code has expired.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is the one who generated the code
        # if activation_code.user.id != request.user.id:
        #     return Response({'status': 'false', 'message': 'This code is not valid for the current user.',
        #                      'error': 'This code is not valid for the current user.'},
        #                     status=status.HTTP_403_FORBIDDEN)

        # Activate the user
        user = activation_code.user
        user.is_active = True
        user.save()

        # Optionally delete the activation code after successful activation
        activation_code.delete()

        return Response({'status': 'true', 'message': 'Account successfully activated.'}, status=status.HTTP_200_OK)
