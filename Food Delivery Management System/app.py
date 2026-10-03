import functools
import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_from_directory

import config
from User import User, _read_rows as _read_user_rows
from restaurant import (
    Restaurant, get_all_restaurants, search_restaurants,
    get_restaurant_by_id, add_new_restaurant, ensure_restaurant_file
)
from FoodItem import FoodItem
from Cart import Cart
from order import (
    Order, generate_order_id, get_orders_by_user,
    get_order_by_id, get_all_orders, ensure_orders_file
)
from payment import (
    Payment, CashOnDelivery, UPIPayment, CardPayment,
    generate_payment_id, get_payment_by_order_id, ensure_payments_file
)
from delivery import (
    DeliveryAgent, get_available_deliveries,
    get_active_deliveries, get_completed_deliveries
)
from utils import calculate_bill

app = Flask(__name__, static_folder="public", static_url_path="")
app.secret_key = config.SECRET_KEY


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Fallback route ensuring backward-compatibility for /static/<filename> requests."""
    return send_from_directory("public", filename)


# ---------------------------------------------------------------
# Startup Checks: ensure all CSV files have headers
# ---------------------------------------------------------------
@app.before_request
def ensure_files():
    # Only run once or fast check
    if not hasattr(app, "_files_initialized"):
        ensure_restaurant_file()
        ensure_orders_file()
        ensure_payments_file()
        app._files_initialized = True


# ---------------------------------------------------------------
# Session & Auth Helpers
# ---------------------------------------------------------------
def get_current_user():
    """Returns the logged-in User object or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = User()
    profile = user.get_profile(user_id)
    if profile:
        user.User_Id = profile["User_Id"]
        user.Name = profile["Name"]
        user.Phone_Number = profile["Phone_Number"]
        user.Email = profile["Email"]
        user.Address = profile["Address"]
        return user
    return None


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth", next=request.url))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("is_admin"):
            flash("Manager access required. Please sign in with the admin password.", "warning")
            return redirect(url_for("admin_login"))
        return view(**kwargs)
    return wrapped_view


def agent_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("agent"):
            flash("Please sign in as a Delivery Agent to access this portal.", "info")
            return redirect(url_for("delivery_login"))
        return view(**kwargs)
    return wrapped_view


# ---------------------------------------------------------------
# Cart Helpers (Flask Session -> Cart Object -> Flask Session)
# ---------------------------------------------------------------
def get_cart_from_session():
    """Reconstructs a Cart object using the data stored in session."""
    cart = Cart()
    cart_data = session.get("cart", {})
    rest_id = cart_data.get("restaurant_id")
    items = cart_data.get("items", [])

    if rest_id and items:
        cart.Restaurant_ID = rest_id
        for entry in items:
            cart.add(rest_id, entry["food_id"], entry["quantity"])
    return cart


def save_cart_to_session(cart):
    """Saves the Cart object back to session."""
    session["cart"] = {
        "restaurant_id": cart.Restaurant_ID,
        "items": [
            {
                "food_id": entry["item"].Food_ID,
                "food_name": entry["item"].Food_Name,
                "price": entry["item"].Price,
                "quantity": entry["quantity"],
                "subtotal": entry["item"].Price * entry["quantity"]
            }
            for entry in cart.List_Of_SelectedItems
        ]
    }
    session.modified = True


# ---------------------------------------------------------------
# Context Processor (Globally available variables in templates)
# ---------------------------------------------------------------
@app.context_processor
def inject_global_context():
    cart_data = session.get("cart", {})
    cart_items = cart_data.get("items", [])
    cart_count = sum(it.get("quantity", 0) for it in cart_items)
    current_user = get_current_user()
    current_agent = session.get("agent")
    is_admin = session.get("is_admin", False)

    return {
        "config": config,
        "cart_count": cart_count,
        "current_user": current_user,
        "current_agent": current_agent,
        "is_admin": is_admin
    }


# ---------------------------------------------------------------
# ROUTES: Customer & Public Facing
# ---------------------------------------------------------------
@app.route("/")
def home():
    """Home page copying the style and sections of reference/theme.png."""
    featured_restaurants = get_all_restaurants()[:4]
    return render_template("index.html", featured_restaurants=featured_restaurants)


