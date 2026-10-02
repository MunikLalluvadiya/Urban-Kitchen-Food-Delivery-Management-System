import csv
import os

PAYMENTS_FILE = "payments.csv"
HEADER = ["Payment_ID", "Order_ID", "Payment_Method", "Payment_Status", "Amount"]


# ---------------------------------------------------------------
# Storage Helpers
# ---------------------------------------------------------------
def ensure_payments_file():
    """Ensures payments.csv exists with header."""
    if not os.path.exists(PAYMENTS_FILE) or os.stat(PAYMENTS_FILE).st_size == 0:
        with open(PAYMENTS_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(HEADER)


def _read_rows():
    ensure_payments_file()
    try:
        with open(PAYMENTS_FILE, "r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)  # skip header
            return [row for row in reader if row]
    except FileNotFoundError:
        return []


def _write_rows(rows):
    with open(PAYMENTS_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(HEADER)
        writer.writerows(rows)


def generate_payment_id():
    """Auto-generates a unique Payment ID like PAY-1001."""
    rows = _read_rows()
    highest = 1000
    for row in rows:
        if row and row[0].startswith("PAY-"):
            try:
                num = int(row[0].replace("PAY-", ""))
                if num > highest:
                    highest = num
            except ValueError:
                pass
    return f"PAY-{highest + 1}"


def get_payment_by_order_id(order_id):
    """Returns payment dictionary for the given Order ID or None."""
    rows = _read_rows()
    oid = str(order_id).strip()
    for row in rows:
        if row and row[1] == oid:
            try:
                amt = float(row[4])
            except ValueError:
                amt = 0.0
            return {
                "Payment_ID": row[0],
                "Order_ID": row[1],
                "Payment_Method": row[2],
                "Payment_Status": row[3],
                "Amount": amt
            }
    return None


def get_payment_by_id(payment_id):
    """Returns payment dictionary for the given Payment ID or None."""
    rows = _read_rows()
    pid = str(payment_id).strip()
    for row in rows:
        if row and row[0] == pid:
            try:
                amt = float(row[4])
            except ValueError:
                amt = 0.0
            return {
                "Payment_ID": row[0],
                "Order_ID": row[1],
                "Payment_Method": row[2],
                "Payment_Status": row[3],
                "Amount": amt
            }
    return None


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
        """Records payment in payments.csv without console input/print."""
        self.Payment_Status = "Paid"
        row = [self.Payment_ID, self.Order_ID, self.Payment_Method, self.Payment_Status, str(self.Amount)]
        rows = _read_rows()
        rows.append(row)
        _write_rows(rows)
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
        row = [self.Payment_ID, self.Order_ID, self.Payment_Method, self.Payment_Status, str(self.Amount)]
        rows = _read_rows()
        rows.append(row)
        _write_rows(rows)
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
        row = [self.Payment_ID, self.Order_ID, self.Payment_Method, self.Payment_Status, str(self.Amount)]
        rows = _read_rows()
        rows.append(row)
        _write_rows(rows)
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
        row = [self.Payment_ID, self.Order_ID, self.Payment_Method, self.Payment_Status, str(self.Amount)]
        rows = _read_rows()
        rows.append(row)
        _write_rows(rows)
        return True, f"Payment of {self.Amount} recorded as {self.Payment_Status} via {self.Payment_Method}."

    def Make_Payment(self):
        card_number = input(" Enter your Card Number : ").strip()
        last_four = card_number[-4:] if len(card_number) >= 4 else "0000"
        print(f" Processing {self.Payment_Method} payment of {self.Amount} using card ending in {last_four}...")
        self.process_payment(card_number)
        print(f" Payment of {self.Amount} recorded as {self.Payment_Status} via {self.Payment_Method}.")
