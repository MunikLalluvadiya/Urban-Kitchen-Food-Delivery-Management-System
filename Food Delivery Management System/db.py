"""
Database module for Urban Kitchen - Supabase integration.
Centralizes all database operations for users, restaurants, food_items,
orders, order_items, and payments.
"""
import os
import csv
from datetime import date
from dotenv import load_dotenv

# Ensure .env is loaded from this project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

_client = None


def get_supabase():
    """Returns the singleton Supabase client or initializes it from .env."""
    global _client
    if _client is not None:
        return _client

    # Reload in case .env was recently created or updated
    load_dotenv(ENV_PATH, override=True)
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in your .env file."
        )

    from supabase import create_client
    _client = create_client(url, key)
    return _client


# ----------------------------------------------------------------------
# Users CRUD
# ----------------------------------------------------------------------
def db_get_all_user_rows():
    """Returns all users formatted as list of rows: [user_id, name, phone, email, address, password]."""
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("*").execute()
        rows = []
        for u in (res.data or []):
            rows.append([
                str(u.get("user_id", "")),
                str(u.get("name", "")),
                str(u.get("phone_number", "")),
                str(u.get("email", "")),
                str(u.get("address", "")),
                str(u.get("password", ""))
            ])
        return rows
    except Exception as e:
        print(f"[db] Error fetching users: {e}")
        return []


def db_get_user_by_email(email):
    """Returns user dict or None."""
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("*").eq("email", email.strip().lower()).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"[db] Error getting user by email: {e}")
        return None


def db_get_user_by_id(user_id):
    """Returns user dict or None."""
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("*").eq("user_id", str(user_id).strip()).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"[db] Error getting user by id: {e}")
        return None


def db_insert_user(user_id, name, phone, email, address, hashed_password):
    """Inserts a new user record into Supabase."""
    supabase = get_supabase()
    payload = {
        "user_id": str(user_id).strip(),
        "name": str(name).strip(),
        "phone_number": str(phone).strip(),
        "email": str(email).strip().lower(),
        "address": str(address).strip(),
        "password": str(hashed_password).strip()
    }
    supabase.table("users").insert(payload).execute()


def db_update_user_field(email, field_name, new_value):
    """Updates a single profile field for a user."""
    field_map = {
        "Name": "name",
        "Phone_Number": "phone_number",
        "Email": "email",
        "Address": "address"
    }
    col = field_map.get(field_name)
    if not col:
        return False
    val = new_value.strip().lower() if col == "email" else str(new_value).strip()
    supabase = get_supabase()
    supabase.table("users").update({col: val}).eq("email", email.strip().lower()).execute()
    return True


def db_update_user_password(email, new_hashed_password):
    """Updates the user password."""
    supabase = get_supabase()
    supabase.table("users").update({"password": str(new_hashed_password).strip()}).eq("email", email.strip().lower()).execute()
    return True


# ----------------------------------------------------------------------
# Restaurants & Food Items CRUD
# ----------------------------------------------------------------------
def db_get_all_restaurants_data():
    """
    Returns list of restaurant dictionaries with Food_Items populated
    matching the format expected by the app.
    """
    from FoodItem import FoodItem

    try:
        supabase = get_supabase()
        r_res = supabase.table("restaurants").select("*").execute()
        f_res = supabase.table("food_items").select("*").execute()

        food_map = {}
        for fi in (f_res.data or []):
            rid = str(fi.get("restaurant_id", "")).strip()
            item = FoodItem(
                str(fi.get("food_id", "")),
                str(fi.get("food_name", "")),
                str(fi.get("category", "")),
                float(fi.get("price") or 0.0),
                bool(fi.get("availability", True))
            )
            if rid not in food_map:
                food_map[rid] = []
            food_map[rid].append(item)

        restaurants = []
        for r in (r_res.data or []):
            rid = str(r.get("restaurant_id", "")).strip()
            items = food_map.get(rid, [])
            restaurants.append({
                "Restaurant_ID": rid,
                "Restaurant_Name": str(r.get("restaurant_name", "")),
                "Location": str(r.get("location", "")),
                "Rating": float(r.get("rating") or 0.0),
                "Food_Items": items,
                "Total_Items": len(items)
            })
        return restaurants
    except Exception as e:
        print(f"[db] Error getting all restaurants: {e}")
        return []