@app.route("/auth")
def auth():
    """Register and Login page with split layout and tab switcher."""
    if session.get("user_id"):
        return redirect(url_for("home"))
    mode = request.args.get("tab", "login")
    return render_template("auth.html", active_tab=mode)


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not email or not password:
        flash("Please enter both email and password.", "danger")
        return redirect(url_for("auth", tab="login"))

    user = User()
    ok, message = user.login_user(email, password)
    if ok:
        session["user_id"] = user.User_Id
        session["user_name"] = user.Name
        session["user_email"] = user.Email
        flash(f"Welcome back, {user.Name}!", "success")
        next_url = request.args.get("next") or request.form.get("next")
        return redirect(next_url or url_for("home"))
    else:
        flash(message, "danger")
        return redirect(url_for("auth", tab="login"))


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    password = request.form.get("password", "").strip()

    # Form Validation
    if not name or not email or not phone or not address or not password:
        flash("All registration fields are required.", "danger")
        return redirect(url_for("auth", tab="register"))

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Please enter a valid email address.", "danger")
        return redirect(url_for("auth", tab="register"))

    clean_phone = re.sub(r"[^\d]", "", phone)
    if len(clean_phone) < 7:
        flash("Please enter a valid phone number.", "danger")
        return redirect(url_for("auth", tab="register"))

    if len(password) < 6:
        flash("Password should be at least 6 characters long.", "danger")
        return redirect(url_for("auth", tab="register"))

    # Auto-generate next numeric User_Id
    existing_rows = _read_user_rows()
    highest_id = 100
    for r in existing_rows:
        if r and r[0].isdigit():
            val = int(r[0])
            if val > highest_id:
                highest_id = val
    new_user_id = highest_id + 1

    user = User()
    ok, message = user.register_user(new_user_id, name, int(clean_phone), email, address, password)
    if ok:
        session["user_id"] = str(new_user_id)
        session["user_name"] = name
        session["user_email"] = email
        flash(f"Account created successfully! Welcome to Urban Kitchen, {name}.", "success")
        return redirect(url_for("home"))
    else:
        flash(message, "danger")
        return redirect(url_for("auth", tab="register"))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    flash("You have been successfully logged out.", "success")
    return redirect(url_for("home"))


@app.route("/restaurants")
def restaurants():
    """Browse restaurants with keyword search and rating filter."""
    query = request.args.get("q", "").strip()
    min_rating = request.args.get("rating", "0").strip()
    try:
        min_rating_val = float(min_rating)
    except ValueError:
        min_rating_val = 0.0

    filtered_restaurants = search_restaurants(keyword=query, min_rating=min_rating_val)
    return render_template(
        "restaurants.html",
        restaurants=filtered_restaurants,
        query=query,
        min_rating=min_rating_val
    )


@app.route("/restaurant/<restaurant_id>")
def restaurant_menu(restaurant_id):
    """Displays a restaurant's menu grouped by category."""
    restaurant_obj = get_restaurant_by_id(restaurant_id)
    if not restaurant_obj:
        flash(f"Restaurant with ID '{restaurant_id}' was not found.", "danger")
        return redirect(url_for("restaurants"))

    menu_by_category = restaurant_obj.get_menu_by_category()
    categories = restaurant_obj.get_categories()
    cart = get_cart_from_session()

    return render_template(
        "menu.html",
        restaurant=restaurant_obj,
        menu_by_category=menu_by_category,
        categories=categories,
        current_cart_rest_id=cart.Restaurant_ID
    )


# ---------------------------------------------------------------
# Cart Routes
# ---------------------------------------------------------------
@app.route("/cart")
def view_cart():
    """Displays items in cart, quantity controls, and bill breakdown."""
    cart = get_cart_from_session()
    cart_rows = cart.rows()
    subtotal = cart.Calculate_Total()

    delivery_charge, gst_amount, grand_total = (0.0, 0.0, 0.0)
    restaurant_info = None

    if cart_rows and cart.Restaurant_ID:
        delivery_charge, gst_amount, grand_total = calculate_bill(subtotal)
        restaurant_info = get_restaurant_by_id(cart.Restaurant_ID)

    return render_template(
        "cart.html",
        cart_rows=cart_rows,
        subtotal=subtotal,
        delivery_charge=delivery_charge,
        gst_amount=gst_amount,
        grand_total=grand_total,
        restaurant=restaurant_info
    )


