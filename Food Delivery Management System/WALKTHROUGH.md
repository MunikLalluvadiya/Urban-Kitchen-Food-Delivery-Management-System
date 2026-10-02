# Walkthrough Summary: Urban Kitchen – Food Delivery Management System

---

## 1. What the Project Is
Urban Kitchen is a full-stack food delivery and catering management web application built with Python and Flask, running on top of an existing Python console application. It allows customers to browse partner restaurants, customize dishes into a cart, and place orders with flexible payment options (Cash on Delivery, UPI, Cards). It also includes a Delivery Agent portal to accept and complete deliveries, and a Restaurant Manager portal to manage menus and toggle item availability. All data is stored directly in simple CSV files without external database servers.

---

## 2. Project Folder & File List

| File / Folder | Short Purpose (One-Line Explanation) |
| :--- | :--- |
| `app.py` | Main Flask web controller routing URLs, managing sessions, and handling form submissions. |
| `config.py` | Configuration file that loads environment variables, branding text, and tax/delivery rates. |
| `User.py` | Customer class handling registration, login, profile updates, and secure PBKDF2 password hashing. |
| `restaurant.py` | Restaurant class managing restaurant details, menu items, search filtering, and CSV updates. |
| `FoodItem.py` | Model class representing individual food items (ID, Name, Category, Price, Availability). |
| `Cart.py` | Shopping cart class tracking selected dishes, quantities, restaurant ID, and item subtotals. |
| `order.py` | Order management class that generates order IDs, serializes dishes, and tracks order statuses. |
| `payment.py` | Payment processor generating payment IDs and handling COD, UPI, Credit Card, and Debit Card. |
| `delivery.py` | Delivery Agent class tracking available orders, route acceptance, and delivery completion. |
| `utils.py` | Helper module calculating order bills (fixed delivery fee of ₹40.00 and 5% GST). |
| `main.py` | Original interactive command-line console interface for customers and delivery agents. |
| `requirements.txt` | Python package list containing Flask, Werkzeug, Jinja2, and python-dotenv. |
| `.env` | Local environment secrets file storing the Flask `SECRET_KEY` and `ADMIN_PASSWORD`. |
| `.env.example` | Template file showing what environment variables need to be set with comments only. |
| `.gitignore` | Git rules preventing `.env` and temporary Python cache files from being committed. |
| `README.md` | Overview documentation with setup guides, credentials, and feature summaries. |
| `test_suite.py` | Automated test script that checks home page, cart, checkout, delivery, and admin features in an isolated environment. |
| `user.csv` | Comma-separated database table storing customer account details and hashed passwords. |
| `restaurant.csv` | Comma-separated database table storing restaurants and their menus in semicolon format. |
| `orders.csv` | Comma-separated database table recording placed orders, item lists, amounts, and statuses. |
| `payments.csv` | Comma-separated database table storing payment transaction IDs, methods, and statuses. |
| `static/css/style.css` | Custom stylesheet implementing the clean catering visual design and responsive layout. |
| `static/js/main.js` | Client-side JavaScript handling the mobile drawer, quantity controls, and payment tabs. |
| `static/images/` | Folder containing `logo.png` and locally saved food photography (`hero_food.jpg`, etc.). |
| `templates/` | Folder containing 15 Jinja2 HTML templates for all customer, agent, and admin pages. |

---

## 3. How to Run the Project (Exact Steps & Commands)

### Step 1: Open Terminal in Project Root
Make sure your terminal is opened inside `e:\Data Science\PROJECTS\Food Delivery Management System`.

### Step 2: Install Required Dependencies
Run the following command to install Flask and python-dotenv:
```bash
pip install -r requirements.txt
```

### Step 3: Verify Environment Secrets File
Ensure a `.env` file exists in the project folder with:
```env
SECRET_KEY=9f8c4e2a1b7d5e6f3c0a8b9d4e5f6a7b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f
ADMIN_PASSWORD=admin123
```

### Step 4: Run the Web Application
Start the Flask web server:
```bash
python app.py
```
Open your web browser and go to:
```
http://127.0.0.1:5000/
```

