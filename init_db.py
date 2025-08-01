import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    college_id TEXT NOT NULL,
    branch TEXT NOT NULL,
    role TEXT DEFAULT 'student',
    is_verified INTEGER DEFAULT 0,
    total_leaves INTEGER DEFAULT 10,
    leaves_taken INTEGER DEFAULT 0
)
''')

# Leave applications table
cursor.execute('''
CREATE TABLE IF NOT EXISTS leave_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected
    applied_on TEXT DEFAULT CURRENT_TIMESTAMP,
    reviewed_by TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()

print("Database with leave tracking initialized successfully.")