@app.route("/cart/add", methods=["POST"])
def cart_add():
    restaurant_id = request.form.get("restaurant_id", "").strip()
    food_id = request.form.get("food_id", "").strip()
    quantity_str = request.form.get("quantity", "1").strip()

    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            quantity = 1
    except ValueError:
        quantity = 1

    cart = get_cart_from_session()

    # Rule 6: Cart belongs to one restaurant
    if cart.List_Of_SelectedItems and cart.Restaurant_ID != restaurant_id:
        # Check if user passed switch_restaurant=true
        if request.form.get("force_switch") == "true":
            cart.clear()
        else:
            old_rest = get_restaurant_by_id(cart.Restaurant_ID)
            old_name = old_rest.Restaurant_Name if old_rest else "another restaurant"
            flash(
                f"Your cart contains items from '{old_name}'. Empty your cart before ordering from another restaurant.",
                "warning"
            )
            return redirect(url_for("restaurant_menu", restaurant_id=restaurant_id))

    ok, message = cart.add(restaurant_id, food_id, quantity)
    if ok:
        save_cart_to_session(cart)
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(request.referrer or url_for("view_cart"))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    food_id = request.form.get("food_id", "").strip()
    quantity_str = request.form.get("quantity", "1").strip()

    try:
        quantity = int(quantity_str)
    except ValueError:
        quantity = 1

    cart = get_cart_from_session()
    ok, message = cart.set_quantity(food_id, quantity)
    if ok:
        save_cart_to_session(cart)
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("view_cart"))


@app.route("/cart/remove/<food_id>", methods=["GET", "POST"])
def cart_remove(food_id):
    cart = get_cart_from_session()
    ok, message = cart.remove(food_id)
    if ok:
        save_cart_to_session(cart)
        flash("Item removed from cart.", "info")
    else:
        flash(message, "danger")

    return redirect(url_for("view_cart"))


@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    cart = get_cart_from_session()
    cart.clear()
    save_cart_to_session(cart)
    flash("Your cart has been emptied.", "info")
    return redirect(url_for("view_cart"))


# ---------------------------------------------------------------
# Checkout & Receipt Routes
# ---------------------------------------------------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = get_cart_from_session()
    if not cart.List_Of_SelectedItems:
        flash("Your cart is empty. Add some delicious items first!", "warning")
        return redirect(url_for("restaurants"))

    # Rule 6: Cart belongs to one restaurant. Use it at checkout instead of asking again.
    restaurant_obj = get_restaurant_by_id(cart.Restaurant_ID)
    if not restaurant_obj:
        flash("The restaurant for this cart could not be located.", "danger")
        return redirect(url_for("view_cart"))

    user = get_current_user()
    subtotal = cart.Calculate_Total()
    delivery_charge, gst_amount, grand_total = calculate_bill(subtotal)

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "").strip()
        delivery_address = request.form.get("delivery_address", "").strip() or user.Address

        # Auto-generate IDs (Rule 4: Auto-generate Order IDs and Payment IDs)
        order_id = generate_order_id()
        payment_id = generate_payment_id()

        # Create Order
        new_order = Order(order_id, user, restaurant_obj, cart.List_Of_SelectedItems, grand_total)
        ok_order, msg_order = new_order.place_order()

        if not ok_order:
            flash(f"Could not place order: {msg_order}", "danger")
            return redirect(url_for("checkout"))

        # Process Payment based on method selected
        if payment_method == "Cash on Delivery":
            payment_obj = CashOnDelivery(payment_id, order_id, grand_total)
            ok_pay, msg_pay = payment_obj.process_payment()

        elif payment_method == "UPI":
            upi_id = request.form.get("upi_id", "").strip()
            if not upi_id:
                upi_id = f"{user.Email.split('@')[0]}@okhdfc"
            payment_obj = UPIPayment(payment_id, order_id, grand_total)
            ok_pay, msg_pay = payment_obj.process_payment(upi_id=upi_id)

        elif payment_method == "Credit Card":
            card_number = request.form.get("card_number", "").strip()
            payment_obj = CardPayment(payment_id, order_id, grand_total, "Credit Card")
            ok_pay, msg_pay = payment_obj.process_payment(card_number=card_number)

        elif payment_method == "Debit Card":
            card_number = request.form.get("card_number", "").strip()
            payment_obj = CardPayment(payment_id, order_id, grand_total, "Debit Card")
            ok_pay, msg_pay = payment_obj.process_payment(card_number=card_number)

        else:
            flash("Please choose a valid payment method.", "danger")
            return redirect(url_for("checkout"))

        if not ok_pay:
            flash(f"Payment issue: {msg_pay}", "warning")

        # Empty Cart
        cart.clear()
        save_cart_to_session(cart)

        flash("Order placed successfully! Thank you for ordering with Urban Kitchen.", "success")
        return redirect(url_for("receipt", order_id=order_id))

    return render_template(
        "checkout.html",
        cart_rows=cart.rows(),
        subtotal=subtotal,
        delivery_charge=delivery_charge,
        gst_amount=gst_amount,
        grand_total=grand_total,
        restaurant=restaurant_obj,
        user=user
    )


