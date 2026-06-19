from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'coincount_secret_key_change_in_production')

# Configuration
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', False) == 'True'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DATABASE = os.getenv('DATABASE_PATH', 'database.db')


# ----------------------------
# Database Connection
# ----------------------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------
# Home Page
# ----------------------------
@app.route('/')
def home():
    return render_template('index.html')


# ----------------------------
# Register
# ----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        # Validation
        if not name or not email or not password:
            flash("All fields are required", "danger")
            return redirect(url_for('register'))

        if password != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for('register'))

        if len(password) < 6:
            flash("Password must be at least 6 characters", "danger")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name, email, hashed)
            )

            conn.commit()

            flash(
                "Welcome to CoinCount! Registration Successful.",
                "success"
            )
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash(
                "Account already exists. Please login instead.",
                "warning"
            )
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            conn.close()

    return render_template('register.html')


# ----------------------------
# Login
# ----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Email and password required", "danger")
            return render_template('login.html')

        conn = get_db()

        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email=?",
                (email,)
            ).fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['user_id']
                session['name'] = user['name']

                flash(
                    f"Welcome back, {user['name']}!",
                    "success"
                )
                return redirect(url_for('dashboard'))

            flash(
                "Invalid Email or Password",
                "danger"
            )
        finally:
            conn.close()

    return render_template('login.html')


# ----------------------------
# Logout
# ----------------------------
@app.route('/logout')
def logout():

    session.clear()

    flash("Logged Out Successfully", "info")

    return redirect(url_for('home'))


# ----------------------------
# Dashboard
# ----------------------------
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    user_id = session['user_id']

    total_income = conn.execute(
        "SELECT IFNULL(SUM(amount),0) FROM income WHERE user_id=?",
        (user_id,)
    ).fetchone()[0]

    total_expense = conn.execute(
        "SELECT IFNULL(SUM(amount),0) FROM expenses WHERE user_id=?",
        (user_id,)
    ).fetchone()[0]

    total_savings = total_income - total_expense

    recent = conn.execute(
        '''
        SELECT *
        FROM expenses
        WHERE user_id=?
        ORDER BY expense_id DESC
        LIMIT 5
        ''',
        (user_id,)
    ).fetchall()

    categories = conn.execute(
        '''
        SELECT category,
        SUM(amount) AS total
        FROM expenses
        WHERE user_id=?
        GROUP BY category
        ''',
        (user_id,)
    ).fetchall()

    category_labels = []
    category_values = []

    for item in categories:

        category_labels.append(
            item['category']
        )

        category_values.append(
            item['total']
        )

    conn.close()

    return render_template(
        'dashboard.html',
        income=total_income,
        expense=total_expense,
        savings=total_savings,
        recent=recent,
        category_labels=category_labels,
        category_values=category_values
    )

