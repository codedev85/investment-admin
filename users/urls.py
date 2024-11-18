from django.contrib import admin
from django.urls import path, include
from .views import RegisterView,LoginView,UserView,LogOutView,ActivateAccountView,InvestmentPlanListView,InvestmentPlanView,SubscribeToInvestmentPlanView,UserWalletDetailsView,UserWalletFundingView,UserFetchTransactionView,UserWalletWithdrawalView,TokenVerificationView,ValidateActivationCodeView

urlpatterns = [

    path("register", RegisterView.as_view()),
    path("login", LoginView.as_view()),
    path("user-details", UserView.as_view()),
    path("logout", LogOutView.as_view()),
    path('activate/<int:uid>/<str:token>/', ActivateAccountView.as_view(), name='activate-account'),
    path('investment-plans', InvestmentPlanListView.as_view()),
    path('investment/plans/<int:id>/', InvestmentPlanView.as_view(), name='investment-plan-detail'),
    path('investment/plans/subscribe', SubscribeToInvestmentPlanView.as_view(), name='subscribe-investment-plan'),
    path('wallet/details', UserWalletDetailsView.as_view(), name='user_wallet_details'),
    path('fund/wallet', UserWalletFundingView.as_view(), name='user_wallet_funding'),
    path('fetch/transactions',UserFetchTransactionView.as_view(), name='fetch_transactions'),
    path('withdraw/fund',UserWalletWithdrawalView.as_view(), name='withdraw_fund'),
    path('validate/token',TokenVerificationView.as_view(), name='validate_token'),
    path('activate/code', ValidateActivationCodeView.as_view(), name='activate_code'),




]