def db_get_restaurant_by_id(restaurant_id):
    """Returns basic tuple (name, location, rating) or None."""
    try:
        supabase = get_supabase()
        res = supabase.table("restaurants").select("*").eq("restaurant_id", str(restaurant_id).strip()).execute()
        if res.data:
            r = res.data[0]
            return str(r.get("restaurant_name", "")), str(r.get("location", "")), float(r.get("rating") or 0.0)
        return None
    except Exception as e:
        print(f"[db] Error getting restaurant by id: {e}")
        return None


def db_get_food_items_for_restaurant(restaurant_id):
    """Returns list of FoodItem objects for a restaurant."""
    from FoodItem import FoodItem

    try:
        supabase = get_supabase()
        res = supabase.table("food_items").select("*").eq("restaurant_id", str(restaurant_id).strip()).execute()
        items = []
        for fi in (res.data or []):
            items.append(FoodItem(
                str(fi.get("food_id", "")),
                str(fi.get("food_name", "")),
                str(fi.get("category", "")),
                float(fi.get("price") or 0.0),
                bool(fi.get("availability", True))
            ))
        return items
    except Exception as e:
        print(f"[db] Error getting food items: {e}")
        return []


def db_add_restaurant(restaurant_id, restaurant_name, location, rating):
    """Adds a new restaurant to Supabase."""
    supabase = get_supabase()
    payload = {
        "restaurant_id": str(restaurant_id).strip(),
        "restaurant_name": str(restaurant_name).strip(),
        "location": str(location).strip(),
        "rating": float(rating)
    }
    supabase.table("restaurants").insert(payload).execute()


def db_add_food_item(restaurant_id, food_id, food_name, category, price, availability=True):
    """Adds a food item to a restaurant."""
    supabase = get_supabase()
    payload = {
        "food_id": str(food_id).strip(),
        "restaurant_id": str(restaurant_id).strip(),
        "food_name": str(food_name).strip(),
        "category": str(category).strip(),
        "price": float(price),
        "availability": bool(availability)
    }
    supabase.table("food_items").insert(payload).execute()


def db_remove_food_item(restaurant_id, food_id):
    """Removes a food item from a restaurant."""
    supabase = get_supabase()
    supabase.table("food_items").delete().match({
        "restaurant_id": str(restaurant_id).strip(),
        "food_id": str(food_id).strip()
    }).execute()


def db_update_food_item(restaurant_id, food_id, updates):
    """Updates specified fields of a food item."""
    supabase = get_supabase()
    payload = {}
    if "new_price" in updates and updates["new_price"] is not None:
        payload["price"] = float(updates["new_price"])
    if "new_availability" in updates and updates["new_availability"] is not None:
        payload["availability"] = bool(updates["new_availability"])
    if "new_name" in updates and updates["new_name"] is not None:
        payload["food_name"] = str(updates["new_name"]).strip()
    if "new_category" in updates and updates["new_category"] is not None:
        payload["category"] = str(updates["new_category"]).strip()

    if payload:
        supabase.table("food_items").update(payload).match({
            "restaurant_id": str(restaurant_id).strip(),
            "food_id": str(food_id).strip()
        }).execute()


