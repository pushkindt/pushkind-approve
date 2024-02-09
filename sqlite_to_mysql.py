import sqlite3

import mysql.connector

TABLES = ["user", "category", "order_category", "cashflow_statement", "income_statement", "site", "order"]


def get_db_connections():
    my_cnx = mysql.connector.connect(user="root", password="root", host="127.0.0.1", database="pushkind")
    sq_cnx = sqlite3.connect("app.db")

    with my_cnx.cursor() as my_cursor:
        my_cursor.execute("SET character_set_client = 'utf8mb4'")
        my_cursor.execute("SET character_set_results = 'utf8mb4'")
        my_cursor.execute("SET character_set_connection = 'utf8mb4'")
        my_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    return my_cnx, sq_cnx


def close_connections(my_cnx, sq_cnx):
    my_cnx.close()
    sq_cnx.close()


def sync_table(my_cnx, sq_cnx, table):
    sq_cursor = sq_cnx.cursor()
    sq_cursor.execute(f"SELECT * FROM `{table}`")
    rows = sq_cursor.fetchall()
    cols = tuple(col[0] for col in sq_cursor.description)
    sq_cursor.close()

    with my_cnx.cursor() as my_cursor:
        for row in rows:
            cols_string = ", ".join(cols)
            values_string = ", ".join(["%s"] * len(row))
            update_string = ", ".join([f"`{col}`=%s" for col in cols])
            sql = f"""
                INSERT INTO `{table}`({cols_string})
                VALUES ({values_string})
                ON DUPLICATE KEY UPDATE {update_string}
            """
            my_cursor.execute(sql, row + row)

        my_cnx.commit()


def print_counts(my_cnx, sq_cnx, table):
    sq_cursor = sq_cnx.cursor()
    sq_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
    rows = sq_cursor.fetchone()
    print(table, "SQLITE", rows[0], end=" | ")
    sq_cursor.close()

    with my_cnx.cursor() as my_cursor:
        my_cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        rows = my_cursor.fetchone()
        print("MYSQL", rows[0])


if __name__ == "__main__":
    mysql_conn, sqlite_conn = get_db_connections()

    for table_name in TABLES:
        sync_table(mysql_conn, sqlite_conn, table_name)

    close_connections(mysql_conn, sqlite_conn)
