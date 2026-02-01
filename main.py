from database import Database
from getpass import getpass
from mysql.connector import connect, Error
from menu import main_menu


def check_credentials(username, password):
    try:
        conn = connect(
            host="localhost",
            user=username,
            password=password,
            database="boardgame_shop"
        )
        conn.close()
        return True
    except Error:
        return False


valid_connection = False

while not valid_connection:
    username = input("Enter your MySQL username: ")
    password = getpass("Enter MySQL password: ")

    if check_credentials(username, password):
        valid_connection = True
    else:
        print(
            "Connection failed. Please make sure:\n"
            "- Credentials are correct\n"
            "- MySQL server is running\n"
        )

db = Database(username, password)
main_menu(db, ["UserLogin", "New Member Registration", "Exit"])
