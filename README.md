# Library Management System

A library management system built with Flask and SQLite, featuring three roles: admin, librarian, and member.

## Features
- Login/logout aur role-based access
- Book catalog (search, pagination, add, edit, delete, detail page)
- Member management
- Book issue aur return, borrowing limit, late fine
- Fine payment, aur unpaid fine wale member ko naya issue na hona
- Reservations (book wapas aane par "ready" hona)
- Dashboard with stats

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Create a .env file in the project root:

```
SECRET_KEY=any-long-random-string
DATABASE_URL=sqlite:///library.db
```

## Run

```bash
python run.py
```

Open in browser `http://127.0.0.1:5000` .

## first create a admin user

```bash
python -c "from app import create_app, db; from app.models import User; app=create_app(); app.app_context().push(); u=User(name='Admin', email='admin@example.com', role='admin'); u.set_password('CHANGE_ME'); db.session.add(u); db.session.commit()"
```
Run this command only once. Then log in and change the password.

## Project Structure

```
app/            Flask app, models, routes aur templates
run.py          App start karne ki file
requirements.txt
```