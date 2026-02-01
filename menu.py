from database import Database
import hashlib
from datetime import datetime, timedelta
import re
from getpass import getpass

current_user_id = None


def is_valid_email(email: str) -> bool:  # Validates email format using regex
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email) is not None


def is_valid_phone(phone: str) -> bool:  # Validates phone number
    if phone == "":
        return True
    pattern = r"^\+?\d{7,15}$"
    return re.match(pattern, phone) is not None


# Main menu shown before login/registration

def main_menu(db: Database, options):
    while True:
        print_header("WELCOME TO THE BOARDGAME SHOP")
        print_option(options)

        choice = check_choice(len(options))

        if choice == 1:
            memberLogin(db)
        elif choice == 2:
            memberReg(db)
        else:
            quit()


# Hashes password before storing or comparing
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def memberReg(db: Database):  # New member registration
    print_header("NEW MEMBER REGISTRATION")

    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()
    street = input("Street: ").strip()
    city = input("City: ").strip()
    postal_code = input("Postal code: ").strip()
    phone_no = input("Phone (optional): ").strip()
    email = input("Email: ").strip()
    password = getpass("Password: ").strip()

    if not first_name or not last_name or not email or not password:
        print("Required fields cannot be empty.")
        return

    if not is_valid_email(email):
        print("Invalid email address.")
        return

    if not is_valid_phone(phone_no):
        print("Invalid phone number.")
        return

    # Prevent duplicate email registration
    if db.execute_with_fetchall(
        f"SELECT user_id FROM users WHERE email='{email}'"
    ):
        print("Email address already exists.")
        return

    # Insert new user into database
    db.execute_with_commit(f"""
        INSERT INTO users
        (first_name,last_name,street,city,postal_code,phone_no,email,pwd_hash)
        VALUES
        ('{first_name}','{last_name}','{street}','{city}',
         '{postal_code}','{phone_no}','{email}','{hash_password(password)}')
    """)

    print("Registration successful.")


def memberLogin(db: Database):  # Authenticates user and starts member session
    global current_user_id

    print_header("USER LOGIN")

    email = input("Email: ").strip()
    password = getpass("Password: ").strip()

    if not email or not password:
        print("Email/Password required.")
        return

    result = db.execute_with_fetchall(
        f"SELECT user_id,pwd_hash FROM users WHERE email='{email}'"
    )

    if not result:
        print("Email does not exist.")
        return

    if hash_password(password) != result[0][1]:
        print("Incorrect password.")
        return

    current_user_id = result[0][0]
    member_menu(db)


# Member menu

def member_menu(db: Database):  # Member menu shown after successful login
    while True:
        print_header("MEMBER MENU")
        print("1) Browse by genre")
        print("2) Search by designer/title")
        print("3) View cart")
        print("4) Checkout")
        print("5) Log out")

        choice = input("Choice: ").strip()

        if choice == "1":
            browse_by_genre(db)
        elif choice == "2":
            search_menu(db)
        elif choice == "3":
            view_cart(db)
        elif choice == "4":
            checkout(db)
        elif choice == "5":
            return


# Adds or updates a game in the shopping cart

def add_to_cart(db: Database, game_id):
    qty = input("Enter quantity: ").strip()

    if not qty.isdigit() or int(qty) <= 0:
        print("Invalid quantity.")
        return

    # Check if game already exists in cart
    result = db.execute_with_fetchall(f"""
        SELECT quantity FROM cart
        WHERE user_id={current_user_id} AND game_id='{game_id}'
    """)

    if result:
        # Update quantity if game already in cart
        db.execute_with_commit(f"""
            UPDATE cart
            SET quantity = quantity + {qty}
            WHERE user_id={current_user_id} AND game_id='{game_id}'
        """)
    else:
        # Insert new game into cart
        db.execute_with_commit(f"""
            INSERT INTO cart (user_id, game_id, quantity)
            VALUES ({current_user_id}, '{game_id}', {qty})
        """)

    print("Game added to cart.")


# Browse / Search

def browse_by_genre(db: Database):  # Browse games by genre
    genres = db.execute_with_fetchall(
        "SELECT DISTINCT genre FROM games ORDER BY genre"
    )

    for i, g in enumerate(genres, 1):  # Display all available genres
        print(f"{i}. {g[0]}")

    choice = input("Select genre: ").strip()
    if not choice.isdigit():
        return

    genre = genres[int(choice) - 1][0]
    offset = 0

    while True:
        games = db.execute_with_fetchall(f"""
            SELECT game_id,title,designer,unit_price
            FROM games
            WHERE genre='{genre}'
            LIMIT 2 OFFSET {offset}
        """)
        # Display games for the selected genre
        for g in games:
            print(f"{g[0]} | {g[1]} | {g[2]} | ${g[3]}")

        choice = input("ENTER=back | n=next | game_id: ").strip()

        if choice == "":
            return
        elif choice == "n":
            offset += 2
        elif choice.upper().startswith("BG"):
            add_to_cart(db, choice.upper())


def search_menu(db: Database):  # Search menu dispatcher
    print("1) Search by designer")
    print("2) Search by title")
    print("3) Return")

    choice = input("Choice: ").strip()

    if choice == "1":
        search_designer(db)
    elif choice == "2":
        search_title(db)


