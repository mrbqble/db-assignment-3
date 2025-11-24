# Caregiving Service Platform

A Flask-based web application for connecting caregivers with members who need caregiving services. This project was developed as part of CSCI341 Database Assignment 3.

## Features

- **User Management**: Register and manage users who can be either caregivers or members
- **Caregiver Profiles**: Create and manage caregiver profiles with hourly rates, caregiving types, and availability
- **Member Profiles**: Create and manage member profiles with house rules and dependent descriptions
- **Job Postings**: Members can post jobs with specific caregiving requirements
- **Job Applications**: Caregivers can apply to posted jobs
- **Appointments**: Schedule and manage appointments between caregivers and members
- **Address Management**: Store and manage member addresses
- **Database Queries**: Comprehensive SQL queries for data analysis and reporting

## Technology Stack

- **Backend**: Flask 3.0.0
- **Database**: MySQL (via PyMySQL)
- **ORM**: SQLAlchemy 2.0+
- **Environment Management**: python-dotenv

## Project Structure

```
db-assignment-3/
├── app.py                 # Main Flask application
├── models.py              # SQLAlchemy database models
├── script.py              # Database initialization script
├── wsgi.py                # WSGI configuration for deployment
├── requirements.txt       # Python dependencies
├── env.example            # Environment variables template
├── DEPLOYMENT.md          # Deployment guide for PythonAnywhere
├── db/                    # SQL query files
│   ├── db.sql            # Main database schema
│   ├── indexes.sql       # Database indexes
│   └── *.sql             # Various query files
└── templates/             # HTML templates
    ├── base.html
    ├── home.html
    ├── users.html
    ├── caregivers.html
    ├── members.html
    ├── jobs.html
    ├── job_applications.html
    ├── appointments.html
    └── ...
```

## Installation

### Prerequisites

- Python 3.10 or higher
- MySQL database server
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd db-assignment-3
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   - Copy `env.example` to `.env`
   - Update the `.env` file with your database credentials:
     ```
     DATABASE_URL=mysql+pymysql://username:password@host:port/database_name
     FLASK_SECRET_KEY=your-secret-key-here
     ```

6. **Initialize the database**
   ```bash
   python script.py
   ```
   This will create all necessary tables and insert sample data.

## Running the Application

### Development Mode

```bash
python app.py
```

Or using Flask's development server:

```bash
flask run
```

The application will be available at `http://localhost:5000`

### Production Mode

For production deployment, refer to `DEPLOYMENT.md` for PythonAnywhere deployment instructions.

## Database Schema

The application uses the following main entities:

- **Users**: Base user information (email, name, phone, etc.)
- **Caregiver**: Caregiver-specific information (hourly rate, caregiving type, photo)
- **Member**: Member-specific information (house rules, dependent description)
- **Address**: Member addresses
- **Job**: Job postings by members
- **JobApplication**: Applications by caregivers to jobs
- **Appointment**: Scheduled appointments between caregivers and members

### Caregiving Types

- `babysitter`
- `caregiver for elderly`
- `playmate for children`

### Appointment Statuses

- `pending`
- `accepted`
- `declined`

## Usage

### Creating Users

1. Navigate to the Users page
2. Click "Create New User"
3. Fill in the required information:
   - Email (must be unique)
   - Given name and surname
   - Phone number (must be unique)
   - Password (must meet security requirements)
   - Optional: City and profile description

### Creating Caregivers

1. First, create a user account
2. Navigate to the Caregivers page
3. Click "Create New Caregiver"
4. Select the user and fill in:
   - Caregiving type
   - Hourly rate
   - Optional: Photo URL and gender

### Creating Members

1. First, create a user account
2. Navigate to the Members page
3. Click "Create New Member"
4. Select the user and fill in:
   - House rules
   - Dependent description
5. Add an address for the member

### Posting Jobs

1. As a member, navigate to the Jobs page
2. Click "Create New Job"
3. Fill in:
   - Required caregiving type
   - Other requirements
   - Date posted (defaults to today)

### Applying to Jobs

1. As a caregiver, navigate to Job Applications
2. Click "Create New Job Application"
3. Select a job to apply to

### Managing Appointments

1. Navigate to the Appointments page
2. Create new appointments with:
   - Caregiver and member selection
   - Date (must be at least tomorrow)
   - Time
   - Work hours (1-24 hours)
   - Status (pending, accepted, declined)

## Validation Rules

### Email
- Must be a valid email format
- Must be unique

### Phone Number
- Must contain 7-15 digits
- Can include spaces, hyphens, parentheses, or + sign
- Must be unique

### Password
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### Hourly Rate
- Must be a positive number

### Work Hours
- Must be a positive number
- Cannot exceed 24 hours

### Appointment Date
- Must be at least tomorrow (cannot be today or in the past)

## SQL Queries

The project includes various SQL query files in the `db/` directory:

- `db.sql`: Main database schema
- `indexes.sql`: Database indexes for performance
- `1.sql` through `8.sql`: Various query exercises

Run queries using the `script.py` file or execute them directly in your MySQL client.

## Deployment

For detailed deployment instructions, see `DEPLOYMENT.md`. The application is configured for deployment on PythonAnywhere.

## Troubleshooting

### Database Connection Issues

- Verify your `DATABASE_URL` in `.env` is correct
- Ensure MySQL server is running
- Check database credentials and permissions

### Import Errors

- Make sure virtual environment is activated
- Verify all dependencies are installed: `pip list`
- Check that you're using the correct Python version

### Application Errors

- Check Flask error logs
- Verify `.env` file exists and is properly configured
- Ensure database tables are created (run `script.py`)

## License

This project was created for educational purposes as part of CSCI341 Database Systems course.

## Contributors

- Developed as part of CSCI341 Database Assignment 3