@app.route("/receipt/<order_id>")
@login_required
def receipt(order_id):
    """Shows receipt details for an order."""
    order_info = get_order_by_id(order_id)
    if not order_info:
        flash("Order receipt not found.", "danger")
        return redirect(url_for("orders"))

    payment_info = get_payment_by_order_id(order_id)
    restaurant_obj = get_restaurant_by_id(order_info["Restaurant_ID"])

    # Calculate itemized bill
    items_subtotal = sum(it["Subtotal"] for it in order_info["Ordered_Items"])
    delivery_charge, gst_amount, grand_total = calculate_bill(items_subtotal)

    return render_template(
        "receipt.html",
        order=order_info,
        payment=payment_info,
        restaurant=restaurant_obj,
        items_subtotal=items_subtotal,
        delivery_charge=delivery_charge,
        gst_amount=gst_amount,
        grand_total=grand_total
    )


# ---------------------------------------------------------------
# Customer Orders & Order Details
# ---------------------------------------------------------------
@app.route("/orders")
@login_required
def orders():
    """Customer orders page with Active and History tabs."""
    user = get_current_user()
    user_orders = get_orders_by_user(user.Email)

    active_orders = []
    history_orders = []

    # Map restaurant names for convenience
    all_rests = {r["Restaurant_ID"]: r["Restaurant_Name"] for r in get_all_restaurants()}

    for ord_dict in reversed(user_orders):
        ord_dict["Restaurant_Name"] = all_rests.get(ord_dict["Restaurant_ID"], f"Restaurant #{ord_dict['Restaurant_ID']}")
        if ord_dict["Order_Status"] in ("Preparing", "Accepted", "Out for Delivery"):
            active_orders.append(ord_dict)
        else:
            history_orders.append(ord_dict)

    active_tab = request.args.get("tab", "active")
    return render_template(
        "orders.html",
        active_orders=active_orders,
        history_orders=history_orders,
        active_tab=active_tab
    )


@app.route("/orders/<order_id>")
@login_required
def order_detail(order_id):
    """Detailed order view with status progression and payment info."""
    user = get_current_user()
    order_info = get_order_by_id(order_id)
    if not order_info:
        flash("Order not found.", "danger")
        return redirect(url_for("orders"))

    # Security check: order must belong to user or user is admin
    if order_info["User_Email"].strip().lower() != user.Email.strip().lower() and not session.get("is_admin"):
        flash("You are not authorized to view this order.", "danger")
        return redirect(url_for("orders"))

    restaurant_obj = get_restaurant_by_id(order_info["Restaurant_ID"])
    payment_info = get_payment_by_order_id(order_id)

    # Timeline status active step
    status_order = ["Preparing", "Accepted", "Out for Delivery", "Delivered"]
    current_status = order_info["Order_Status"]
    step_index = 0
    if current_status in status_order:
        step_index = status_order.index(current_status) + 1

    return render_template(
        "order_detail.html",
        order=order_info,
        restaurant=restaurant_obj,
        payment=payment_info,
        step_index=step_index
    )


