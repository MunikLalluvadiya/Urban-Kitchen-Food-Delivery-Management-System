import csv
import os
from datetime import date

ORDERS_FILE = "orders.csv"
HEADER = ["Order_ID", "User_Email", "Restaurant_ID", "Ordered_Items", "Total_Amount", "Order_Status", "Order_Date"]


# ---------------------------------------------------------------
# Storage & Parsing Helpers
# ---------------------------------------------------------------
def ensure_orders_file():
    """Ensures orders.csv exists with header."""
    if not os.path.exists(ORDERS_FILE) or os.stat(ORDERS_FILE).st_size == 0:
        with open(ORDERS_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(HEADER)


def _read_rows():
    ensure_orders_file()
    try:
        with open(ORDERS_FILE, "r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)  # skip header
            return [row for row in reader if row]
    except FileNotFoundError:
        return []


def _write_rows(rows):
    with open(ORDERS_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(HEADER)
        writer.writerows(rows)


def parse_ordered_items(items_str):
    """Parses 'fid:fname:price:qty;...' into a list of item dictionaries."""
    items = []
    if not items_str:
        return items
    for entry in items_str.split(";"):
        if not entry.strip():
            continue
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
            items.append({
                "Food_ID": fid,
                "Food_Name": fname,
                "Price": p_val,
                "Quantity": q_val,
                "Subtotal": p_val * q_val
            })
    return items


def serialize_ordered_items(ordered_items):
    """Serializes cart items or item dicts to 'fid:fname:price:qty;...' string."""
    parts = []
    for entry in ordered_items:
        if isinstance(entry, dict):
            if "item" in entry:
                item = entry["item"]
                quantity = entry.get("quantity", 1)
                fid = getattr(item, "Food_ID", str(item))
                fname = getattr(item, "Food_Name", "")
                price = getattr(item, "Price", 0.0)
            else:
                fid = entry.get("Food_ID", "")
                fname = entry.get("Food_Name", "")
                price = entry.get("Price", 0.0)
                quantity = entry.get("Quantity", 1)
        else:
            fid = getattr(entry, "Food_ID", "")
            fname = getattr(entry, "Food_Name", "")
            price = getattr(entry, "Price", 0.0)
            quantity = getattr(entry, "Quantity", 1)
        parts.append(f"{fid}:{fname}:{price}:{quantity}")
    return ";".join(parts)


def generate_order_id():
    """Auto-generates a unique Order ID like ORD-1001."""
    rows = _read_rows()
    highest = 1000
    for row in rows:
        if row and row[0].startswith("ORD-"):
            try:
                num = int(row[0].replace("ORD-", ""))
                if num > highest:
                    highest = num
            except ValueError:
                pass
    return f"ORD-{highest + 1}"


# ---------------------------------------------------------------
# UI-Friendly Functions (Web App / API)
# ---------------------------------------------------------------
def get_all_orders():
    """Returns a list of all order dictionaries."""
    rows = _read_rows()
    orders = []
    for row in rows:
        if len(row) < 7:
            continue
        try:
            total_amt = float(row[4])
        except ValueError:
            total_amt = 0.0

        orders.append({
            "Order_ID": row[0],
            "User_Email": row[1],
            "Restaurant_ID": row[2],
            "Ordered_Items": parse_ordered_items(row[3]),
            "Items_Raw": row[3],
            "Total_Amount": total_amt,
            "Order_Status": row[5],
            "Order_Date": row[6]
        })
    return orders


def get_orders_by_user(user_email):
    """Returns list of orders for a specific user email."""
    all_orders = get_all_orders()
    email_clean = (user_email or "").strip().lower()
    return [o for o in all_orders if o["User_Email"].strip().lower() == email_clean]


def get_order_by_id(order_id):
    """Returns order dictionary or None."""
    all_orders = get_all_orders()
    oid = str(order_id).strip()
    for o in all_orders:
        if o["Order_ID"] == oid:
            return o
    return None


def update_status_by_order_id(order_id, new_status):
    """Updates order status directly in orders.csv."""
    rows = _read_rows()
    found = False
    oid = str(order_id).strip()
    for row in rows:
        if row and row[0] == oid:
            row[5] = new_status
            found = True
            break
    if found:
        _write_rows(rows)
        return True, f"Order {order_id} status updated to {new_status}."
    return False, f"Order {order_id} not found."


# ---------------------------------------------------------------
# Order Class
# ---------------------------------------------------------------
class Order:

    def __init__(self, Order_ID, User, Restaurant, Ordered_Items, Total_Amount, Order_Status="Preparing", Order_Date=None):
        self.Order_ID = str(Order_ID)
        self.User = User
        self.Restaurant = Restaurant
        self.Ordered_Items = Ordered_Items
        try:
            self.Total_Amount = float(Total_Amount)
        except (ValueError, TypeError):
            self.Total_Amount = 0.0
        self.Order_Status = Order_Status or "Preparing"
        self.Order_Date = Order_Date or str(date.today())

    # ===========================================================
    # UI-FRIENDLY METHODS: return (success, message)
    # ===========================================================
    def place_order(self):
        """Saves order to orders.csv without any print/input calls."""
        if not self.Order_ID:
            self.Order_ID = generate_order_id()

        user_email = getattr(self.User, "Email", str(self.User) if self.User else "")
        rest_id = getattr(self.Restaurant, "Restaurant_ID", str(self.Restaurant) if self.Restaurant else "")
        items_str = serialize_ordered_items(self.Ordered_Items)

        rows = _read_rows()
        row = [self.Order_ID, user_email, rest_id, items_str,
               str(self.Total_Amount), self.Order_Status, self.Order_Date]
        rows.append(row)
        _write_rows(rows)
        return True, f"Order {self.Order_ID} placed successfully. Status: {self.Order_Status}"

    def cancel_order(self):
        """Cancels order if eligible; returns (success, message)."""
        current = get_order_by_id(self.Order_ID)
        if current:
            status = current["Order_Status"]
        else:
            status = self.Order_Status

        if status == "Cancelled":
            return False, f"Order {self.Order_ID} is already cancelled."
        if status == "Delivered":
            return False, f"Cannot cancel Order {self.Order_ID} as it has already been delivered."
        if status == "Out for Delivery":
            return False, f"Cannot cancel Order {self.Order_ID} because it is already out for delivery."

        self.Order_Status = "Cancelled"
        rows = _read_rows()
        for row in rows:
            if row and row[0] == self.Order_ID:
                row[5] = "Cancelled"
                break
        _write_rows(rows)
        return True, f"Order {self.Order_ID} has been cancelled."

    def update_order_status(self, new_status):
        """Updates status of this order to new_status."""
        self.Order_Status = new_status
        ok, msg = update_status_by_order_id(self.Order_ID, new_status)
        return ok, msg

    def get_details(self):
        """Returns details dict of this order."""
        return get_order_by_id(self.Order_ID)

    # ===========================================================
    # CONSOLE METHODS (Preserved for main.py compatibility)
    # ===========================================================
    def Place_Order(self):
        ok, msg = self.place_order()
        print(f" Order {self.Order_ID} placed successfully. Status: {self.Order_Status}")

    def Cancel_Order(self):
        ok, msg = self.cancel_order()
        print(" " + msg)

    def View_Order(self):
        order_info = get_order_by_id(self.Order_ID)
        if not order_info:
            print(" Order Not Found.")
            return
        print(f"Order_ID : {order_info['Order_ID']}")
        print(f"User_Email : {order_info['User_Email']}")
        print(f"Restaurant_ID : {order_info['Restaurant_ID']}")
        print(f"Ordered_Items : {order_info['Items_Raw']}")
        print(f"Total_Amount : {order_info['Total_Amount']}")
        print(f"Order_Status : {order_info['Order_Status']}")
        print(f"Order_Date : {order_info['Order_Date']}")

    def Order_History(self):
        user_email = getattr(self.User, "Email", "")
        orders = get_orders_by_user(user_email)
        if not orders:
            print(" No previous orders found.")
            return
        for o in orders:
            print(f"Order_ID : {o['Order_ID']} , Restaurant_ID : {o['Restaurant_ID']} , "
                  f"Total_Amount : {o['Total_Amount']} , Status : {o['Order_Status']} , Date : {o['Order_Date']}")

    def Update_Status(self):
        print(" Status options: Preparing / Accepted / Out for Delivery / Delivered / Cancelled")
        new_status = input(" Enter New Status : ").strip()
        ok, msg = self.update_order_status(new_status)
        print(" " + msg)
