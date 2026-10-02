import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application Configuration (read from environment / .env file)
SECRET_KEY = os.environ.get("SECRET_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# Branding
BRAND_NAME = "URBAN KITCHEN – Food & Beverage"
SITE_TITLE = "Urban Kitchen"
LOGO_PATH = "images/logo.png"

# Pricing & Billing (aligned with utils.py)
DELIVERY_CHARGE = 40.0
GST_RATE = 0.05  # 5%
CURRENCY_SYMBOL = "₹"
