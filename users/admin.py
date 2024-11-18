from django.contrib import admin

# Register your models here.
# investments/admin.py

from django.contrib import admin
from .models import InvestmentPlan, InvestmentSubscription, Transaction


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'description', 'min_investment_amount', 'max_investment_amount', 'duration_in_months', 'return_rate',
        'created_at', 'updated_at')
    search_fields = ['name', 'description']
    list_filter = ['created_at', 'updated_at']

    def has_change_permission(self, request, obj=None):
        # Restrict update and delete to admins only
        return request.user.is_superuser

    def has_add_permission(self, request):
        # Restrict adding new investment plans to admins only
        return request.user.is_superuser


@admin.register(InvestmentSubscription)
class InvestmentSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'investment_plan', 'subscription_date', 'amount_invested', 'status')
    search_fields = ['user__email', 'investment_plan__name']
    list_filter = ['status', 'subscription_date']


# Custom admin actions
def approve_transaction(modeladmin, request, queryset):
    # Approve all selected transactions
    queryset.update(status=Transaction.APPROVED)
    for transaction in queryset:
        # Save the approved transaction, which will trigger balance adjustments
        transaction.save()
    modeladmin.message_user(request, "Selected transactions have been approved.")


approve_transaction.short_description = "Approve selected transactions"


def reject_transaction(modeladmin, request, queryset):
    # Reject all selected transactions
    queryset.update(status=Transaction.REJECTED)
    modeladmin.message_user(request, "Selected transactions have been rejected.")


reject_transaction.short_description = "Reject selected transactions"


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'status', 'transaction_date', 'balance_after_transaction']
    actions = [approve_transaction, reject_transaction]  # Add actions for approval and rejection


admin.site.register(Transaction, TransactionAdmin)
