import sys, os, traceback
sys.path.insert(0, '/home/claude/project/smart expense and travel expense tracker')
os.chdir('/home/claude/project/smart expense and travel expense tracker')

out = open('/home/claude/audit_results2.txt', 'w')

def log(*a):
    print(*a)
    print(*a, file=out)

try:
    import app as appmod
    client = appmod.app.test_client()

    def show(method, path, **kwargs):
        fn = getattr(client, method)
        r = fn(path, **kwargs)
        log(f"{method.upper():5} {path:35} -> {r.status_code}")
        return r

    # register + login user A
    show('post', '/register', data={'name':'User A','email':'usera@example.com','password':'pass123','confirm':'pass123'})
    show('post', '/login', data={'email':'usera@example.com','password':'pass123'})

    # Add expense
    show('post', '/expenses', data={'category':'Food','amount':'250','description':'Lunch','date':'2026-06-18'})
    r = client.get('/expenses')
    # extract expense_id via app.py db query directly for reliability
    conn = appmod.get_db()
    exp = conn.execute("SELECT * FROM expenses").fetchone()
    log("Expense row:", dict(exp))
    eid = exp['expense_id']
    conn.close()

    # Edit expense
    show('get', f'/edit_expense/{eid}')
    show('post', f'/edit_expense/{eid}', data={'category':'Bills','amount':'300','description':'Updated','date':'2026-06-19'})
    conn = appmod.get_db()
    exp2 = conn.execute("SELECT * FROM expenses WHERE expense_id=?", (eid,)).fetchone()
    log("After edit:", dict(exp2))
    conn.close()

    # Budget with zero -> utilization calc
    show('post', '/budget', data={'category':'Food','amount':'0'})
    r = show('get', '/budget')
    log("Budget page loaded without crash on zero budget:", r.status_code == 200)

    # Savings with target 0
    show('post', '/savings', data={'goal':'Emergency Fund','target':'0','saved':'0'})
    r = show('get', '/savings')
    log("Savings page loaded without crash on zero target:", r.status_code == 200)

    # Delete expense
    show('get', f'/delete_expense/{eid}')
    conn = appmod.get_db()
    exp3 = conn.execute("SELECT * FROM expenses WHERE expense_id=?", (eid,)).fetchone()
    log("After delete, row exists:", exp3 is not None)
    conn.close()

    # Cross-user ownership test: register user B, try to edit/delete user A's income
    show('get', '/logout')
    show('post', '/register', data={'name':'User B','email':'userb@example.com','password':'pass123','confirm':'pass123'})
    show('post', '/login', data={'email':'userb@example.com','password':'pass123'})

    # user A's income (create one first as A)
    show('get', '/logout')
    show('post', '/login', data={'email':'usera@example.com','password':'pass123'})
    show('post', '/income', data={'source':'Salary','amount':'5000','date':'2026-06-01'})
    conn = appmod.get_db()
    inc = conn.execute("SELECT * FROM income WHERE user_id=(SELECT user_id FROM users WHERE email='usera@example.com')").fetchone()
    log("User A income row:", dict(inc))
    income_id = inc['income_id']
    conn.close()

    # switch to B, try editing A's income_id directly
    show('get', '/logout')
    show('post', '/login', data={'email':'userb@example.com','password':'pass123'})
    r = show('post', f'/edit_income/{income_id}', data={'source':'HACKED','amount':'1','date':'2026-01-01'})
    conn = appmod.get_db()
    inc_after = conn.execute("SELECT * FROM income WHERE income_id=?", (income_id,)).fetchone()
    log("SECURITY CHECK -- Income after user B tried editing it (should be unchanged if secure):", dict(inc_after))
    conn.close()

    # missing form field crash test
    r = client.post('/expenses', data={'category':'Food'})  # missing amount/description/date
    log("POST /expenses missing fields -> status:", r.status_code)

except Exception as e:
    log("EXCEPTION:", e)
    traceback.print_exc(file=out)
    traceback.print_exc()

out.close()