import db
from FoodItem import FoodItem


class Cart:

    def __init__(self):
        self.List_Of_SelectedItems = []
        self.Total_Price = 0.0
        self.Restaurant_ID = None      # which restaurant this cart belongs to

    # ===========================================================
    # Internal helper: look up one food item in Supabase via db.py
    # Returns (FoodItem or None, is_available)
    # ===========================================================
    def _find_item(self, restaurant_id, food_id):
        return db.db_get_food_item(restaurant_id, food_id)

    # ===========================================================
    # UI-FRIENDLY METHODS: parameters in, (success, message) out.
    # No input() and no print() inside. Use these from Streamlit / Flask.
    # ===========================================================
    def add(self, restaurant_id, food_id, quantity):
        if quantity <= 0:
            return False, "Quantity must be at least 1."

        if self.List_Of_SelectedItems and self.Restaurant_ID != restaurant_id:
            return False, "Your cart has items from another restaurant. Empty it first."

        item, available = self._find_item(restaurant_id, food_id)
        if item is None:
            return False, "Item not found."
        if not available:
            return False, f"{item.Food_Name} is currently unavailable."

        # if the same food is already in the cart, increase its quantity
        for entry in self.List_Of_SelectedItems:
            if entry["item"].Food_ID == food_id:
                entry["quantity"] += quantity
                self.Calculate_Total()
                return True, f"Updated {item.Food_Name} quantity to {entry['quantity']}."

        self.List_Of_SelectedItems.append({"item": item, "quantity": quantity})
        self.Restaurant_ID = restaurant_id
        self.Calculate_Total()
        return True, f"Added {quantity} x {item.Food_Name} to cart."

    def remove(self, food_id):
        for entry in self.List_Of_SelectedItems:
            if entry["item"].Food_ID == food_id:
                self.List_Of_SelectedItems.remove(entry)
                if not self.List_Of_SelectedItems:
                    self.Restaurant_ID = None
                self.Calculate_Total()
                return True, f"Removed {food_id} from cart."
        return False, "Item not in cart."

    def set_quantity(self, food_id, new_quantity):
        if new_quantity <= 0:
            return self.remove(food_id)
        for entry in self.List_Of_SelectedItems:
            if entry["item"].Food_ID == food_id:
                entry["quantity"] = new_quantity
                self.Calculate_Total()
                return True, "Quantity updated."
        return False, "Item not in cart."

    def rows(self):
        """Cart as a list of dicts, ready for a table in the UI."""
        return [
            {
                "Food_ID": e["item"].Food_ID,
                "Food_Name": e["item"].Food_Name,
                "Price": e["item"].Price,
                "Quantity": e["quantity"],
                "Subtotal": e["item"].Price * e["quantity"],
            }
            for e in self.List_Of_SelectedItems
        ]

    def clear(self):
        self.List_Of_SelectedItems = []
        self.Total_Price = 0.0
        self.Restaurant_ID = None

    def Calculate_Total(self):
        total = 0.0
        for entry in self.List_Of_SelectedItems:
            total = total + (entry["item"].Price * entry["quantity"])
        self.Total_Price = total
        return self.Total_Price

    # ===========================================================
    # CONSOLE METHODS: same names as before so main.py keeps working.
    # ===========================================================
    def Add_Item(self):
        restaurant_id = input(" Enter Restaurant ID : ")
        food_id = input(" Enter Food ID : ")
        try:
            quantity = int(input(" Enter Quantity : "))
        except ValueError:
            print(" Quantity must be a number.")
            return
        ok, message = self.add(restaurant_id, food_id, quantity)
        print(" " + message)

    def Remove_Item(self):
        food_id = input(" Enter Food ID to remove : ")
        ok, message = self.remove(food_id)
        print(" " + message)

    def Update_Quantity(self):
        food_id = input(" Enter Food ID to update quantity : ")
        try:
            new_quantity = int(input(" Enter New Quantity : "))
        except ValueError:
            print(" Quantity must be a number.")
            return
        ok, message = self.set_quantity(food_id, new_quantity)
        print(" " + message)

    def View_Cart(self):
        if not self.List_Of_SelectedItems:
            print(" Cart is empty.")
            return
        for r in self.rows():
            print(f"Food_ID : {r['Food_ID']} , Food_Name : {r['Food_Name']} , Price : {r['Price']} , "
                  f"Quantity : {r['Quantity']} , Subtotal : {r['Subtotal']}")
        print(f"Total Price : {self.Total_Price}")

    def Empty_Cart(self):
        self.clear()
        print(" Cart Emptied.")