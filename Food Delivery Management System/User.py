import hashlib
import os
import db

HEADER = ["User_Id", "Name", "Phone_Number", "Email", "Address", "Password"]


# ---------------------------------------------------------------
# Helpers (module level, no input/print)
# ---------------------------------------------------------------
def _hash_password(password):
    salt = os.urandom(8).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def _check_password(stored, password):
    # Legacy rows might still hold plain-text passwords, so accept those too.
    if stored == password:
        return True
    if "$" in stored:
        salt, digest = stored.split("$", 1)
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex() == digest
    return False


def _read_rows():
    """Returns list of rows for backward compatibility."""
    return db.db_get_all_user_rows()


def _write_rows(rows):
    """Legacy helper maintained for backward compatibility."""
    pass


class User:

    # ===========================================================
    # UI-FRIENDLY METHODS: take values as parameters and return
    # (success, message). No input() and no print() inside.
    # Use these from Streamlit / Flask.
    # ===========================================================
    def register_user(self, user_id, name, phone, email, address, password):
        clean_email = str(email).strip().lower()
        clean_uid = str(user_id).strip()

        if db.db_get_user_by_email(clean_email):
            return False, "This email is already registered."
        if db.db_get_user_by_id(clean_uid):
            return False, "This User Id already exists."

        hashed = _hash_password(password)
        db.db_insert_user(clean_uid, name, phone, clean_email, address, hashed)

        self.User_Id = clean_uid
        self.Name = name
        self.Phone_Number = phone
        self.Email = clean_email
        self.Address = address
        self.Password = password
        return True, "Registered successfully."

    def login_user(self, email, password):
        clean_email = str(email).strip().lower()
        user = db.db_get_user_by_email(clean_email)
        if not user:
            return False, "You are not a registered user. Please register first."

        if not _check_password(user.get("password", ""), password):
            return False, "Incorrect password."

        self.User_Id = str(user.get("user_id", ""))
        self.Name = str(user.get("name", ""))
        self.Phone_Number = str(user.get("phone_number", ""))
        self.Email = str(user.get("email", ""))
        self.Address = str(user.get("address", ""))
        self.Password = password
        return True, "Login successful."

    def get_profile(self, user_id):
        """Returns a dict without the password, or None if not found."""
        user = db.db_get_user_by_id(str(user_id).strip())
        if not user:
            return None
        return {
            "User_Id": str(user.get("user_id", "")),
            "Name": str(user.get("name", "")),
            "Phone_Number": str(user.get("phone_number", "")),
            "Email": str(user.get("email", "")),
            "Address": str(user.get("address", ""))
        }

    def update_field(self, email, password, field, new_value):
        """field must be one of: Name, Phone_Number, Email, Address"""
        valid_fields = ["Name", "Phone_Number", "Email", "Address"]
        if field not in valid_fields:
            return False, "You can only change Name, Phone_Number, Email or Address."

        clean_email = str(email).strip().lower()
        user = db.db_get_user_by_email(clean_email)
        if not user:
            return False, "You are not a registered user. Please register first."
        if not _check_password(user.get("password", ""), password):
            return False, "Incorrect password."

        if field == "Email":
            new_email = str(new_value).strip().lower()
            existing = db.db_get_user_by_email(new_email)
            if existing and existing.get("user_id") != user.get("user_id"):
                return False, "That email is already used by another account."

        db.db_update_user_field(clean_email, field, new_value)
        setattr(self, field, new_value)
        return True, "Profile updated successfully."

    def set_password(self, email, current_password, new_password):
        clean_email = str(email).strip().lower()
        user = db.db_get_user_by_email(clean_email)
        if not user:
            return False, "Email not found."

        if not _check_password(user.get("password", ""), current_password):
            return False, "Incorrect current password."

        new_hashed = _hash_password(new_password)
        db.db_update_user_password(clean_email, new_hashed)
        self.Password = new_password
        return True, "Password changed successfully."

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