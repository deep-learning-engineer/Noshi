# Noshi

Noshi is a modern mobile banking backend built with Django. It provides a secure and feature-rich environment for managing users, bank accounts, transactions, achievements, scheduled transfers, and more. The system is designed for extensibility and includes a robust admin panel with detailed action logging for administrators.

## Features
- User registration and authentication
- Bank account management (including co-owners)
- Savings accounts with interest calculation
- Scheduled and recurring transfers
- Transaction history and currency conversion
- Achievements system for user engagement
- Admin panel with detailed action logs

## Quickstart: Running the Backend

### 1. Clone the repository
```bash
git clone https://github.com/deep-learning-engineer/Noshi.git
cd Noshi/backend
```

### 2. Create and activate a virtual environment
**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```
**On Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply migrations
```bash
python manage.py migrate
```

### 5. Create a superuser (admin account)
```bash
python manage.py createsuperuser
```

### 6. Run the development server
```bash
python manage.py runserver
```

The backend will be available at [http://localhost:8000/](http://localhost:8000/)

## Admin Panel
Access the admin panel at [http://localhost:8000/admin/](http://localhost:8000/admin/) using your superuser credentials.

## Notes
- Make sure you have Python 3.10+ installed.
- For production, configure your database and environment variables in `settings.py`.
- All admin actions are logged for security and auditing.

---
For any questions or contributions, please open an issue or pull request.