### Step 5: Run the Console Application (Optional)
In a separate terminal window, you can run the original console menu:
```bash
python main.py
```

### Step 6: Run Automated Tests (Optional)
Run the test suite (it automatically runs on temporary copies and never touches your real CSV files):
```bash
python -m unittest test_suite.py
```

---

## 4. Every Page and URL Explained

### Customer Pages:
1. **Home Page (`/`)**:
   - **Shows:** Hero banner with circular catering plate, 4 circular green badges, 2x4 feature cards (Fast Delivery, Fresh Ingredients, etc.), Customer reviews with food photos, split call-to-action banner, and dark green footer.
   - **Actions:** Click "Order Now" or "Browse Restaurants" to view restaurants; access navigation links; view live cart count.
2. **Sign In & Register (`/auth`, `/login`, `/register`)**:
   - **Shows:** Split layout with catering artwork on the left and tabbed Sign In / Register forms on the right.
   - **Actions:** Switch between tabs; sign in with email and password; create a new account (full name, email, phone, address, password).
3. **Browse Restaurants (`/restaurants`)**:
   - **Shows:** Search bar, minimum rating filter dropdown (All, 4.0+, 4.5+, 4.8+), and a grid of restaurant cards with ratings and locations.
   - **Actions:** Search by restaurant name, location, or food dish; filter by star rating; click "View Menu".
4. **Restaurant Menu (`/restaurant/<restaurant_id>`)**:
   - **Shows:** Restaurant header (rating, location, total items), category filter pills, food items grouped by category (Starters, Main Course, Desserts, Beverages), prices, and availability badges ("Available" or "Out of Stock").
   - **Actions:** Adjust quantity (+ / -); click "Add to Cart" for available dishes; switch restaurants if cart has items from another kitchen.
5. **Shopping Cart (`/cart`)**:
   - **Shows:** Table of chosen items with unit prices, quantity modifiers, item subtotals, restaurant notice, and a bill summary card (Subtotal, Delivery Fee ₹40.00, GST 5%, Grand Total).
   - **Actions:** Change item quantities; remove individual items; empty the entire cart; click "Proceed to Checkout".
6. **Checkout (`/checkout`)**:
   - **Shows:** Pre-filled delivery address, payment method cards (Cash on Delivery, UPI, Credit Card, Debit Card), dynamic input fields for UPI ID / Card numbers, and order summary.
   - **Actions:** Edit delivery address; choose payment method; enter payment details; click "Place Order & Pay" (Order ID and Payment ID are auto-generated).
7. **Order Receipt (`/receipt/<order_id>`)**:
   - **Shows:** Printable receipt with Order ID, Payment ID, Payment Method, Payment Status ("Paid" or "Pending"), date, customer details, restaurant location, and itemized bill.
   - **Actions:** Click "Print Receipt" (opens browser print dialog); click "Track Order" to visit the orders page.
8. **My Orders & Tracking (`/orders`)**:
   - **Shows:** Two tabs: "Active Orders" (status: Preparing, Accepted, Out for Delivery) and "Order History" (Delivered, Cancelled) with color-coded status badges and total amounts.
   - **Actions:** Switch tabs; view order items; click "View Tracking & Details"; click "Cancel Order" on cancellable orders.
9. **Order Details & Progress (`/orders/<order_id>`)**:
   - **Shows:** 4-step status timeline (Placed → Preparing → On Route → Delivered), ordered items breakdown, restaurant info, payment status, and delivery recipient.
   - **Actions:** Cancel order if status is still "Preparing" or "Accepted"; click "View Invoice / Receipt".
10. **Customer Profile (`/profile`, `/profile/change-password`)**:
    - **Shows:** Customer details (User ID, Name, Email, Phone, Address). Passwords are never displayed.
    - **Actions:** Update name, phone number, and address; change password by providing current password and new password.
11. **Sign Out (`/logout`)**:
    - **Actions:** Clears session and redirects to home page with a confirmation message.

### Delivery Partner Pages:
1. **Delivery Agent Login (`/delivery/login`)**:
   - **Shows:** Dedicated delivery agent sign-in card.
   - **Actions:** Enter Agent ID, Full Name, Phone Number, and Vehicle Number to log in.
