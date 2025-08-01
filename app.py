from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ---------------- EMAIL CONFIG ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'akhilroyal151@gmail.com'
app.config['MAIL_PASSWORD'] = 'ngel ackz xcby ccci'  # App password

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

DB_PATH = 'database.db'

# ------------------ DB SETUP ------------------
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # USERS table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            college_id TEXT UNIQUE NOT NULL,
            branch TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            is_verified INTEGER DEFAULT 1,
            total_leaves INTEGER DEFAULT 10,
            leaves_taken INTEGER DEFAULT 0
        )
        ''')

        # Leave applications
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            applied_on TEXT DEFAULT CURRENT_TIMESTAMP,
            reviewed_by TEXT,
            remarks TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        # Activity log
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            performed_by TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Sample users
        users = [
            ("Admin User", "admin@example.com", "admin123", "ADM001", "MCA", "admin"),
            ("Faculty One", "faculty@example.com", "faculty123", "FAC001", "MBA", "faculty"),
            ("CR User", "cr@example.com", "cr123", "CR001", "CSE", "cr"),
            ("Student A", "student@example.com", "student123", "STD001", "EEE", "student"),
        ]
        for name, email, password, college_id, branch, role in users:
            cursor.execute('''
                INSERT INTO users (name, email, password, college_id, branch, role, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (name, email, password, college_id, branch, role))

        conn.commit()
        conn.close()
        print("✅ Database initialized.")
    else:
        print("ℹ️ Database already exists.")


# ------------------ ROUTES ------------------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        college_id = request.form['college_id']
        branch = request.form['branch']

        token = serializer.dumps(email, salt='email-verify')
        verify_url = url_for('verify_email', token=token, _external=True)

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (name, email, password, college_id, branch)
                    VALUES (?, ?, ?, ?, ?)''',
                    (name, email, password, college_id, branch))
                conn.commit()

            msg = Message('Verify your email - Student Leave Portal',
                          sender='akhilroyal151@gmail.com', recipients=[email])
            msg.body = f'Hi {name}, click the link to verify: {verify_url}'
            mail.send(msg)

            flash('Signup successful. Check your email to verify.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Email or College ID already exists.', 'danger')
            return redirect('/signup')

    return render_template('signup.html')


@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify', max_age=3600)
    except Exception:
        return 'Verification link is invalid or expired.'

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_verified=1 WHERE email=?', (email,))
        cursor.execute('SELECT * FROM users WHERE email=?', (email,))
        user = cursor.fetchone()

    session['user'] = user[0]
    session['role'] = user[6]

    if user[6] == 'student':
        return redirect('/dashboard')
    elif user[6] == 'faculty':
        return redirect('/faculty_portal')
    elif user[6] == 'cr':
        return redirect('/cr_dashboard')
    elif user[6] == 'admin':
        return redirect('/admin_dashboard')
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        college_id = request.form['college_id']
        password = request.form['password']

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE college_id=? AND password=?', (college_id, password))
            user = cursor.fetchone()

            if user:
                if user[7] == 1:
                    session['user'] = user[0]
                    session['role'] = user[6]
                    if user[6] == 'student':
                        return redirect('/dashboard')
                    elif user[6] == 'faculty':
                        return redirect('/faculty_portal')
                    elif user[6] == 'cr':
                        return redirect('/cr_dashboard')
                    elif user[6] == 'admin':
                        return redirect('/admin_dashboard')
                else:
                    flash('Please verify your email.', 'warning')
            else:
                flash('Invalid credentials.', 'danger')

    return render_template('login.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email=? AND password=? AND role="admin"', (email, password))
            admin = cursor.fetchone()

            if admin:
                session['user'] = admin[0]
                session['role'] = 'admin'
                return redirect('/admin_dashboard')
            else:
                flash('Invalid admin credentials.', 'danger')

    return render_template('admin_login.html')


@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (name, email, password, college_id, branch, role, is_verified)
                VALUES (?, ?, ?, ?, ?, 'admin', 1)
            ''', (name, email, password, f"ADM{email[:3]}", "AdminBranch"))
            conn.commit()

        flash("Admin registered successfully. Please login.")
        return redirect('/admin_login')

    return render_template('admin_signup.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('student_dashboard.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/admin_login')
    return render_template('admin_dashboard.html')


@app.route('/faculty_portal')
def faculty_portal():
    if 'user' not in session or session.get('role') != 'faculty':
        return redirect('/login')

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leave_applications WHERE reviewed_by IS NULL AND status="pending"')
        leave_requests = cursor.fetchall()

    return render_template('faculty_dashboard.html', leave_requests=leave_requests)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
@app.route('/accept_leave', methods=['POST'])
def accept_leave():
    leave_id = request.form['id']
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE leave_applications 
            SET status = 'approved', reviewed_by = ? 
            WHERE id = ?
        ''', (session.get('user_name'), leave_id))
        conn.commit()
    return redirect('/faculty_portal')

@app.route('/reject_leave', methods=['POST'])
def reject_leave():
    leave_id = request.form['id']
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE leave_applications 
            SET status = 'rejected', reviewed_by = ? 
            WHERE id = ?
        ''', (session.get('user_name'), leave_id))
        conn.commit()
    return redirect('/faculty_portal')



# ------------------ RUN APP ------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0") 
