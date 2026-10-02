import db

PAYMENTS_FILE = "payments.csv"
HEADER = ["Payment_ID", "Order_ID", "Payment_Method", "Payment_Status", "Amount"]


# ---------------------------------------------------------------
# Storage Helpers (Maintained for backward compatibility)
# ---------------------------------------------------------------
def ensure_payments_file():
    """Ensures Supabase connectivity / schema readiness."""
    pass


def _read_rows():
    """Returns rows in the legacy CSV format: [Payment_ID, Order_ID, Method, Status, Amount]."""
    payments = db.db_get_all_payments()
    rows = []
    for p in payments:
        rows.append([
            p.get("Payment_ID", ""),
            p.get("Order_ID", ""),
            p.get("Payment_Method", ""),
            p.get("Payment_Status", ""),
            str(p.get("Amount", 0.0))
        ])
    return rows


def _write_rows(rows):
    """Legacy helper maintained for backward compatibility."""
    pass


def generate_payment_id():
    """Auto-generates a unique Payment ID like PAY-1001."""
    return db.db_generate_payment_id()


def get_payment_by_order_id(order_id):
    """Returns payment dictionary for the given Order ID or None."""
    return db.db_get_payment_by_order_id(order_id)


def get_payment_by_id(payment_id):
    """Returns payment dictionary for the given Payment ID or None."""
    return db.db_get_payment_by_id(payment_id)


# ---------------------------------------------------------------
# Payment Base Class
# ---------------------------------------------------------------
class Payment:

    def __init__(self, Payment_ID, Order_ID, Payment_Method, Amount):
        self.Payment_ID = str(Payment_ID) if Payment_ID else generate_payment_id()
        self.Order_ID = str(Order_ID)
        self.Payment_Method = Payment_Method
        self.Payment_Status = "Pending"
        try:
            self.Amount = float(Amount)
        except (ValueError, TypeError):
            self.Amount = 0.0

    # ===========================================================
    # UI-FRIENDLY METHODS: return (success, message)
    # ===========================================================
    def process_payment(self):
        """Records payment in Supabase without console input/print."""
        self.Payment_Status = "Paid"
        db.db_insert_payment(
            self.Payment_ID,
            self.Order_ID,
            self.Payment_Method,
            self.Payment_Status,
            self.Amount
        )
        return True, f"Payment of {self.Amount} recorded as {self.Payment_Status} via {self.Payment_Method}."

    def get_receipt_data(self):
        return {
            "Payment_ID": self.Payment_ID,
            "Order_ID": self.Order_ID,
            "Payment_Method": self.Payment_Method,
            "Payment_Status": self.Payment_Status,
            "Amount": self.Amount
        }

    # ===========================================================
    # CONSOLE METHODS (Preserved for main.py compatibility)
    # ===========================================================
    def Make_Payment(self):
        self.process_payment()
        print(f" Payment of {self.Amount} recorded as {self.Payment_Status} via {self.Payment_Method}.")

    def Generate_Receipt(self):
        print(" ----- RECEIPT ----- ")
        print(f" Payment_ID : {self.Payment_ID}")
        print(f" Order_ID : {self.Order_ID}")
        print(f" Payment_Method : {self.Payment_Method}")
        print(f" Payment_Status : {self.Payment_Status}")
        print(f" Amount : {self.Amount}")
        print(" -------------------- ")

    def View_Payment_Details(self):
        details = get_payment_by_id(self.Payment_ID)
        if details:
            print(f"Payment_ID : {details['Payment_ID']} , Order_ID : {details['Order_ID']} , "
                  f"Payment_Method : {details['Payment_Method']} , Payment_Status : {details['Payment_Status']} , "
                  f"Amount : {details['Amount']}")
        else:
            print(" Payment Not Found.")


# ---------------------------------------------------------------
# Subclasses for Payment Methods
# ---------------------------------------------------------------
class CashOnDelivery(Payment):

    def __init__(self, Payment_ID, Order_ID, Amount):
        super().__init__(Payment_ID, Order_ID, "Cash on Delivery", Amount)
        self.Payment_Status = "Pending"

    def process_payment(self):
        self.Payment_Status = "Pending"
        db.db_insert_payment(
            self.Payment_ID,
            self.Order_ID,
            self.Payment_Method,
            self.Payment_Status,
            self.Amount
        )
        return True, "Cash on Delivery selected. Please keep exact change ready for the delivery agent."

    def Make_Payment(self):
        print(" Cash on Delivery selected. Please keep exact change ready for the delivery agent.")
        self.process_payment()


class UPIPayment(Payment):

    def __init__(self, Payment_ID, Order_ID, Amount):
        super().__init__(Payment_ID, Order_ID, "UPI", Amount)

    def process_payment(self, upi_id="customer@upi"):
        if not upi_id or "@" not in upi_id:
            return False, "Please provide a valid UPI ID (e.g. name@bank)."
        self.Payment_Status = "Paid"
        db.db_insert_payment(
            self.Payment_ID,
            self.Order_ID,
            self.Payment_Method,
            self.Payment_Status,
            self.Amount
        )
        return True, f"Payment of {self.Amount} recorded as {self.Payment_Status} via {self.Payment_Method}."

    def Make_Payment(self):
        upi_id = input(" Enter your UPI ID : ").strip()
        print(f" Processing UPI payment of {self.Amount} using {upi_id}...")
        self.process_payment(upi_id)
        print(f" Payment of {self.Amount} recorded as {self.Payment_Status} via {self.Payment_Method}.")


class CardPayment(Payment):

    def __init__(self, Payment_ID, Order_ID, Amount, card_type="Credit Card"):
        super().__init__(Payment_ID, Order_ID, card_type, Amount)

    def process_payment(self, card_number="0000", expiry="", cvv=""):
        cleaned_card = card_number.replace(" ", "").replace("-", "")
        if len(cleaned_card) < 12 or not cleaned_card.isdigit():
            return False, "Please enter a valid card number (12-19 digits)."
        self.Payment_Status = "Paid"
        db.db_insert_payment(
            self.Payment_ID,
            self.Order_ID,
            self.Payment_Method,
            self.Payment_Status,
            self.Amount
        )
        return True, f"Payment of {self.Amount} recorded as {self.Payment_Status} via {self.Payment_Method}."

    def Make_Payment(self):
        card_number = input(" Enter your Card Number : ").strip()
        last_four = card_number[-4:] if len(card_number) >= 4 else "0000"
        print(f" Processing {self.Payment_Method} payment of {self.Amount} using card ending in {last_four}...")
        self.process_payment(card_number)
        print(f" Payment of {self.Amount} recorded as {self.Payment_Status} via {self.Payment_Method}.")
