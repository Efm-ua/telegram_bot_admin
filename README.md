Telegram Bot Admin Panel

An administrative panel for managing a Telegram bot that allows:
- Tracking user activity
- Managing referral system
- Checking user participation in Telegram group
- Sending messages to users
- Collecting and analyzing statistics

## Technical Stack

- **Programming Language**: Python 3.13
- **Framework**: Django 5.1.2
- **Database**: PostgreSQL
- **Libraries**:
  - python-telegram-bot 21.6 (for Telegram API interaction)
  - python-dotenv (for environment variables)
  - whitenoise (for static files)
  - django-crispy-forms (for forms)

## Project Structure
telegram_bot_admin/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── telegram_admin/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── dashboard/
├── admin.py
├── models.py
├── views.py
├── urls.py
├── forms.py
├── services/
│   ├── status_checker.py
│   └── message_sender.py
├── management/
│   └── commands/
│       ├── import_data.py
│       └── run_bot.py
└── templates/
└── dashboard/
├── base.html
└── index.html
Copy
## Features

### Data Models
- **TelegramUser**: User information
- **Statistics**: General statistics
- **UserActivity**: Activity logging

### Administrative Interface
- User viewing and filtering
- Referral statistics
- User status checking
- Message broadcasting system

### Telegram Integration
- Bot activity checking
- Group membership verification
- Mass messaging

### Statistics and Analytics
- Active users count
- Referral statistics
- Language preferences analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Efm-ua/telegram_bot_admin.git
cd telegram_bot_admin

Create virtual environment:

bash
Copypython -m venv venv
source venv/Scripts/activate  # for Windows

Install dependencies:

bash
Copy
pip install -r requirements.txt

Set up environment variables:
Create .env file and add:

Copy
DEBUG=True
SECRET_KEY=your-secret-key
TELEGRAM_BOT_TOKEN=your-bot-token

Apply migrations:

bash
Copy
python manage.py migrate

Create superuser:

bash
Copy
python manage.py createsuperuser

Run server:

bashCopypython manage.py runserver
Technical Solutions
Telegram API Limitations

Implemented batch request processing
Added delays between requests
RetryAfter error handling

Asynchronous Processing

Proper event loop handling in Python 3.13
Correct async operation completion

Scalability

Database query optimization
Efficient handling of large user bases

Development Plans

Adding new metrics and statistics
Expanding messaging functionality
Improving UI/UX of admin panel
Adding notification system

Contributing

Fork the repository
Create your feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add some amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request

Authors

Yevgeniy Melnyk - Initial work - Efm-ua

Support
For support, email ym@ahimsa.coop or create an issue in the repository.
