from rest_framework import serializers
from .models import User, InvestmentPlan, InvestmentSubscription, Wallet


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'password', 'role', 'first_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)

        if password is not None:
            instance.set_password(password)
            instance.save()
            return instance


class InvestmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentPlan
        fields = ['id', 'name', 'description', 'min_investment_amount', 'max_investment_amount', 'duration_in_months',
                  'return_rate', 'created_at', 'updated_at']


class InvestmentSubscriptionSerializer(serializers.ModelSerializer):
    investment_plan = serializers.PrimaryKeyRelatedField(queryset=InvestmentPlan.objects.all())

    class Meta:
        model = InvestmentSubscription
        fields = ['id', 'user', 'investment_plan', 'subscription_date', 'amount_invested', 'status', 'date_of_returns']
        read_only_fields = ['status', 'subscription_date']


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id','account_number', 'balance', 'previous_balance', 'status','ledger_balance', 'created_at', 'updated_at']