2. **Delivery Agent Dashboard (`/delivery/dashboard`)**:
   - **Shows:** Agent information banner (Agent ID, vehicle, phone, online status), "Active Deliveries in Transit", "Available Catering Deliveries", and "Completed Deliveries History".
   - **Actions:** Click "Accept Delivery" on available orders; click "Start Transit (Out for Delivery)"; click "Complete Delivery" to mark an order as "Delivered".
3. **Delivery Sign Out (`/delivery/logout`)**:
   - **Actions:** Logs out delivery agent and returns to home.

### Restaurant Manager Pages:
1. **Manager Sign In (`/admin/login`)**:
   - **Shows:** Clean admin passcode login form without any exposed credentials.
   - **Actions:** Enter admin password to access the operations hub.
2. **Manager Dashboard (`/admin/dashboard`)**:
   - **Shows:** Overview statistics (Total Restaurants, Total Menu Items, Total Orders, Gross Revenue), "Add New Restaurant" form, restaurant selector dropdown, and current menu dishes table.
   - **Actions:**
     - Add new restaurant (ID, Name, Location, Rating).
     - Add new food item to the selected restaurant (ID, Name, Category, Price, Availability).
     - 1-Click Toggle Availability button (instantly switches item between "Available" and "Out of Stock").
     - Inline price edit (enter new price and click "Save").
     - Delete food item from restaurant menu.
3. **Manager Sign Out (`/admin/logout`)**:
   - **Actions:** Clears admin session and returns to home.

---

## 5. Full Flow of an Order (From Register to Delivery)

1. **Registration:**
   - A customer opens `http://127.0.0.1:5000/auth?tab=register` and registers with Name, Email, Phone, Address, and Password.
   - The password is salted and hashed using PBKDF2 (`_hash_password()`) and stored in `user.csv`.
2. **Browsing & Menu Selection:**
   - The customer navigates to `/restaurants` and selects a restaurant (e.g. *Urban Bistro & Grill*).
   - On `/restaurant/R101`, the customer adjusts quantities (+ / -) and clicks "Add". The item is stored in the user's Flask session cart.
3. **Cart Review:**
   - On `/cart`, the customer reviews the items. The system calls `calculate_bill()` from `utils.py` to calculate:
     - Subtotal
     - Delivery Charge: ₹40.00
     - GST (5%): Subtotal × 0.05
     - Grand Total: Subtotal + Delivery + GST.
4. **Checkout & Auto-Generated IDs:**
   - The customer clicks "Proceed to Checkout" (`/checkout`).
   - The customer confirms the delivery address and picks a payment method (e.g., *Cash on Delivery* or *UPI*).
   - Upon form submission, the system automatically calls `generate_order_id()` (e.g., `ORD-1010`) and `generate_payment_id()` (e.g., `PAY-1010`).
   - `order.place_order()` saves the order to `orders.csv` with status `"Preparing"`.
   - `payment.process_payment()` records the transaction in `payments.csv`.
   - The shopping cart is emptied.
5. **Receipt Generation:**
   - The customer is redirected to `/receipt/<order_id>` showing an invoice with Order ID, Payment ID, items, and tax breakdown.
6. **Delivery Agent Dispatch:**
   - A delivery agent signs in at `/delivery/login` and visits `/delivery/dashboard`.
   - Under "Available Catering Deliveries", the agent sees the new order (Status: `"Preparing"`) and clicks "Accept Delivery".
   - The order status updates to `"Accepted"` in `orders.csv`.
   - When food is ready, the agent clicks "Start Transit", updating the status to `"Out for Delivery"`.
7. **Customer Tracking:**
   - In `/orders` and `/orders/<order_id>`, the customer watches the 4-step progress tracker update to "On Route".
8. **Delivery Completion:**
   - When the agent reaches the customer's address, the agent clicks "Complete Delivery" on `/delivery/dashboard`.
   - `orders.csv` updates status to `"Delivered"`, and the agent becomes available for new deliveries.
   - The order moves to the customer's "Order History" tab.

