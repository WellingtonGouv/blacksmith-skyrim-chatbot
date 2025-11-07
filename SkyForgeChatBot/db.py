import mysql.connector
global con

con = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="admin",
        database="skyforge"
    )

def get_order_status(order_id: int):
    cursor = con.cursor()
    query = "select status from order_tracking where order_id = %s"
    cursor.execute(query, (order_id,))
    result = cursor.fetchone()
    cursor.close()

    if result is not None:
        return result[0]
    else:
        return None

def get_next_order_id():
    cursor = con.cursor()
    query = "select max(order_id) from orders"
    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.close()

    if result is not None:
        return result + 1
    else:
        return 1

def insert_order_item(forge_item, quantity, order_id):
    try:
        cursor = con.cursor()
        cursor.callproc('insert_order_item', (forge_item, quantity, order_id))
        con.commit()
        cursor.close()
        print("Order item inserted successfully!")
        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")
        con.rollback()

        return -1

    except Exception as e:
        print(f"An error occurred: {e}")
        con.rollback()

        return -1

def get_total_order_price(order_id):
    cursor = con.cursor()
    query = f"select get_total_order_price({order_id})"
    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.close()

    return result

def insert_order_tracking(order_id, status):
    cursor = con.cursor()
    query = "insert into order_tracking (order_id, status) values (%s, %s)"
    cursor.execute(query, (order_id, status))
    con.commit()
    cursor.close()