def search_designer(db: Database):  # Searches games by designer name
    name = input("Designer name: ").strip()
    offset = 0

    while True:
        games = db.execute_with_fetchall(f"""
            SELECT game_id,title,designer,unit_price
            FROM games
            WHERE designer LIKE '{name}%'
            LIMIT 3 OFFSET {offset}
        """)
        # Display search results
        for g in games:
            print(f"{g[0]} | {g[1]} | {g[2]} | ${g[3]}")

        choice = input("ENTER=back | n=next | game_id: ").strip()

        if choice == "":
            return
        elif choice == "n":
            offset += 3
        elif choice.upper().startswith("BG"):
            add_to_cart(db, choice.upper())


def search_title(db: Database):  # Searches games by title
    word = input("Title keyword: ").strip()
    offset = 0

    while True:
        games = db.execute_with_fetchall(f"""
            SELECT game_id,title,designer,unit_price
            FROM games
            WHERE LOWER(title) LIKE '%{word.lower()}%'
            LIMIT 3 OFFSET {offset}
        """)
        # Display search results
        for g in games:
            print(f"{g[0]} | {g[1]} | {g[2]} | ${g[3]}")

        choice = input("ENTER=back | n=next | game_id: ").strip()

        if choice == "":
            return
        elif choice == "n":
            offset += 3
        elif choice.upper().startswith("BG"):
            add_to_cart(db, choice.upper())


# View cart

def view_cart(db: Database):  # Displays current cart contents
    print_header("Current Cart Contents")

    cart = db.execute_with_fetchall(f"""
        SELECT g.game_id, g.title, g.unit_price,
               c.quantity, (g.unit_price*c.quantity)
        FROM cart c
        JOIN games g ON c.game_id=g.game_id
        WHERE c.user_id={current_user_id}
    """)

    if not cart:
        print("Cart is empty.")
        return

    # Print cart table header
    print(f"{'Game ID':<10} {'Title':<45} {'$':>8} {'Qty':>5} {'Total':>8}")
    print("-" * 80)

    total_sum = 0
    for game_id, title, price, qty, total in cart:
        title = title[:42] + "..." if len(title) > 45 else title
        print(f"{game_id:<10} {title:<45} {price:>8.2f} {qty:>5} "
              f"{total:>8.2f}")
        total_sum += total

    # Print total cost of all items in cart
    print("-" * 80)
    print(f"{'Total =':>66} ${total_sum:.2f}")


# Checkout
def checkout(db: Database):  # Creates order, order items, and prints invoice
    print_header("Invoice")

    cart = db.execute_with_fetchall(f"""
        SELECT g.game_id, g.title, g.unit_price,
               c.quantity, (g.unit_price*c.quantity)
        FROM cart c
        JOIN games g ON c.game_id=g.game_id
        WHERE c.user_id={current_user_id}
    """)

    if not cart:
        print("Cart is empty.")
        return

    total_sum = sum(item[4] for item in cart)

    confirm = input("\nProceed to checkout (Y/N)? ").strip().lower()
    if confirm != "y":
        return

    name, street, city, postal_code = db.execute_with_fetchall(f"""
        SELECT CONCAT(first_name,' ',last_name), street, city, postal_code
        FROM users WHERE user_id={current_user_id}
    """)[0]

    delivery_date = (datetime.now() + timedelta(days=7)).date()

    # Create order record
    db.execute_with_commit(f"""
        INSERT INTO orders
        (user_id, created, ship_street, ship_city, ship_postal_code)
        VALUES
        ({current_user_id}, NOW(), '{street}', '{city}', '{postal_code}')
    """)

    order_no = db.execute_with_fetchall("SELECT LAST_INSERT_ID()")[0][0]

    # Insert order items
    for game_id, title, price, qty, total in cart:
        db.execute_with_commit(f"""
            INSERT INTO order_items (order_no, game_id, quantity, line_total)
            VALUES ({order_no}, '{game_id}', {qty}, {total})
        """)

    # Clear cart after checkout
    db.execute_with_commit(
        f"DELETE FROM cart WHERE user_id={current_user_id}"
    )

    # Print invoice
    print("\n" + "=" * 60)
    print(f"Invoice for Order no. {order_no}")
    print("=" * 60)
    print(f"Name: {name}")
    print(f"Address: {street}, {city}")
    print(f"Postcode: {postal_code}")
    print(f"Estimated delivery: {delivery_date}")
    print("-" * 60)

    print(f"{'Game ID':<10} {'Title':<40} {'$':>7} {'Qty':>5} {'Total':>8}")
    print("-" * 60)

    for game_id, title, price, qty, total in cart:
        title = title[:37] + "..." if len(title) > 40 else title
        print(f"{game_id:<10} {title:<40} {price:>7.2f} "
              f"{qty:>5} {total:>8.2f}")

    print("-" * 60)
    print(f"Total = ${total_sum:.2f}")
    print("=" * 60)

    input("Press Enter to return to the main menu")


def print_header(title):  # Prints a header
    width = 70
    print("*" * width)
    print(title.center(width))
    print("*" * width)


def print_option(options):  # Prints menu options
    for i in range(len(options)):
        print(f"{i + 1}. {options[i]}")


def check_choice(maxoption):  # Ensures user enters a valid menu choice
    while True:
        try:
            choice = int(input("Enter Choice: "))
            if 1 <= choice <= maxoption:
                return choice
        except ValueError:
            pass
        print("Invalid input.")
