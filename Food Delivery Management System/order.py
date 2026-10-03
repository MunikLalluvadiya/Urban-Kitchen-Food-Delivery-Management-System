from datetime import date
import db

HEADER = ["Order_ID", "User_Email", "Restaurant_ID", "Ordered_Items", "Total_Amount", "Order_Status", "Order_Date"]


# ---------------------------------------------------------------
# Storage & Parsing Helpers
# ---------------------------------------------------------------
def ensure_orders_file():
    """Ensures Supabase connectivity / schema readiness."""
    pass


def _read_rows():
    """Returns rows in the legacy CSV format: [id, email, rest_id, items_raw, total, status, date]."""
    orders = db.db_get_all_orders()
    rows = []
    for o in orders:
        rows.append([
            o.get("Order_ID", ""),
            o.get("User_Email", ""),
            o.get("Restaurant_ID", ""),
            o.get("Items_Raw", ""),
            str(o.get("Total_Amount", 0.0)),
            o.get("Order_Status", ""),
            o.get("Order_Date", "")
        ])
    return rows


def _write_rows(rows):
    """Legacy helper maintained for backward compatibility."""
    pass


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
    return db.db_generate_order_id()


# ---------------------------------------------------------------
# UI-Friendly Functions (Web App / API)
# ---------------------------------------------------------------
def get_all_orders():
    """Returns a list of all order dictionaries."""
    return db.db_get_all_orders()


def get_orders_by_user(user_email):
    """Returns list of orders for a specific user email."""
    return db.db_get_orders_by_user(user_email)


def get_order_by_id(order_id):
    """Returns order dictionary or None."""
    return db.db_get_order_by_id(order_id)


def update_status_by_order_id(order_id, new_status):
    """Updates order status directly in Supabase."""
    oid = str(order_id).strip()
    order = db.db_get_order_by_id(oid)
    if not order:
        return False, f"Order {order_id} not found."
    db.db_update_order_status(oid, new_status)
    return True, f"Order {order_id} status updated to {new_status}."


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
        """Saves order to Supabase without any print/input calls."""
        if not self.Order_ID:
            self.Order_ID = generate_order_id()

        user_email = getattr(self.User, "Email", str(self.User) if self.User else "")
        rest_id = getattr(self.Restaurant, "Restaurant_ID", str(self.Restaurant) if self.Restaurant else "")

        db.db_insert_order(
            self.Order_ID,
            user_email,
            rest_id,
            self.Total_Amount,
            self.Order_Status,
            self.Order_Date,
            self.Ordered_Items
        )
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
        db.db_update_order_status(self.Order_ID, "Cancelled")
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