# ----------------------------
# Expenses
# ----------------------------
@app.route('/expenses', methods=['GET', 'POST'])
def expenses():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':

        category = request.form.get('category', '').strip()
        amount = request.form.get('amount', '')
        description = request.form.get('description', '').strip()
        date = request.form.get('date', '')

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than 0", "danger")
                return redirect(url_for('expenses'))

            conn.execute(
                '''
                INSERT INTO expenses
                (user_id,category,amount,description,date)
                VALUES(?,?,?,?,?)
                ''',
                (
                    session['user_id'],
                    category,
                    amount,
                    description,
                    date
                )
            )

            conn.commit()
            flash("Expense Added", "success")
        except ValueError:
            flash("Invalid amount", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    try:
        data = conn.execute(
            "SELECT * FROM expenses WHERE user_id=? ORDER BY expense_id DESC",
            (session['user_id'],)
        ).fetchall()
    except Exception as e:
        flash(f"Error fetching expenses: {str(e)}", "danger")
        data = []
    finally:
        conn.close()

    return render_template(
        'expenses.html',
        expenses=data
    )


# ----------------------------
# Delete Expense
# ----------------------------
@app.route('/delete_expense/<int:id>')
def delete_expense(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    try:
        conn.execute(
            '''
            DELETE FROM expenses
            WHERE expense_id=?
            ''',
            (id,)
        )

        conn.commit()
        flash("Expense Deleted", "warning")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for('expenses'))


# ----------------------------
# Income
# ----------------------------
@app.route('/income', methods=['GET', 'POST'])
def income():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':

        source = request.form.get('source', '').strip()
        amount = request.form.get('amount', '')
        date = request.form.get('date', '')

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than 0", "danger")
                return redirect(url_for('income'))

            conn.execute(
                '''
                INSERT INTO income
                (user_id,source,amount,date)
                VALUES(?,?,?,?)
                ''',
                (
                    session['user_id'],
                    source,
                    amount,
                    date
                )
            )

            conn.commit()
            flash("Income Added", "success")
        except ValueError:
            flash("Invalid amount", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    try:
        records = conn.execute(
            "SELECT * FROM income WHERE user_id=? ORDER BY income_id DESC",
            (session['user_id'],)
        ).fetchall()
    except Exception as e:
        flash(f"Error fetching income: {str(e)}", "danger")
        records = []
    finally:
        conn.close()

    return render_template(
        'income.html',
        income=records
    )


# ----------------------------
# Budget
# ----------------------------
@app.route('/budget', methods=['GET', 'POST'])
def budget():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':

        category = request.form.get('category', '').strip()
        amount = request.form.get('amount', '')

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than 0", "danger")
                return redirect(url_for('budget'))

            conn.execute(
                '''
                INSERT INTO budgets
                (user_id,category,budget_amount)
                VALUES(?,?,?)
                ''',
                (
                    session['user_id'],
                    category,
                    amount
                )
            )

            conn.commit()
            flash("Budget Added", "success")
        except ValueError:
            flash("Invalid amount", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    try:
        budgets = conn.execute(
            '''
            SELECT *
            FROM budgets
            WHERE user_id=?
            ''',
            (session['user_id'],)
        ).fetchall()

        total_budget = conn.execute(
            '''
            SELECT IFNULL(SUM(budget_amount),0)
            FROM budgets
            WHERE user_id=?
            ''',
            (session['user_id'],)
        ).fetchone()[0]

        total_expense = conn.execute(
            '''
            SELECT IFNULL(SUM(amount),0)
            FROM expenses
            WHERE user_id=?
            ''',
            (session['user_id'],)
        ).fetchone()[0]

        if total_budget > 0:
            utilization = round(
                (total_expense / total_budget) * 100,
                1
            )
        else:
            utilization = 0
    except Exception as e:
        flash(f"Error fetching budgets: {str(e)}", "danger")
        budgets = []
        total_budget = 0
        total_expense = 0
        utilization = 0
    finally:
        conn.close()

    return render_template(
        'budget.html',
        budgets=budgets,
        utilization=utilization,
        total_budget=total_budget,
        total_expense=total_expense
    )

# ----------------------------
# Savings
# ----------------------------
@app.route('/savings', methods=['GET', 'POST'])
def savings():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':

        goal = request.form.get('goal', '').strip()
        target = request.form.get('target', '')
        saved = request.form.get('saved', '')

        try:
            target = float(target)
            saved = float(saved)

            if target <= 0 or saved < 0:
                flash("Enter valid amounts", "danger")
                return redirect(url_for('savings'))

            conn.execute(
                '''
                INSERT INTO savings_goals
                (user_id,goal_name,target_amount,saved_amount)
                VALUES(?,?,?,?)
                ''',
                (
                    session['user_id'],
                    goal,
                    target,
                    saved
                )
            )

            conn.commit()
            flash("Savings Goal Added Successfully", "success")
        except ValueError:
            flash("Invalid amounts", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    try:
        goals = conn.execute(
            "SELECT * FROM savings_goals WHERE user_id=?",
            (session['user_id'],)
        ).fetchall()
    except Exception as e:
        flash(f"Error fetching goals: {str(e)}", "danger")
        goals = []
    finally:
        conn.close()

    return render_template(
        'savings.html',
        goals=goals
    )


# ----------------------------
# Trips
# ----------------------------
@app.route('/trips', methods=['GET', 'POST'])
def trips():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':

        destination = request.form.get('destination', '').strip()
        start = request.form.get('start', '')
        end = request.form.get('end', '')
        budget = request.form.get('budget', '')
        notes = request.form.get('notes', '').strip()

        try:
            budget = float(budget)
            if budget <= 0:
                flash("Budget must be greater than 0", "danger")
                return redirect(url_for('trips'))

            conn.execute(
                '''
                INSERT INTO trips
                (user_id,destination,start_date,end_date,budget,notes)
                VALUES(?,?,?,?,?,?)
                ''',
                (
                    session['user_id'],
                    destination,
                    start,
                    end,
                    budget,
                    notes
                )
            )

            conn.commit()
            flash("Trip Added Successfully", "success")
        except ValueError:
            flash("Invalid budget amount", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    try:
        trips_data = conn.execute(
            "SELECT * FROM trips WHERE user_id=?",
            (session['user_id'],)
        ).fetchall()
    except Exception as e:
        flash(f"Error fetching trips: {str(e)}", "danger")
        trips_data = []
    finally:
        conn.close()

    return render_template('trips.html', trips=trips_data)


@app.route('/reports')
def reports():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('reports.html')

@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('profile.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form.get('email', '').strip()

        conn = get_db()

        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email=?",
                (email,)
            ).fetchone()

            if user:
                flash(
                    "OTP Sent Successfully (Demo OTP: 123456)",
                    "success"
                )

                return render_template(
                    'forgot_password.html',
                    email=email,
                    show_otp=True
                )

            flash(
                "Email Not Found",
                "danger"
            )
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            conn.close()

    return render_template(
        'forgot_password.html'
    )

@app.route('/delete_goal/<int:id>')
def delete_goal(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    try:
        conn.execute(
            '''
            DELETE FROM savings_goals
            WHERE goal_id=?
            ''',
            (id,)
        )

        conn.commit()
        flash(
            "Goal Deleted Successfully",
            "warning"
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(
        url_for('savings')
    )

@app.route('/reset_password', methods=['POST'])
def reset_password():

    email = request.form.get('email', '').strip()
    otp = request.form.get('otp', '')
    new_password = request.form.get('new_password', '')

    if not email or not otp or not new_password:
        flash("All fields required", "danger")
        return redirect(url_for('forgot_password'))

    if otp != "123456":
        flash(
            "Invalid OTP",
            "danger"
        )

        return redirect(
            url_for('forgot_password')
        )

    conn = get_db()

    try:
        hashed_password = generate_password_hash(
            new_password
        )

        conn.execute(
            '''
            UPDATE users
            SET password=?
            WHERE email=?
            ''',
            (
                hashed_password,
                email
            )
        )

        conn.commit()
        flash(
            "Password Reset Successful",
            "success"
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(
        url_for('login')
    )

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    try:
        expense = conn.execute(
            '''
            SELECT *
            FROM expenses
            WHERE expense_id=?
            ''',
            (id,)
        ).fetchone()

        if request.method == 'POST':

            category = request.form.get('category', '').strip()
            amount = request.form.get('amount', '')
            description = request.form.get('description', '').strip()
            date = request.form.get('date', '')

            try:
                amount = float(amount)
                if amount <= 0:
                    flash("Amount must be greater than 0", "danger")
                    return redirect(url_for('edit_expense', id=id))

                conn.execute(
                    '''
                    UPDATE expenses
                    SET category=?,
                        amount=?,
                        description=?,
                        date=?
                    WHERE expense_id=?
                    ''',
                    (
                        category,
                        amount,
                        description,
                        date,
                        id
                    )
                )

                conn.commit()
                flash(
                    "Expense Updated Successfully",
                    "success"
                )

                return redirect(
                    url_for('expenses')
                )
            except ValueError:
                flash("Invalid amount", "danger")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return render_template(
        'edit_expense.html',
        expense=expense
    )

@app.route('/edit_budget/<int:id>', methods=['GET', 'POST'])
def edit_budget(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    try:
        budget = conn.execute(
            '''
            SELECT *
            FROM budgets
            WHERE budget_id=?
            ''',
            (id,)
        ).fetchone()

        if request.method == 'POST':

            category = request.form.get('category', '').strip()
            amount = request.form.get('amount', '')

            try:
                amount = float(amount)
                if amount <= 0:
                    flash("Amount must be greater than 0", "danger")
                    return redirect(url_for('edit_budget', id=id))

                conn.execute(
                    '''
                    UPDATE budgets
                    SET category=?,
                        budget_amount=?
                    WHERE budget_id=?
                    ''',
                    (
                        category,
                        amount,
                        id
                    )
                )

                conn.commit()
                flash(
                    "Budget Updated Successfully",
                    "success"
                )

                return redirect(
                    url_for('budget')
                )
            except ValueError:
                flash("Invalid amount", "danger")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return render_template(
        'edit_budget.html',
        budget=budget
    )

@app.route('/delete_budget/<int:id>')
def delete_budget(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    try:
        conn.execute(
            '''
            DELETE FROM budgets
            WHERE budget_id=?
            ''',
            (id,)
        )

        conn.commit()
        flash(
            "Budget Deleted Successfully",
            "warning"
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(
        url_for('budget')
    )

@app.route('/edit_income/<int:id>', methods=['GET', 'POST'])
def edit_income(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    try:
        income = conn.execute(
            '''
            SELECT *
            FROM income
            WHERE income_id=?
            ''',
            (id,)
        ).fetchone()

        if request.method == 'POST':

            try:
                amount = float(request.form.get('amount', ''))
                if amount <= 0:
                    flash("Amount must be greater than 0", "danger")
                    return redirect(url_for('edit_income', id=id))

                conn.execute(
                    '''
                    UPDATE income
                    SET source=?,
                        amount=?,
                        date=?
                    WHERE income_id=?
                    ''',
                    (
                        request.form.get('source', '').strip(),
                        amount,
                        request.form.get('date', ''),
                        id
                    )
                )

                conn.commit()
                flash(
                    "Income Updated Successfully",
                    "success"
                )

                return redirect(
                    url_for('income')
                )
            except ValueError:
                flash("Invalid amount", "danger")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return render_template(
        'edit_income.html',
        income=income
    )

@app.route('/delete_income/<int:id>')
def delete_income(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    try:
        conn.execute(
            '''
            DELETE FROM income
            WHERE income_id=?
            ''',
            (id,)
        )

        conn.commit()
        flash(
            "Income Deleted Successfully",
            "warning"
        )
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for('income'))

@app.route('/edit_goal/<int:id>', methods=['GET', 'POST'])
def edit_goal(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    try:
        goal = conn.execute(
            '''
            SELECT *
            FROM savings_goals
            WHERE goal_id=?
            ''',
            (id,)
        ).fetchone()

        if request.method == 'POST':

            try:
                target = float(request.form.get('target', ''))
                saved = float(request.form.get('saved', ''))

                if target <= 0 or saved < 0:
                    flash("Enter valid amounts", "danger")
                    return redirect(url_for('edit_goal', id=id))

                conn.execute(
                    '''
                    UPDATE savings_goals
                    SET goal_name=?,
                        target_amount=?,
                        saved_amount=?
                    WHERE goal_id=?
                    ''',
                    (
                        request.form.get('goal', '').strip(),
                        target,
                        saved,
                        id
                    )
                )

                conn.commit()
                flash(
                    "Goal Updated Successfully",
                    "success"
                )
                return redirect(url_for('savings'))
            except ValueError:
                flash("Invalid amounts", "danger")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()

    return render_template(
        'edit_goal.html',
        goal=goal
    )

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Development only - use gunicorn for production
    app.run(debug=False)