# Django Project ( Investment Application )  with Mailtrap Email Configuration

This project is a Django-based web application with email functionality configured using Mailtrap. Follow the setup instructions below to get started.

---

## Table of Contents
1. [Requirements](#requirements)
2. [Setup Instructions](#setup-instructions)
3. [Create Env](#create-env)
4. [Set Up Virtual Environment](#setup-virtual-environment)
5. [Install Packages](#install-packages)
6. [Apply Migrations](#apply-migrations)
7. [Run Server](#run-server)
8. [Hosted Url & Admin Credentials](#hosted-url-&-admin-credentials)


---

## 1. Requirements

Ensure you have the following installed:

- Python 3.8 or later
- Django 3.x or later
- pip (Python package installer)
- A virtual environment tool (optional but recommended)

---

## Setup Instructions

### 2. Clone the Repository
```bash
git clone https://github.com/codedev85/investment_admin.git
cd <project-directory>


```
## 3. Create Env
```
 sudo nano .env
```

## Add the following parameters to .env
```
DJANGO_SECRET_KEY="django-insecure-7cv%)jt7$cz&(u%ewxpvb#5(#cd%htvu9x#_ih(70jcr^&8up5"
DEBUG=True

# Database settings
DB_NAME="investment_db"
DB_USER="root"
DB_PASSWORD=""
DB_HOST="127.0.0.1"
DB_PORT="3306"

# Other secret keys or API keys
MY_API_KEY="your-api-key-here"

# i used mailtrap for sending mail , you need to add the crednetials here 
EMAIL_HOST ='sandbox.smtp.mailtrap.io'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

```

## 4. Setup Virtual Environment 
```
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```
## 5. Install Packages
```
pip install -r requirements.txt
```
## 6. Apply Migrations
```
python manage.py makemigrations
python manage.py migrate
```
## 7. Run Server
```
python manage.py runserver
```
## 8. Hosted Url & Admin Credentials
```
url : https://investment.veloxsolution.ng/admin
email : admin2@admin.com
password : password
```