---

## 6. Where the Data is Stored (CSV Files Breakdown)

All application data is stored in plain CSV files located in the root directory:

1. **`user.csv`**:
   - `User_Id`: Unique numeric ID (e.g., `1000`).
   - `Name`: Customer full name.
   - `Phone_Number`: Contact number.
   - `Email`: Unique registered email address.
   - `Address`: Delivery street address.
   - `Password`: Cryptographic PBKDF2 salt and hash (`salt$hash`).
2. **`restaurant.csv`**:
   - `Restaurant_ID`: Unique restaurant code (e.g., `R101`).
   - `Restaurant_Name`: Name of the restaurant.
   - `Location`: Area/Neighborhood.
   - `Rating`: Decimal rating out of 5.0 (e.g., `4.8`).
   - `Food_Items`: Semicolon-delimited list of dishes formatted as `Food_ID:Food_Name:Category:Price:Availability` (e.g., `F101:Truffle Mushroom Bruschetta:Starters:280.0:True`).
3. **`orders.csv`**:
   - `Order_ID`: Unique order code (e.g., `ORD-1009`).
   - `User_Email`: Email of the customer who ordered.
   - `Restaurant_ID`: ID of the restaurant fulfilling the order.
   - `Ordered_Items`: Semicolon-delimited items formatted as `Food_ID:Food_Name:Price:Quantity`.
   - `Total_Amount`: Final bill amount including delivery and tax.
   - `Order_Status`: Current stage (`Preparing`, `Accepted`, `Out for Delivery`, `Delivered`, `Cancelled`).
   - `Order_Date`: Order date in `YYYY-MM-DD` format.
4. **`payments.csv`**:
   - `Payment_ID`: Unique transaction reference (e.g., `PAY-1009`).
   - `Order_ID`: Associated order identifier.
   - `Payment_Method`: `Cash on Delivery`, `UPI`, `Credit Card`, or `Debit Card`.
   - `Payment_Status`: `Paid` or `Pending` (for COD).
   - `Amount`: Total amount charged.

---

## 7. Which Features Work (Tested One by One)

| Feature | Tested? | Result / Observation |
| :--- | :--- | :--- |
| **Flask Server Startup (`python app.py`)** | Yes | **Working.** Server runs on `http://127.0.0.1:5000` with active debugger. |
| **Console Application (`python main.py`)** | Yes | **Working.** Complete interactive loop tested (Register, Cart, Order, Payment, Agent dispatch, Exit). |
| **Home Page Rendering (`/`)** | Yes | **Working.** Hero section, circular food image, 2x4 feature cards, and feedback cards render with HTTP 200. |
| **Customer Registration (`/register`)** | Yes | **Working.** Validates input, hashes password, saves to `user.csv`, logs user in. |
| **Customer Login & Logout (`/login`, `/logout`)** | Yes | **Working.** Validates credentials against hashed passwords; sets and clears session. |
| **Restaurant Browsing & Keyword Search (`/restaurants`)** | Yes | **Working.** Searches restaurants by name, location, and dish name/category. |
| **Star Rating Filter** | Yes | **Working.** Dropdown filters restaurants with rating >= 4.0, 4.5, or 4.8. |
| **Categorized Menu Display (`/restaurant/<id>`)** | Yes | **Working.** Groups items into Starters, Mains, Desserts, Beverages; shows availability badge. |
| **Add to Cart & Quantity Modifiers** | Yes | **Working.** Adds dishes to session cart; updates quantities (+ / -); prevents negative numbers. |
| **Cross-Restaurant Cart Warning** | Yes | **Working.** Prompts customer when attempting to add items from a second restaurant. |
| **Cart Subtotal, Delivery Fee & GST (`/cart`)** | Yes | **Working.** Accurately applies ₹40 delivery fee and 5% GST on subtotal. |
| **Checkout & Auto ID Generation (`/checkout`)** | Yes | **Working.** Generates `ORD-xxxx` and `PAY-xxxx` automatically; no user typing required. |
| **Payment Options (COD, UPI, Cards)** | Yes | **Working.** COD sets status to "Pending"; UPI and Cards validate input and record "Paid". |
| **Receipt Generation (`/receipt/<id>`)** | Yes | **Working.** Displays itemized receipt; "Print Receipt" triggers window.print(). |
| **Customer Order Tracking (`/orders`, `/orders/<id>`)** | Yes | **Working.** Displays Active vs History tabs; 4-step progress tracker displays correct step. |
| **Order Cancellation** | Yes | **Working.** Cancels order if in "Preparing" or "Accepted" state; blocks cancellation if Delivered. |
| **Customer Profile Update & Password Change** | Yes | **Working.** Updates name, phone, address; verifies current password before updating to new hash. |
| **Delivery Agent Login & Dashboard** | Yes | **Working.** Agent logs in with ID/vehicle; views available orders; accepts and marks delivered. |
| **Restaurant Manager Authentication (`/admin/login`)** | Yes | **Working.** Protected by `ADMIN_PASSWORD = admin123` from `.env`. No passwords shown on page. |
| **Manager: Add New Restaurant** | Yes | **Working.** Appends new restaurant row to `restaurant.csv`. |
| **Manager: Add Food Item to Restaurant** | Yes | **Working.** Appends new dish formatted with semicolons into `restaurant.csv`. |
| **Manager: 1-Click Availability Toggle** | Yes | **Working.** Instantly flips item between `True` (Available) and `False` (Out of Stock). |
| **Manager: Quick Price Update & Remove Dish** | Yes | **Working.** Updates price in-place; removes dish from `restaurant.csv`. |
| **Automated Test Suite (`test_suite.py`)** | Yes | **Working.** 7/7 unittest test cases pass in 0.66s; isolated sandbox guarantees real CSVs are untouched. |
| **Browser Subagent Automation via Playwright** | Attempted | **Not tested.** The internal Playwright browser engine returned a 404 on its CDN binary driver during automated subagent launch; all endpoints were verified via live HTTP requests instead. |

