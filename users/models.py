from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from datetime import timedelta
import logging


# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True)
    ROLE_CHOICES = [('INVESTOR', 'Investor'), ('ADMIN', 'Admin')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='INVESTOR')
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password', 'phone_number']
    objects = CustomUserManager()

    def __str__(self):
        return self.email


class InvestmentPlan(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    min_investment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_investment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration_in_months = models.PositiveIntegerField()
    return_rate = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Wallet(models.Model):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='wallets')
    account_number = models.CharField(max_length=255, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ledger_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet for {self.user.email} - Account: {self.account_number}"

    # def save(self, *args, **kwargs):
    #     # Update previous_balance before saving a new wallet state
    #     if self.pk:
    #         self.previous_balance = self.balance
    #     super().save(*args, **kwargs)


class Transaction(models.Model):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'

    TRANSACTION_TYPES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
    ]

    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

    TRANSACTION_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after_transaction = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, default=PENDING)
    transaction_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} of {self.amount} on {self.transaction_date}"

    def save(self, *args, **kwargs):
        # Adjust wallet balance based on transaction type before saving the transaction
        if self.transaction_type == self.DEPOSIT:
            self.wallet.ledger_balance += self.amount
        elif self.transaction_type == self.WITHDRAWAL:
            self.wallet.ledger_balance -= self.amount

        if self.status == self.APPROVED:
            # Process the transaction if approved
            if self.transaction_type == self.DEPOSIT:
                self.wallet.ledger_balance -= self.amount
                self.wallet.balance += self.amount
            elif self.transaction_type == self.WITHDRAWAL:
                # self.wallet.ledger_balance -= self.amount
                self.wallet.balance -= self.amount

        # Update the wallet's balance and previous_balance before saving transaction
        self.wallet.save()  # Save the updated wallet balance
        self.balance_after_transaction = self.wallet.balance

        super().save(*args, **kwargs)


class InvestmentSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    investment_plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    subscription_date = models.DateTimeField(auto_now_add=True)
    amount_invested = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Active')
    date_of_returns = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Automatically calculate the date_of_returns if not already set
        if not self.date_of_returns and self.investment_plan and self.subscription_date:
            duration = self.investment_plan.duration_in_months or 0
            # Convert subscription_date to date before adding timedelta
            subscription_date = self.subscription_date.date()
            self.date_of_returns = subscription_date + timedelta(days=duration * 30)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} subscribed to {self.investment_plan.name}"


class ActivationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)  # Store the code (6 digits)
    created_at = models.DateTimeField(auto_now_add=True)  # Time when the code was created

    @property
    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=5)  # 5 minutes expiry
        return timezone.now() > expiration_time
