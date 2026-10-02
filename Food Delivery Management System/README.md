# URBAN KITCHEN – Food & Beverage
### Food Delivery & Catering Management System

A full-featured, responsive Python Flask web application and console system designed for **Urban Kitchen – Food & Beverage**. It features artisanal catering menus, multi-restaurant browsing, shopping cart, multi-method checkout (Cash on Delivery, UPI, Cards), order lifecycle tracking, customer profiles, delivery partner dispatch portal, and a restaurant manager portal.

---

## 🌟 Key Highlights & Design Aesthetic
- **Visual Design**: Follows the clean catering aesthetic of `reference/theme.png` with a light mint (`#EAF4EC`) and white palette, deep green primary (`#2F6B4A`), Google Font Poppins, rounded cards (14px), and royalty-free high-resolution food photography.
- **Brand Assets**: Circular black-and-white crest logo (`static/images/logo.png`) featured in the sticky frosted-glass navigation bar and footer.
- **Preserved Business Logic**: 100% backward-compatible with original CSV files (`user.csv`, `restaurant.csv`, `orders.csv`, `payments.csv`) and console menu (`main.py`).

---

## 🚀 Quick Start Instructions

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Web Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

### 4. Run the Console System (Optional)
The original console menu continues to work alongside the web app:
```bash
python main.py
```

---

## 🔑 Default Credentials & Demo Accounts

### 1. Customer Demo Account
- **Email**: `alice@urbankitchen.com` (or create any account via the Register tab)
- **Password**: `password123`

### 2. Restaurant Operations Manager
- **URL**: `http://127.0.0.1:5000/admin/login`
- **Admin Password**: `admin123` (configured in `config.py`)

### 3. Delivery Agent Portal
- **URL**: `http://127.0.0.1:5000/delivery/login`
- **Agent ID**: `DA-101`
- **Name**: `Rajesh Kumar`
- **Phone**: `9876543211`
- **Vehicle**: `KA-01-AB-1234`

---

## 📁 Project Structure

```
├── app.py                      # Flask application and route handlers
├── config.py                   # App config, secrets, rates, and brand tokens
├── Cart.py                     # Cart business logic and row formatting
├── FoodItem.py                 # Food item class definition
├── User.py                     # User profile, authentication, and PBKDF2 hashing
├── restaurant.py               # Restaurant catalog, menu grouping, and CSV persistence
├── order.py                    # Order lifecycle, ID generator, and tracking
├── payment.py                  # Payment methods (COD, UPI, Credit/Debit card)
├── delivery.py                 # Delivery partner assignment and status updates
├── utils.py                    # Bill calculation (delivery fee + 5% GST)
├── main.py                     # Interactive console menu
├── requirements.txt            # Python dependencies
├── user.csv                    # User accounts data storage
├── restaurant.csv              # Restaurant and menu data storage
├── orders.csv                  # Order transactions data storage
├── payments.csv                # Payment receipts data storage
├── static/
│   ├── css/
│   │   └── style.css           # Catering theme styles and responsive layout
│   ├── js/
│   │   └── main.js             # Cart quantities, payment tabs, mobile drawer
│   └── images/
│       ├── logo.png            # Official Urban Kitchen crest logo
│       ├── hero_food.jpg       # Hero circular food dish
│       ├── feedback1.jpg       # Customer review dish 1
│       ├── feedback2.jpg       # Customer review dish 2
│       ├── feedback3.jpg       # Customer review dish 3
│       └── cta_sandwich.jpg    # Split CTA artisan sandwich
└── templates/
    ├── base.html               # Sticky navbar, flash banners, footer
    ├── index.html              # Home page matching reference/theme.png
    ├── auth.html               # Register and login tabbed interface
    ├── restaurants.html        # Restaurant browsing and rating filters
    ├── menu.html               # Categorized menu with availability badges
    ├── cart.html               # Shopping cart and bill summary
    ├── checkout.html           # Payment method selection and order placement
    ├── receipt.html            # Order receipt and printable invoice
    ├── orders.html             # Customer active tracking and order history
    ├── order_detail.html       # Visual status progression timeline
    ├── profile.html            # Profile viewer, updates, and password changes
    ├── delivery_login.html     # Delivery agent authentication
    ├── delivery_dashboard.html # Available deliveries, pickup, and transit completion
    ├── admin_login.html        # Restaurant manager passcode entry
    └── admin_dashboard.html    # Add restaurants, update dishes, toggle availability
```
