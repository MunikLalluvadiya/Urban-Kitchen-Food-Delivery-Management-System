import csv
import os
from order import update_status_by_order_id, get_all_orders, get_order_by_id

ORDERS_FILE = "orders.csv"


# ---------------------------------------------------------------
# Delivery Module Helpers
# ---------------------------------------------------------------
def get_available_deliveries():
    """Returns orders waiting for delivery assignment (Preparing or Accepted)."""
    all_orders = get_all_orders()
    return [o for o in all_orders if o["Order_Status"] in ("Preparing", "Accepted")]


def get_active_deliveries():
    """Returns orders that are currently in transit (Out for Delivery)."""
    all_orders = get_all_orders()
    return [o for o in all_orders if o["Order_Status"] == "Out for Delivery"]


def get_completed_deliveries():
    """Returns orders that have been successfully delivered."""
    all_orders = get_all_orders()
    return [o for o in all_orders if o["Order_Status"] == "Delivered"]


# ---------------------------------------------------------------
# DeliveryAgent Class
# ---------------------------------------------------------------
class DeliveryAgent:

    def __init__(self, Agent_ID, Name, Phone_Number, Vehicle_Number, Availability=True):
        self.Agent_ID = str(Agent_ID)
        self.Name = str(Name)
        self.Phone_Number = str(Phone_Number)
        self.Vehicle_Number = str(Vehicle_Number)
        self.Availability = Availability

    # ===========================================================
    # UI-FRIENDLY METHODS: take parameters, return (success, msg)
    # ===========================================================
    def accept_delivery(self, order_id):
        """Accepts an order delivery without console input."""
        oid = str(order_id).strip()
        order_info = get_order_by_id(oid)
        if not order_info:
            return False, f"Order {oid} not found."

        if order_info["Order_Status"] in ("Delivered", "Cancelled"):
            return False, f"Order {oid} is already {order_info['Order_Status'].lower()} and cannot be accepted."

        self.Availability = False
        ok, msg = update_status_by_order_id(oid, "Accepted")
        if ok:
            return True, f"Agent {self.Name} accepted Order {oid}. Status set to Accepted."
        return False, msg

    def update_delivery_status(self, order_id, new_status):
        """Updates the status of an order (e.g. Out for Delivery, Delivered)."""
        oid = str(order_id).strip()
        status_clean = str(new_status).strip()
        valid_statuses = ["Preparing", "Accepted", "Out for Delivery", "Delivered", "Cancelled"]

        if status_clean not in valid_statuses:
            return False, f"Invalid status. Choose from: {', '.join(valid_statuses)}"

        ok, msg = update_status_by_order_id(oid, status_clean)
        if ok and status_clean == "Delivered":
            self.Availability = True
        return ok, msg

    def complete_delivery(self, order_id):
        """Marks an order as Delivered and frees the agent."""
        oid = str(order_id).strip()
        order_info = get_order_by_id(oid)
        if not order_info:
            return False, f"Order {oid} not found."

        ok, msg = update_status_by_order_id(oid, "Delivered")
        if ok:
            self.Availability = True
            return True, f"Order {oid} marked as Delivered. Agent {self.Name} is now available."
        return False, msg

    def get_info(self):
        """Returns dict of agent profile."""
        return {
            "Agent_ID": self.Agent_ID,
            "Name": self.Name,
            "Phone_Number": self.Phone_Number,
            "Vehicle_Number": self.Vehicle_Number,
            "Availability": self.Availability
        }

    # ===========================================================
    # CONSOLE METHODS (Preserved for main.py compatibility)
    # ===========================================================
    def Accept_Delivery(self):
        order_id = input(" Enter Order ID to accept : ").strip()
        ok, msg = self.accept_delivery(order_id)
        print(" " + msg)

    def Update_Delivery_Status(self):
        order_id = input(" Enter Order ID : ").strip()
        new_status = input(" Enter New Status (e.g. Out for Delivery) : ").strip()
        ok, msg = self.update_delivery_status(order_id, new_status)
        print(" " + msg)

    def Complete_Delivery(self):
        order_id = input(" Enter Order ID to complete : ").strip()
        ok, msg = self.complete_delivery(order_id)
        print(" " + msg)
