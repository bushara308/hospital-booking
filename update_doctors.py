import pymysql
from config import Config

connection = pymysql.connect(
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB
)

try:
    with connection.cursor() as cursor:
        cursor.execute("UPDATE doctors SET name='Dr. Amar Rasal' WHERE id=1")
        cursor.execute("UPDATE doctors SET name='Dr. Vishal Mutkule' WHERE id=2")
        cursor.execute("UPDATE doctors SET name='Dr. Imran Khan' WHERE id=3")
        cursor.execute("UPDATE doctors SET name='Dr. Suvarna Karpe' WHERE id=4")
    connection.commit()
    print("Successfully updated doctor names in the live database!")
except Exception as e:
    print(f"Error: {e}")
finally:
    connection.close()
