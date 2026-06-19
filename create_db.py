import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    security_question TEXT NOT NULL,
    security_answer TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses(
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    amount REAL,
    description TEXT,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS income(
    income_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    source TEXT,
    amount REAL,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS budgets(
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    budget_amount REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS savings_goals(
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    goal_name TEXT,
    target_amount REAL,
    saved_amount REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS trips(
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    destination TEXT,
    start_date TEXT,
    end_date TEXT,
    budget REAL,
    notes TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS travel_expenses(
    travel_expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER,
    category TEXT,
    amount REAL,
    description TEXT
)
""")

conn.commit()
conn.close()

print("Database Created Successfully!")