# ----------------------------------------------------------------------
# Orders & Order Items CRUD
# ----------------------------------------------------------------------
def db_get_all_orders():
    """Returns list of order dictionaries matching the format expected by the app."""
    try:
        supabase = get_supabase()
        orders_res = supabase.table("orders").select("*").order("order_id", desc=True).execute()
        items_res = supabase.table("order_items").select("*").execute()

        items_by_order = {}
        for it in (items_res.data or []):
            oid = str(it.get("order_id", "")).strip()
            p_val = float(it.get("price") or 0.0)
            q_val = int(it.get("quantity") or 1)
            item_entry = {
                "Food_ID": str(it.get("food_id", "")),
                "Food_Name": str(it.get("food_name", "")),
                "Price": p_val,
                "Quantity": q_val,
                "Subtotal": p_val * q_val
            }
            if oid not in items_by_order:
                items_by_order[oid] = []
            items_by_order[oid].append(item_entry)

        orders = []
        for o in (orders_res.data or []):
            oid = str(o.get("order_id", "")).strip()
            order_items = items_by_order.get(oid, [])

            # Format raw string for legacy compatibility
            raw_parts = [
                f"{item['Food_ID']}:{item['Food_Name']}:{item['Price']}:{item['Quantity']}"
                for item in order_items
            ]
            items_raw = ";".join(raw_parts)

            orders.append({
                "Order_ID": oid,
                "User_Email": str(o.get("user_email", "")),
                "Restaurant_ID": str(o.get("restaurant_id", "")),
                "Ordered_Items": order_items,
                "Items_Raw": items_raw,
                "Total_Amount": float(o.get("total_amount") or 0.0),
                "Order_Status": str(o.get("order_status", "Placed")),
                "Order_Date": str(o.get("order_date", ""))
            })
        return orders
    except Exception as e:
        print(f"[db] Error getting all orders: {e}")
        return []


def db_get_order_by_id(order_id):
    """Returns single order dict or None."""
    orders = db_get_all_orders()
    oid = str(order_id).strip()
    for o in orders:
        if o["Order_ID"] == oid:
            return o
    return None


def db_get_orders_by_user(user_email):
    """Returns list of orders for a user email."""
    all_orders = db_get_all_orders()
    clean_email = (user_email or "").strip().lower()
    return [o for o in all_orders if o["User_Email"].strip().lower() == clean_email]


def db_insert_order(order_id, user_email, restaurant_id, total_amount, order_status, order_date, ordered_items):
    """Inserts order and corresponding order_items."""
    supabase = get_supabase()
    order_payload = {
        "order_id": str(order_id).strip(),
        "user_email": str(user_email).strip().lower(),
        "restaurant_id": str(restaurant_id).strip() if restaurant_id else None,
        "total_amount": float(total_amount),
        "order_status": str(order_status).strip(),
        "order_date": str(order_date or date.today())
    }
    supabase.table("orders").insert(order_payload).execute()

    items_payload = []
    for entry in ordered_items:
        if isinstance(entry, dict):
            if "item" in entry:
                item = entry["item"]
                quantity = int(entry.get("quantity", 1))
                fid = getattr(item, "Food_ID", str(item))
                fname = getattr(item, "Food_Name", "")
                price = float(getattr(item, "Price", 0.0))
            else:
                fid = entry.get("Food_ID", "")
                fname = entry.get("Food_Name", "")
                price = float(entry.get("Price", 0.0))
                quantity = int(entry.get("Quantity", 1))
        else:
            fid = getattr(entry, "Food_ID", "")
            fname = getattr(entry, "Food_Name", "")
            price = float(getattr(entry, "Price", 0.0))
            quantity = int(getattr(entry, "Quantity", 1))

        items_payload.append({
            "order_id": str(order_id).strip(),
            "food_id": str(fid).strip(),
            "food_name": str(fname).strip(),
            "price": price,
            "quantity": quantity
        })

    if items_payload:
        supabase.table("order_items").insert(items_payload).execute()


def db_update_order_status(order_id, new_status):
    """Updates status for an order."""
    supabase = get_supabase()
    res = supabase.table("orders").update({"order_status": str(new_status).strip()}).eq("order_id", str(order_id).strip()).execute()
    return bool(res.data)


def db_generate_order_id():
    """Generates next Order ID like ORD-1010."""
    try:
        supabase = get_supabase()
        res = supabase.table("orders").select("order_id").execute()
        highest = 1000
        for row in (res.data or []):
            oid = str(row.get("order_id", ""))
            if oid.startswith("ORD-"):
                try:
                    num = int(oid.replace("ORD-", ""))
                    if num > highest:
                        highest = num
                except ValueError:
                    pass
        return f"ORD-{highest + 1}"
    except Exception:
        return "ORD-1001"


