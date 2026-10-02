import csv
import os
from FoodItem import FoodItem

RESTAURANT_FILE = "restaurant.csv"
HEADER = ["Restaurant_ID", "Restaurant_Name", "Location", "Rating", "Food_Items"]


# ---------------------------------------------------------------
# Storage Helpers
# ---------------------------------------------------------------
def ensure_restaurant_file():
    """Ensures restaurant.csv exists with header."""
    if not os.path.exists(RESTAURANT_FILE) or os.stat(RESTAURANT_FILE).st_size == 0:
        with open(RESTAURANT_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(HEADER)


def _read_rows():
    ensure_restaurant_file()
    try:
        with open(RESTAURANT_FILE, "r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)  # skip header
            return [row for row in reader if row]
    except FileNotFoundError:
        return []


def _write_rows(rows):
    with open(RESTAURANT_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(HEADER)
        writer.writerows(rows)


def _parse_food_items(items_str):
    """Parses 'fid:fname:cat:price:avail;...' into a list of FoodItem objects."""
    items = []
    if not items_str:
        return items
    for item_str in items_str.split(";"):
        if not item_str.strip():
            continue
        parts = item_str.split(":")
        if len(parts) != 5:
            continue
        fid, fname, category, price, availability = parts
        try:
            parsed_price = float(price)
        except ValueError:
            parsed_price = 0.0
        is_avail = availability.strip().lower() in ("true", "yes", "1")
        items.append(FoodItem(fid, fname, category, parsed_price, is_avail))
    return items


def _serialize_food_items(food_items):
    """Serializes a list of FoodItem objects to ';'-separated string."""
    parts = []
    for item in food_items:
        parts.append(f"{item.Food_ID}:{item.Food_Name}:{item.Category}:{item.Price}:{item.Availability}")
    return ";".join(parts)


# ---------------------------------------------------------------
# UI-Friendly Functions (Web App / API)
# ---------------------------------------------------------------
def get_all_restaurants():
    """Returns a list of restaurant dictionaries."""
    rows = _read_rows()
    restaurants = []
    for row in rows:
        if len(row) < 4:
            continue
        rest_id, name, location, rating = row[0], row[1], row[2], row[3]
        items_str = row[4] if len(row) > 4 else ""
        items = _parse_food_items(items_str)
        try:
            parsed_rating = float(rating)
        except ValueError:
            parsed_rating = 0.0

        restaurants.append({
            "Restaurant_ID": rest_id,
            "Restaurant_Name": name,
            "Location": location,
            "Rating": parsed_rating,
            "Food_Items": items,
            "Total_Items": len(items)
        })
    return restaurants


def search_restaurants(keyword="", min_rating=0.0):
    """Filters restaurants by name, location, dish name, or category, and minimum rating."""
    all_rests = get_all_restaurants()
    results = []
    kw = (keyword or "").strip().lower()
    try:
        min_r = float(min_rating)
    except (ValueError, TypeError):
        min_r = 0.0

    for r in all_rests:
        match_name_or_loc = (kw in r["Restaurant_Name"].lower()) or (kw in r["Location"].lower())
        match_dish = any(kw in item.Food_Name.lower() or kw in item.Category.lower() for item in r["Food_Items"])
        match_kw = (not kw) or match_name_or_loc or match_dish
        match_rating = r["Rating"] >= min_r
        if match_kw and match_rating:
            results.append(r)
    return results


def get_restaurant_by_id(restaurant_id):
    """Returns a Restaurant instance by ID or None."""
    rows = _read_rows()
    for row in rows:
        if row and row[0] == str(restaurant_id):
            try:
                rating = float(row[3])
            except ValueError:
                rating = 0.0
            return Restaurant(row[0], row[1], row[2], rating)
    return None


def add_new_restaurant(restaurant_id, restaurant_name, location, rating):
    """Adds a new restaurant to restaurant.csv without console input."""
    if not str(restaurant_id).strip():
        return False, "Restaurant ID cannot be empty."
    if not str(restaurant_name).strip():
        return False, "Restaurant Name cannot be empty."
    if not str(location).strip():
        return False, "Location cannot be empty."
    try:
        rating_val = float(rating)
        if not (0.0 <= rating_val <= 5.0):
            return False, "Rating must be between 0.0 and 5.0."
    except (ValueError, TypeError):
        return False, "Rating must be a valid number."

    rows = _read_rows()
    for row in rows:
        if row and row[0] == str(restaurant_id):
            return False, f"Restaurant ID '{restaurant_id}' already exists."

    rows.append([str(restaurant_id), str(restaurant_name), str(location), str(rating_val), ""])
    _write_rows(rows)
    return True, f"Restaurant '{restaurant_name}' added successfully."


# ---------------------------------------------------------------
# Legacy Helpers (Preserved for main.py console compatibility)
# ---------------------------------------------------------------
def get_restaurant_basic_info(restaurant_id):
    """Legacy helper: returns (name, location, rating) or (None, None, None)."""
    rows = _read_rows()
    for row in rows:
        if row and row[0] == str(restaurant_id):
            return row[1], row[2], row[3]
    return None, None, None


def view_restaurants():
    """Legacy console function."""
    rests = get_all_restaurants()
    if not rests:
        print(" No restaurants available yet.")
        return
    for r in rests:
        print(f"Restaurant_ID : {r['Restaurant_ID']} , Restaurant_Name : {r['Restaurant_Name']} , "
              f"Location : {r['Location']} , Rating : {r['Rating']}")


def search_restaurant():
    """Legacy console function with interactive input."""
    search_text = input(" Enter restaurant name to search : ").strip()
    results = search_restaurants(keyword=search_text)
    if not results:
        print(" No matching restaurant found.")
        return
    for r in results:
        print(f"Restaurant_ID : {r['Restaurant_ID']} , Restaurant_Name : {r['Restaurant_Name']} , "
              f"Location : {r['Location']} , Rating : {r['Rating']}")


# ---------------------------------------------------------------
# Restaurant Class
# ---------------------------------------------------------------
class Restaurant:

    def __init__(self, Restaurant_ID, Restaurant_Name, Location, Rating):
        self.Restaurant_ID = str(Restaurant_ID)
        self.Restaurant_Name = str(Restaurant_Name)
        self.Location = str(Location)
        self.Rating = Rating
        self.List_Of_FoodItems = []
        self._load_items()

    def _load_items(self):
        self.List_Of_FoodItems = []
        rows = _read_rows()
        for row in rows:
            if row and row[0] == self.Restaurant_ID:
                items_str = row[4] if len(row) > 4 else ""
                self.List_Of_FoodItems = _parse_food_items(items_str)
                break

    def _save_items_to_csv(self):
        rows = _read_rows()
        updated_rows = []
        found = False
        items_str = _serialize_food_items(self.List_Of_FoodItems)

        for row in rows:
            if row and row[0] == self.Restaurant_ID:
                updated_rows.append([self.Restaurant_ID, self.Restaurant_Name, self.Location, str(self.Rating), items_str])
                found = True
            else:
                updated_rows.append(row)

        if not found:
            updated_rows.append([self.Restaurant_ID, self.Restaurant_Name, self.Location, str(self.Rating), items_str])

        _write_rows(updated_rows)

    # ===========================================================
    # UI-FRIENDLY METHODS: take parameters, return (success, msg)
    # ===========================================================
    def add_food_item(self, food_id, food_name, category, price, availability=True):
        """Adds a food item to this restaurant's menu."""
        fid = str(food_id).strip()
        fname = str(food_name).strip()
        cat = str(category).strip()

        if not fid:
            return False, "Food ID cannot be empty."
        if not fname:
            return False, "Food Name cannot be empty."
        if not cat:
            return False, "Category cannot be empty."
        try:
            price_val = float(price)
            if price_val < 0:
                return False, "Price cannot be negative."
        except (ValueError, TypeError):
            return False, "Price must be a valid number."

        # Check for duplicate Food ID within this restaurant
        for item in self.List_Of_FoodItems:
            if item.Food_ID == fid:
                return False, f"Food ID '{fid}' already exists in this restaurant."

        is_avail = availability if isinstance(availability, bool) else (str(availability).strip().lower() in ("yes", "y", "true", "1"))
        new_item = FoodItem(fid, fname, cat, price_val, is_avail)
        self.List_Of_FoodItems.append(new_item)
        self._save_items_to_csv()
        return True, f"Added {fname} to {self.Restaurant_Name}'s menu."

    def remove_food_item(self, food_id):
        """Removes a food item from this restaurant's menu."""
        fid = str(food_id).strip()
        target = None
        for item in self.List_Of_FoodItems:
            if item.Food_ID == fid:
                target = item
                break

        if target is None:
            return False, f"Food item '{fid}' not found."

        self.List_Of_FoodItems.remove(target)
        self._save_items_to_csv()
        return True, f"Removed food item {fid}."

    def update_food_item(self, food_id, new_price=None, new_availability=None, new_name=None, new_category=None):
        """Updates fields of an existing food item."""
        fid = str(food_id).strip()
        target = None
        for item in self.List_Of_FoodItems:
            if item.Food_ID == fid:
                target = item
                break

        if target is None:
            return False, f"Food item '{fid}' not found."

        if new_price is not None:
            try:
                p = float(new_price)
                if p < 0:
                    return False, "Price cannot be negative."
                target.Update_Price(p)
            except (ValueError, TypeError):
                return False, "Price must be a valid number."

        if new_availability is not None:
            if isinstance(new_availability, bool):
                target.Update_Availability(new_availability)
            else:
                target.Update_Availability(str(new_availability).strip().lower() in ("yes", "y", "true", "1"))

        if new_name is not None and str(new_name).strip():
            target.Food_Name = str(new_name).strip()

        if new_category is not None and str(new_category).strip():
            target.Category = str(new_category).strip()

        self._save_items_to_csv()
        return True, f"Updated food item {fid}."

    def get_menu(self):
        """Returns list of FoodItem objects."""
        return self.List_Of_FoodItems

    def get_menu_by_category(self):
        """Returns dictionary of food items grouped by Category."""
        grouped = {}
        for item in self.List_Of_FoodItems:
            cat = item.Category or "Other"
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(item)
        return grouped

    def get_categories(self):
        """Returns list of unique category names."""
        cats = []
        for item in self.List_Of_FoodItems:
            if item.Category and item.Category not in cats:
                cats.append(item.Category)
        return cats

    # ===========================================================
    # CONSOLE METHODS (Preserved for main.py compatibility)
    # ===========================================================
    def Display_Restaurant(self):
        print(f"Restaurant_ID : {self.Restaurant_ID} , Restaurant_Name : {self.Restaurant_Name} , "
              f"Location : {self.Location} , Rating : {self.Rating}")
        if self.List_Of_FoodItems:
            for item in self.List_Of_FoodItems:
                print(f"    Food_ID : {item.Food_ID} , Food_Name : {item.Food_Name} , "
                      f"Category : {item.Category} , Price : {item.Price} , Availability : {item.Availability}")
        else:
            print("    (No food items yet.)")

    def Add_Food_Item(self):
        Food_ID = input(" Enter Food ID : ").strip()
        Food_Name = input(" Enter Food Name : ").strip()
        Category = input(" Enter Food Category : ").strip()
        try:
            Price = float(input(" Enter Food Price : "))
        except ValueError:
            print(" Price must be a number.")
            return
        Availability = input(" Enter Availability (yes/no) : ").strip().lower() in ("yes", "y", "true")

        ok, msg = self.add_food_item(Food_ID, Food_Name, Category, Price, Availability)
        print(" " + msg)

    def Remove_Food_Item(self):
        food_id = input(" Enter Food ID to remove : ").strip()
        ok, msg = self.remove_food_item(food_id)
        if ok:
            print(f" Removed food item {food_id}.")
        else:
            print(" Deta NotFound! ")

    def Update_Food_Item(self):
        food_id = input(" Enter Food ID to update : ").strip()
        target_item = None
        for item in self.List_Of_FoodItems:
            if item.Food_ID == food_id:
                target_item = item
                break

        if target_item is None:
            print(" Deta NotFound! ")
            return

        choice = input(" Update (1) Price or (2) Availability? : ").strip()
        if choice == "1":
            try:
                new_price = float(input(" Enter new price : "))
            except ValueError:
                print(" Price must be a number.")
                return
            ok, msg = self.update_food_item(food_id, new_price=new_price)
            print(f" Updated food item {food_id}.")
        elif choice == "2":
            avail_input = input(" Available? (yes/no) : ").strip().lower() in ("yes", "y", "true")
            ok, msg = self.update_food_item(food_id, new_availability=avail_input)
            print(f" Updated food item {food_id}.")
        else:
            print(" Invalid choice.")

    def View_Menu(self):
        if not self.List_Of_FoodItems:
            print(" (No food items yet.)")
            return
        for item in self.List_Of_FoodItems:
            item.Display_Food_Details()