---

## 8. Anything That Looks Wrong or Unfinished

1. **Fixed Placeholder Copy:**
   - "Taly Feedback" was replaced with "Customer Feedback".
   - "High Rigin Pasta" was replaced with "Artisan Seafood Fettuccine".
   - Default configured password hint removed from `admin_login.html`.
2. **CSV Clean State:**
   - Development test rows from previous runs were cleared:
     - `user.csv` retains only real account: `1000, Munik Lalluvadiya, muniklalluvadiya@gmail.com`.
     - `orders.csv` retains real order: `ORD-1009`.
     - `payments.csv` retains real payment: `PAY-1009`.
     - `restaurant.csv` retains all 4 partner restaurants and their complete menus.
3. **Test Suite Isolation:**
   - `test_suite.py` now copies all CSV files into a temporary directory using `tempfile.TemporaryDirectory()`, executes in that sandbox, and deletes the temporary files upon completion, ensuring zero test data leaks into production files.
4. **Mobile Responsiveness Notes (around 375px width):**
   - The shopping cart table (`templates/cart.html`) on screens narrower than 400px can experience horizontal stretching. Adding an explicit overflow wrapper will give smoother touch scrolling.
   - The 4-step order progress timeline (`templates/order_detail.html`) uses horizontal step nodes (`width: 80px`), which become compressed on very small mobile displays (375px).
   - The hamburger navigation drawer opens smoothly, but could benefit from a dimmed backdrop overlay to close the menu when tapping outside.

---

## 9. Anything We Are Not Sure About

1. **Currency Symbol Representation:**
   - The original console codebase did not specify currency symbols (it simply output numbers like `Price : 280.0`). The web app uses the Indian Rupee symbol (`₹`), which matches the local address and phone numbers in the database. If your instructor prefers US Dollars (`$`), this can be changed in `config.py`.
2. **Delivery Agent Account Storage:**
   - In `main.py`, delivery agents simply type their name, vehicle, and phone on login without checking an `agents.csv` file. The web application replicates this exact console logic by keeping the active agent in session. If your teacher asks whether delivery agents have a dedicated CSV file, confirm that they are currently transient/session-based like the console design.