# ----------------------------------------------------------------------
# Payments CRUD
# ----------------------------------------------------------------------
def db_get_all_payments():
    """Returns all payments as list of dicts."""
    try:
        supabase = get_supabase()
        res = supabase.table("payments").select("*").execute()
        payments = []
        for p in (res.data or []):
            payments.append({
                "Payment_ID": str(p.get("payment_id", "")),
                "Order_ID": str(p.get("order_id", "")),
                "Payment_Method": str(p.get("payment_method", "")),
                "Payment_Status": str(p.get("payment_status", "")),
                "Amount": float(p.get("amount") or 0.0)
            })
        return payments
    except Exception as e:
        print(f"[db] Error getting payments: {e}")
        return []


def db_get_payment_by_order_id(order_id):
    """Returns payment dict for given order ID or None."""
    try:
        supabase = get_supabase()
        res = supabase.table("payments").select("*").eq("order_id", str(order_id).strip()).execute()
        if res.data:
            p = res.data[0]
            return {
                "Payment_ID": str(p.get("payment_id", "")),
                "Order_ID": str(p.get("order_id", "")),
                "Payment_Method": str(p.get("payment_method", "")),
                "Payment_Status": str(p.get("payment_status", "")),
                "Amount": float(p.get("amount") or 0.0)
            }
        return None
    except Exception as e:
        print(f"[db] Error getting payment by order id: {e}")
        return None


def db_get_payment_by_id(payment_id):
    """Returns payment dict for given payment ID or None."""
    try:
        supabase = get_supabase()
        res = supabase.table("payments").select("*").eq("payment_id", str(payment_id).strip()).execute()
        if res.data:
            p = res.data[0]
            return {
                "Payment_ID": str(p.get("payment_id", "")),
                "Order_ID": str(p.get("order_id", "")),
                "Payment_Method": str(p.get("payment_method", "")),
                "Payment_Status": str(p.get("payment_status", "")),
                "Amount": float(p.get("amount") or 0.0)
            }
        return None
    except Exception as e:
        print(f"[db] Error getting payment by id: {e}")
        return None


def db_insert_payment(payment_id, order_id, payment_method, payment_status, amount):
    """Inserts a payment record into Supabase."""
    supabase = get_supabase()
    payload = {
        "payment_id": str(payment_id).strip(),
        "order_id": str(order_id).strip(),
        "payment_method": str(payment_method).strip(),
        "payment_status": str(payment_status).strip(),
        "amount": float(amount)
    }
    supabase.table("payments").insert(payload).execute()


def db_generate_payment_id():
    """Generates next Payment ID like PAY-1010."""
    try:
        supabase = get_supabase()
        res = supabase.table("payments").select("payment_id").execute()
        highest = 1000
        for row in (res.data or []):
            pid = str(row.get("payment_id", ""))
            if pid.startswith("PAY-"):
                try:
                    num = int(pid.replace("PAY-", ""))
                    if num > highest:
                        highest = num
                except ValueError:
                    pass
        return f"PAY-{highest + 1}"
    except Exception:
        return "PAY-1001"


