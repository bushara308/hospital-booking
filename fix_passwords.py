
import pymysql
from werkzeug.security import generate_password_hash
from config import Config

try:
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    cursor = conn.cursor()
    print("Connected. Updating patient passwords to 'password123' and admin to 'admin123'...")
    cursor.execute("UPDATE patients SET password_hash=%s", (generate_password_hash('password123'),))
    cursor.execute("UPDATE admins SET password_hash=%s WHERE username='admin'", (generate_password_hash('admin123'),))
    conn.commit()
    conn.close()
    print("Success!")
except Exception as e:
    print("Error:", e)
