# Library Management System

A library management system built with Flask and SQLite. It has three roles: admin, librarian, and member.

## Features

**For everyone (after login)**
- Login and logout with password hashing
- Profile edit and password change
- Book catalog with search, pagination, and detail page
- View and cancel your own reservations

**Admin and Librarian**
- Books: add, edit, and delete (only books with no issue or reservation history)
- Copy management: add new copies, mark copies as damaged, lost, or removed
- Members: add and list
- Issue and return with borrowing limits, due dates, and one renewal (7 days)
- Late fines, plus damage and lost charges (2 times the book price)
- Fines: list and mark as paid
- Reservations list
- Dashboard with stats

**Admin only**
- Users and roles: add, change role, enable or disable
- Audit log: who did what, and when
- Settings: loan days, renewal days, fine per day, fine cap, max books

## Library rules (changeable from Settings)

| Rule | Default |
|---|---|
| Normal loan | 14 days |
| Student loan | 21 days |
| Renewal | 1 time, 7 days |
| Late fine | Rs 2 per day |
| Fine cap | Rs 100 |
| Max books: general / student / staff | 2 / 3 / 5 |

Fixed rules (in code):
- Reference books cannot be taken home, only read in the library
- A member with an unpaid fine cannot issue new books
- Damage and lost charges are 2 times the book price
- Renewal is allowed only if the book has no reservation

## Tech stack

- Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF (CSRF)
- SQLite (development)
- Jinja2 templates
- gunicorn (for deployment)

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
SECRET_KEY=any-long-random-string
DATABASE_URL=sqlite:///library.db
```

To generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Run

```bash
python run.py
```

Open `http://127.0.0.1:5000` in your browser.

## Creating the first admin user

Run this command only once:

```bash
python -c "from app import create_app, db; from app.models import User; app=create_app(); app.app_context().push(); u=User(name='Admin', email='admin@example.com', role='admin'); u.set_password('YOUR_STRONG_PASSWORD'); db.session.add(u); db.session.commit()"
```

Log in and change the password right away. Never write a real password in this file.

## Project structure

```
app/
  __init__.py         Flask app setup, blueprints registered
  models.py           Database tables
  routes.py           Login, logout, dashboard, role_required
  books.py            Book and copy management
  members.py          Member management
  issues.py           Issue, return, renew, lost
  fines.py            Fine list and payment
  reservations.py     Reservations and cancel
  profile.py          Profile and password
  users.py            Users and roles (admin)
  settings_routes.py  Settings page (admin)
  settings.py         Settings helper
  audit.py            Audit log helper
  templates/          HTML templates
run.py                Starts the app
requirements.txt      Package list
```

## Upcoming features

- Backup and restore
- Notifications (due date reminder, ready message)
- Reference books as a separate copy status (currently a flag only)
- Member wishlist, reading goals, reading history, personal notes
- AI features (ISBN auto-fill, semantic search, chatbot, reports)
- Deployment (Render, PostgreSQL)