@app.route("/orders/<order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    """Cancels an order if eligible."""
    user = get_current_user()
    order_info = get_order_by_id(order_id)
    if not order_info:
        flash("Order not found.", "danger")
        return redirect(url_for("orders"))

    if order_info["User_Email"].strip().lower() != user.Email.strip().lower():
        flash("You are not authorized to cancel this order.", "danger")
        return redirect(url_for("orders"))

    order_obj = Order(order_id, user, None, [], order_info["Total_Amount"], Order_Status=order_info["Order_Status"])
    ok, message = order_obj.cancel_order()
    if ok:
        flash(message, "success")
    else:
        flash(message, "warning")

    return redirect(url_for("order_detail", order_id=order_id))


# ---------------------------------------------------------------
# Customer Profile
# ---------------------------------------------------------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """View and update profile information (no password shown)."""
    user = get_current_user()

    if request.method == "POST":
        new_name = request.form.get("name", "").strip()
        new_phone = request.form.get("phone", "").strip()
        new_address = request.form.get("address", "").strip()

        if not new_name or not new_phone or not new_address:
            flash("All profile fields are required.", "danger")
            return redirect(url_for("profile"))

        # Update in user.csv using User helpers
        user_rows = _read_user_rows()
        updated = False
        for row in user_rows:
            if row[0] == str(user.User_Id):
                row[1] = new_name
                row[2] = new_phone
                row[4] = new_address
                updated = True
                break

        if updated:
            from User import _write_rows as _write_user_rows
            _write_user_rows(user_rows)
            session["user_name"] = new_name
            flash("Profile details updated successfully!", "success")
        else:
            flash("Unable to update profile.", "danger")

        return redirect(url_for("profile"))

    profile_dict = user.get_profile(user.User_Id)
    return render_template("profile.html", profile=profile_dict)


@app.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    user = get_current_user()
    current_password = request.form.get("current_password", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if not current_password or not new_password or not confirm_password:
        flash("Please fill in all password fields.", "danger")
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("profile"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "danger")
        return redirect(url_for("profile"))

    ok, message = user.set_password(user.Email, current_password, new_password)
    if ok:
        flash("Password changed successfully!", "success")
    else:
        flash(message, "danger")

    return redirect(url_for("profile"))


# ---------------------------------------------------------------
# Delivery Agent Portal
# ---------------------------------------------------------------
@app.route("/delivery/login", methods=["GET", "POST"])
def delivery_login():
    """Separate login page for Delivery Agents."""
    if session.get("agent"):
        return redirect(url_for("delivery_dashboard"))

    if request.method == "POST":
        agent_id = request.form.get("agent_id", "").strip()
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        vehicle = request.form.get("vehicle", "").strip()

        if not agent_id or not name or not phone or not vehicle:
            flash("All agent credentials are required.", "danger")
            return redirect(url_for("delivery_login"))

        session["agent"] = {
            "Agent_ID": agent_id,
            "Name": name,
            "Phone_Number": phone,
            "Vehicle_Number": vehicle,
            "Availability": True
        }
        flash(f"Welcome, Delivery Partner {name}!", "success")
        return redirect(url_for("delivery_dashboard"))

    return render_template("delivery_login.html")


@app.route("/delivery/dashboard")
@agent_required
def delivery_dashboard():
    """Agent dashboard showing agent details, available and active deliveries."""
    agent_info = session.get("agent")
    available_orders = get_available_deliveries()
    active_orders = get_active_deliveries()
    completed_orders = get_completed_deliveries()

    all_rests = {r["Restaurant_ID"]: r for r in get_all_restaurants()}

    for o in available_orders:
        o["Restaurant"] = all_rests.get(o["Restaurant_ID"])
    for o in active_orders:
        o["Restaurant"] = all_rests.get(o["Restaurant_ID"])
    for o in completed_orders:
        o["Restaurant"] = all_rests.get(o["Restaurant_ID"])

    return render_template(
        "delivery_dashboard.html",
        agent=agent_info,
        available_orders=available_orders,
        active_orders=active_orders,
        completed_orders=completed_orders
    )


@app.route("/delivery/accept/<order_id>", methods=["POST"])
@agent_required
def delivery_accept(order_id):
    agent_data = session.get("agent")
    agent = DeliveryAgent(
        agent_data["Agent_ID"],
        agent_data["Name"],
        agent_data["Phone_Number"],
        agent_data["Vehicle_Number"]
    )
    ok, message = agent.accept_delivery(order_id)
    if ok:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("delivery_dashboard"))


@app.route("/delivery/status/<order_id>", methods=["POST"])
@agent_required
def delivery_update_status(order_id):
    new_status = request.form.get("status", "").strip()
    agent_data = session.get("agent")
    agent = DeliveryAgent(
        agent_data["Agent_ID"],
        agent_data["Name"],
        agent_data["Phone_Number"],
        agent_data["Vehicle_Number"]
    )
    ok, message = agent.update_delivery_status(order_id, new_status)
    if ok:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("delivery_dashboard"))


@app.route("/delivery/complete/<order_id>", methods=["POST"])
@agent_required
def delivery_complete(order_id):
    agent_data = session.get("agent")
    agent = DeliveryAgent(
        agent_data["Agent_ID"],
        agent_data["Name"],
        agent_data["Phone_Number"],
        agent_data["Vehicle_Number"]
    )
    ok, message = agent.complete_delivery(order_id)
    if ok:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("delivery_dashboard"))


@app.route("/delivery/logout")
def delivery_logout():
    session.pop("agent", None)
    flash("Delivery agent logged out successfully.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------------
# Restaurant Manager Portal (Protected by ADMIN_PASSWORD)
# ---------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Login for Restaurant Manager / Admin."""
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        entered_password = request.form.get("admin_password", "").strip()
        if entered_password == config.ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Welcome, Restaurant Operations Manager!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Incorrect admin password. Please try again.", "danger")
            return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Restaurant Manager dashboard with menu management and restaurant additions."""
    restaurants_list = get_all_restaurants()
    all_orders = get_all_orders()

    total_revenue = sum(o["Total_Amount"] for o in all_orders if o["Order_Status"] != "Cancelled")
    total_items = sum(len(r["Food_Items"]) for r in restaurants_list)

    selected_rest_id = request.args.get("restaurant_id")
    selected_restaurant = None
    if selected_rest_id:
        selected_restaurant = get_restaurant_by_id(selected_rest_id)
    elif restaurants_list:
        selected_restaurant = get_restaurant_by_id(restaurants_list[0]["Restaurant_ID"])

    return render_template(
        "admin_dashboard.html",
        restaurants=restaurants_list,
        selected_restaurant=selected_restaurant,
        total_orders=len(all_orders),
        total_revenue=total_revenue,
        total_items=total_items
    )


@app.route("/admin/restaurant/add", methods=["POST"])
@admin_required
def admin_add_restaurant():
    rest_id = request.form.get("restaurant_id", "").strip()
    name = request.form.get("restaurant_name", "").strip()
    location = request.form.get("location", "").strip()
    rating = request.form.get("rating", "4.5").strip()

    ok, message = add_new_restaurant(rest_id, name, location, rating)
    if ok:
        flash(message, "success")
        return redirect(url_for("admin_dashboard", restaurant_id=rest_id))
    else:
        flash(message, "danger")
        return redirect(url_for("admin_dashboard"))


@app.route("/admin/menu/add", methods=["POST"])
@admin_required
def admin_add_food_item():
    restaurant_id = request.form.get("restaurant_id", "").strip()
    food_id = request.form.get("food_id", "").strip()
    food_name = request.form.get("food_name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "0").strip()
    availability = request.form.get("availability") == "true"

    restaurant_obj = get_restaurant_by_id(restaurant_id)
    if not restaurant_obj:
        flash("Restaurant not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    ok, message = restaurant_obj.add_food_item(food_id, food_name, category, price, availability)
    if ok:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("admin_dashboard", restaurant_id=restaurant_id))


@app.route("/admin/menu/update", methods=["POST"])
@admin_required
def admin_update_food_item():
    restaurant_id = request.form.get("restaurant_id", "").strip()
    food_id = request.form.get("food_id", "").strip()
    food_name = request.form.get("food_name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "").strip()

    restaurant_obj = get_restaurant_by_id(restaurant_id)
    if not restaurant_obj:
        flash("Restaurant not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    ok, message = restaurant_obj.update_food_item(
        food_id,
        new_price=price if price else None,
        new_name=food_name if food_name else None,
        new_category=category if category else None
    )
    if ok:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("admin_dashboard", restaurant_id=restaurant_id))


@app.route("/admin/menu/toggle-availability", methods=["POST"])
@admin_required
def admin_toggle_availability():
    restaurant_id = request.form.get("restaurant_id", "").strip()
    food_id = request.form.get("food_id", "").strip()
    current_status = request.form.get("current_status") == "True"

    restaurant_obj = get_restaurant_by_id(restaurant_id)
    if not restaurant_obj:
        flash("Restaurant not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    new_status = not current_status
    ok, message = restaurant_obj.update_food_item(food_id, new_availability=new_status)
    if ok:
        status_text = "Available" if new_status else "Out of Stock"
        flash(f"Item availability updated to {status_text}.", "info")
    else:
        flash(message, "danger")

    return redirect(url_for("admin_dashboard", restaurant_id=restaurant_id))


@app.route("/admin/menu/remove", methods=["POST"])
@admin_required
def admin_remove_food_item():
    restaurant_id = request.form.get("restaurant_id", "").strip()
    food_id = request.form.get("food_id", "").strip()

    restaurant_obj = get_restaurant_by_id(restaurant_id)
    if not restaurant_obj:
        flash("Restaurant not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    ok, message = restaurant_obj.remove_food_item(food_id)
    if ok:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("admin_dashboard", restaurant_id=restaurant_id))


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Admin logged out successfully.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
