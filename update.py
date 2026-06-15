from utils.db import init_db
import sqlite3

# Ensure schema is up to date
init_db()

c = sqlite3.connect('database.db')
c.execute("UPDATE users SET display_name='Apurba Roy' WHERE email='apurbaroyleo5@gmail.com'")
c.commit()
