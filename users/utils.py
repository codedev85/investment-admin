from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse

# def generate_activation_email(user, request):
#     token = default_token_generator.make_token(user)
#     activation_link = request.build_absolute_uri(
#         reverse('activate-account', kwargs={'uid': user.pk, 'token': token})
#     )
#     return activation_link

# def generate_activation_email(user, request):
#     token = default_token_generator.make_token(user)
#     frontend_url = 'http://localhost:3000'
#     activation_link = f"{frontend_url}/activate-account/{user.pk}/{token}/"
#     return activation_link


import random
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from .models import ActivationCode


def generate_activation_email(user, request):
    # Generate a random 6-digit code
    code = str(random.randint(100000, 999999))

    # Save the code and its expiration time
    activation_code = ActivationCode.objects.create(user=user, code=code)

    # Create the link to your frontend
    frontend_url = 'http://localhost:3000'  # Change to your frontend URL
    activation_link = f"{frontend_url}/activate-account/{activation_code.code}/"

    # Send the email (for simplicity, you can use Django's built-in send_mail)
    send_mail(
        'Account Activation',
        f'Use the following code to activate your account: {code}. It is valid for 5 minutes.',
        'from@example.com',
        [user.email],
        fail_silently=False,
    )

    return activation_link
