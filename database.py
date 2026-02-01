from mysql.connector import connect


class Database:
    # establish the connection to the database in MySQL Server
    def __init__(self, username, password) -> None:
        self.connection = connect(
            host="localhost",
            user=username,
            password=password,
            database="boardgame_shop"
        )

    def __get_cursor__(self):
        return self.connection.cursor()

    # execute and fetch all results
    def execute_with_fetchall(self, query):
        with self.__get_cursor__() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    # execute with commit
    def execute_with_commit(self, query):
        with self.__get_cursor__() as cursor:
            cursor.execute(query)
            self.connection.commit()