# ----------------------------------------------------------------------
# Migration: Copy existing CSV data into Supabase
# ----------------------------------------------------------------------
def migrate_csv_to_supabase():
    """Reads all existing CSV files and copies their records into Supabase tables."""
    supabase = get_supabase()
    summary = {}

    # 1. Users
    user_file = os.path.join(BASE_DIR, "user.csv")
    users_inserted = 0
    if os.path.exists(user_file):
        with open(user_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # header
            for row in reader:
                if len(row) >= 6 and row[0].strip():
                    supabase.table("users").upsert({
                        "user_id": str(row[0]).strip(),
                        "name": str(row[1]).strip(),
                        "phone_number": str(row[2]).strip(),
                        "email": str(row[3]).strip().lower(),
                        "address": str(row[4]).strip(),
                        "password": str(row[5]).strip()
                    }).execute()
                    users_inserted += 1
    summary["users"] = users_inserted

    # 2. Restaurants & Food Items
    rest_file = os.path.join(BASE_DIR, "restaurant.csv")
    rests_inserted = 0
    items_inserted = 0
    if os.path.exists(rest_file):
        with open(rest_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 4 and row[0].strip():
                    rid = str(row[0]).strip()
                    rname = str(row[1]).strip()
                    loc = str(row[2]).strip()
                    try:
                        rating = float(row[3])
                    except ValueError:
                        rating = 0.0

                    supabase.table("restaurants").upsert({
                        "restaurant_id": rid,
                        "restaurant_name": rname,
                        "location": loc,
                        "rating": rating
                    }).execute()
                    rests_inserted += 1

                    # Parse and upsert food items
                    if len(row) > 4 and row[4].strip():
                        for item_str in row[4].split(";"):
                            parts = item_str.split(":")
                            if len(parts) == 5:
                                fid, fname, cat, price, avail = parts
                                try:
                                    p_val = float(price)
                                except ValueError:
                                    p_val = 0.0
                                is_avail = avail.strip().lower() in ("true", "1", "yes")
                                supabase.table("food_items").upsert({
                                    "food_id": fid.strip(),
                                    "restaurant_id": rid,
                                    "food_name": fname.strip(),
                                    "category": cat.strip(),
                                    "price": p_val,
                                    "availability": is_avail
                                }).execute()
                                items_inserted += 1
    summary["restaurants"] = rests_inserted
    summary["food_items"] = items_inserted

    # 3. Orders & Order Items
    order_file = os.path.join(BASE_DIR, "orders.csv")
    orders_inserted = 0
    order_items_inserted = 0
    if os.path.exists(order_file):
        with open(order_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 7 and row[0].strip():
                    oid = str(row[0]).strip()
                    u_email = str(row[1]).strip().lower()
                    rid = str(row[2]).strip() if row[2].strip() else None
                    items_str = row[3].strip()
                    try:
                        tot = float(row[4])
                    except ValueError:
                        tot = 0.0
                    status = str(row[5]).strip()
                    o_date = str(row[6]).strip()

                    supabase.table("orders").upsert({
                        "order_id": oid,
                        "user_email": u_email,
                        "restaurant_id": rid,
                        "total_amount": tot,
                        "order_status": status,
                        "order_date": o_date
                    }).execute()
                    orders_inserted += 1

                    # Parse items: fid:fname:price:qty
                    if items_str:
                        # Clear old items for this order before inserting
                        supabase.table("order_items").delete().eq("order_id", oid).execute()
                        for entry in items_str.split(";"):
                            parts = entry.split(":")
                            if len(parts) >= 4:
                                fid, fname, price, qty = parts[0], parts[1], parts[2], parts[3]
                                try:
                                    p_val = float(price)
                                except ValueError:
                                    p_val = 0.0
                                try:
                                    q_val = int(qty)
                                except ValueError:
                                    q_val = 1
                                supabase.table("order_items").insert({
                                    "order_id": oid,
                                    "food_id": fid.strip(),
                                    "food_name": fname.strip(),
                                    "price": p_val,
                                    "quantity": q_val
                                }).execute()
                                order_items_inserted += 1
    summary["orders"] = orders_inserted
    summary["order_items"] = order_items_inserted

    # 4. Payments
    pay_file = os.path.join(BASE_DIR, "payments.csv")
    payments_inserted = 0
    if os.path.exists(pay_file):
        with open(pay_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 5 and row[0].strip():
                    pid = str(row[0]).strip()
                    oid = str(row[1]).strip()
                    method = str(row[2]).strip()
                    p_status = str(row[3]).strip()
                    try:
                        amt = float(row[4])
                    except ValueError:
                        amt = 0.0
                    supabase.table("payments").upsert({
                        "payment_id": pid,
                        "order_id": oid,
                        "payment_method": method,
                        "payment_status": p_status,
                        "amount": amt
                    }).execute()
                    payments_inserted += 1
    summary["payments"] = payments_inserted

    return summary


if __name__ == "__main__":
    print("Testing Supabase connection and running CSV migration...")
    res = migrate_csv_to_supabase()
    print("Migration summary:", res)
