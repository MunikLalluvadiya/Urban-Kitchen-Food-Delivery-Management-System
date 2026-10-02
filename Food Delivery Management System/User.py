import csv
import hashlib
import os

USER_FILE = "user.csv"
HEADER = ["User_Id", "Name", "Phone_Number", "Email", "Address", "Password"]


# ---------------------------------------------------------------
# Helpers (module level, no input/print)
# ---------------------------------------------------------------
def _hash_password(password):
    salt = os.urandom(8).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def _check_password(stored, password):
    # Old rows in user.csv still hold plain-text passwords, so accept those too.
    if stored == password:
        return True
    if "$" in stored:
        salt, digest = stored.split("$", 1)
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex() == digest
    return False


def _read_rows():
    try:
        with open(USER_FILE, "r", newline="") as file:
            return list(csv.reader(file))[1:]      # skip header
    except FileNotFoundError:
        return []


def _write_rows(rows):
    with open(USER_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(HEADER)
        writer.writerows(rows)


class User:

    # ===========================================================
    # UI-FRIENDLY METHODS: take values as parameters and return
    # (success, message). No input() and no print() inside.
    # Use these from Streamlit / Flask.
    # ===========================================================
    def register_user(self, user_id, name, phone, email, address, password):
        rows = _read_rows()
        for row in rows:
            if row[3] == email:
                return False, "This email is already registered."
            if row[0] == str(user_id):
                return False, "This User Id already exists."

        rows.append([user_id, name, phone, email, address, _hash_password(password)])
        _write_rows(rows)

        self.User_Id = user_id
        self.Name = name
        self.Phone_Number = phone
        self.Email = email
        self.Address = address
        self.Password = password
        return True, "Registered successfully."

    def login_user(self, email, password):
        for row in _read_rows():
            if row[3] == email:
                if _check_password(row[5], password):
                    self.User_Id = row[0]
                    self.Name = row[1]
                    self.Phone_Number = row[2]
                    self.Email = row[3]
                    self.Address = row[4]
                    self.Password = password
                    return True, "Login successful."
                return False, "Incorrect password."
        return False, "You are not a registered user. Please register first."

    def get_profile(self, user_id):
        """Returns a dict without the password, or None if not found."""
        for row in _read_rows():
            if row[0] == str(user_id):
                return {"User_Id": row[0], "Name": row[1], "Phone_Number": row[2],
                        "Email": row[3], "Address": row[4]}
        return None

    def update_field(self, email, password, field, new_value):
        """field must be one of: Name, Phone_Number, Email, Address"""
        columns = {"Name": 1, "Phone_Number": 2, "Email": 3, "Address": 4}
        if field not in columns:
            return False, "You can only change Name, Phone_Number, Email or Address."

        rows = _read_rows()
        target = None
        for row in rows:
            if row[3] == email:
                target = row
                break
        if target is None:
            return False, "You are not a registered user. Please register first."
        if not _check_password(target[5], password):
            return False, "Incorrect password."

        if field == "Email" and any(r[3] == new_value for r in rows):
            return False, "That email is already used by another account."

        target[columns[field]] = new_value
        _write_rows(rows)

        setattr(self, field, new_value)
        return True, "Profile updated successfully."

    def set_password(self, email, current_password, new_password):
        rows = _read_rows()
        for row in rows:
            if row[3] == email:
                if not _check_password(row[5], current_password):
                    return False, "Incorrect current password."
                row[5] = _hash_password(new_password)
                _write_rows(rows)
                self.Password = new_password
                return True, "Password changed successfully."
        return False, "Email not found."

    # ===========================================================
    # CONSOLE METHODS: same names as before so main.py keeps working.
    # They only collect input, call the methods above, and print.
    # ===========================================================
    def Register(self):
        try:
            user_id = int(input(" Enter Your User Id : "))
            name = input(" Enter Your Name : ")
            phone = int(input(" Enter Your Phone Number : "))
        except ValueError:
            print(" User Id and Phone Number must be numbers.")
            return
        email = input(" Enter Your Email : ")
        address = input(" Enter Your Address : ")
        password = input(" Enter Your Password : ")

        ok, message = self.register_user(user_id, name, phone, email, address, password)
        print(" " + message)

    def Login(self):
        email = input(" Enter Your Email : ")
        password = input(" Enter Your Password : ")
        ok, message = self.login_user(email, password)
        print(" " + message)
        return ok

    def View_Profile(self):
        user_id = input(" Enter User Id : ")
        profile = self.get_profile(user_id)
        if profile is None:
            print(" There Is NO User With This Id. ")
            return
        for key, value in profile.items():
            print(key, ":", value)

    def Update_Profile(self):
        email = input(" Enter Your Email : ")
        password = input(" Enter Your Password : ")
        field = input(" What would you change (Name / Phone_Number / Email / Address) : ")
        new_value = input(f" Enter New {field} : ")
        ok, message = self.update_field(email, password, field, new_value)
        print(" " + message)

    def Change_Password(self):
        email = input(" Enter Your Email : ")
        current = input(" Enter Current Password : ")
        new = input(" Enter New Password : ")
        ok, message = self.set_password(email, current, new)
        print(" " + message)