from models import db, Users, Caregiver, Member, Address, Job, Appointment, JobApplication, CAREGIVING_TYPES, APPOINTMENT_STATUSES
import os
import re
from flask import Flask, render_template, flash, redirect, url_for, request
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import ProgrammingError, IntegrityError
from sqlalchemy import exists, select, or_, func
from datetime import date, time, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Validation patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)]{7,20}$')


def validate_email(email: str) -> tuple[bool, str | None]:
    """Validate email format"""
    if not email:
        return False, "Email is required."
    if not EMAIL_PATTERN.match(email):
        return False, "Please enter a valid email address (e.g., user@example.com)."
    return True, None


def validate_phone_number(phone: str) -> tuple[bool, str | None]:
    """Validate phone number format"""
    if not phone:
        return False, "Phone number is required."
    # Remove common formatting characters for validation
    digits_only = re.sub(r'[\s\-\+\(\)]', '', phone)
    if len(digits_only) < 7 or len(digits_only) > 15:
        return False, "Phone number must contain 7-15 digits."
    if not PHONE_PATTERN.match(phone):
        return False, "Please enter a valid phone number (digits, spaces, hyphens, parentheses, or + sign)."
    return True, None


def validate_password(password: str) -> tuple[bool, str | None]:
    """Validate password format"""
    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;':\",./<>?)."
    return True, None


def validate_hourly_rate(rate_str: str) -> tuple[bool, float | None, str | None]:
    """Validate hourly rate - returns (is_valid, rate_value, error_message)"""
    if not rate_str:
        return False, None, "Hourly rate is required."
    try:
        rate_value = float(rate_str)
        if rate_value <= 0:
            return False, None, "Hourly rate must be a positive number."
        return True, rate_value, None
    except ValueError:
        return False, None, "Hourly rate must be a valid number."


def validate_work_hours(hours_str: str) -> tuple[bool, float | None, str | None]:
    """Validate work hours - returns (is_valid, hours_value, error_message)"""
    if not hours_str:
        return False, None, "Work hours is required."
    try:
        hours_value = float(hours_str)
        if hours_value <= 0:
            return False, None, "Work hours must be a positive number."
        if hours_value > 24:
            return False, None, "Work hours cannot exceed 24 hours."
        return True, hours_value, None
    except ValueError:
        return False, None, "Work hours must be a valid number."


def validate_appointment_date(appointment_date: date) -> tuple[bool, str | None]:
    """Validate that appointment date is at least tomorrow - returns (is_valid, error_message)"""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    if appointment_date <= today:
        return False, "Appointment date must be at least tomorrow (later than today)."

    return True, None


def check_email_uniqueness(email: str, exclude_user_id: int | None = None) -> tuple[bool, str | None]:
    """Check if email is unique - returns (is_unique, error_message)"""
    query = Users.query.filter(Users.email == email)
    if exclude_user_id:
        query = query.filter(Users.user_id != exclude_user_id)
    existing: Users | None = query.first()
    if existing:
        return False, "Email already exists. Please use a different email."
    return True, None


def check_phone_uniqueness(phone: str, exclude_user_id: int | None = None) -> tuple[bool, str | None]:
    """Check if phone number is unique - returns (is_unique, error_message)"""
    query = Users.query.filter(Users.phone_number == phone)
    if exclude_user_id:
        query = query.filter(Users.user_id != exclude_user_id)
    existing = query.first()
    if existing:
        return False, "Phone number already exists. Please use a different phone number."
    return True, None


def reset_user_sequence() -> bool:
    """Reset auto-increment for MySQL - MySQL handles AUTO_INCREMENT automatically"""
    # MySQL handles AUTO_INCREMENT automatically, so this function is kept
    # for compatibility but does nothing. AUTO_INCREMENT will automatically
    # use the next available ID based on the maximum existing ID.
    return True


def get_form_field(field: str, default: str = '') -> str:
    """Extract and strip a form field value"""
    return request.form.get(field, default).strip()


def get_form_fields(*fields: str, default: str = '') -> dict[str, str]:
    """Extract multiple form fields at once"""
    return {field: get_form_field(field, default) for field in fields}


def apply_date_range_filter(query, field, from_date: str | None, to_date: str | None):
    """Apply date range filter to a query"""
    if from_date:
        try:
            from_date_obj = date.fromisoformat(from_date)
            query = query.filter(field >= from_date_obj)
        except ValueError:
            pass  # Ignore invalid date values

    if to_date:
        try:
            to_date_obj = date.fromisoformat(to_date)
            query = query.filter(field <= to_date_obj)
        except ValueError:
            pass  # Ignore invalid date values

    return query


def apply_numeric_range_filter(query, field, min_value: str | None, max_value: str | None):
    """Apply numeric range filter to a query"""
    if min_value:
        try:
            min_val = float(min_value)
            query = query.filter(field >= min_val)
        except ValueError:
            pass  # Ignore invalid values

    if max_value:
        try:
            max_val = float(max_value)
            query = query.filter(field <= max_val)
        except ValueError:
            pass  # Ignore invalid values

    return query


# Database configuration
database_url = os.getenv('DATABASE_URL')
# Convert postgresql:// to mysql+pymysql:// if needed (for backward compatibility)
if database_url and database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'mysql+pymysql://', 1)
elif database_url and database_url.startswith('postgresql+psycopg://'):
    database_url = database_url.replace(
        'postgresql+psycopg://', 'mysql+pymysql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv(
    'FLASK_SECRET_KEY', '2-python-projects-in-a-row-i-am-sick-of-this-shit')

# Initialize SQLAlchemy with app
db.init_app(app)


# Flask error handler for database errors
@app.errorhandler(ProgrammingError)
def handle_programming_error(e: ProgrammingError):
    """Handle database programming errors (e.g., missing tables)"""
    if 'does not exist' in str(e) or 'UndefinedTable' in str(e):
        return render_template('error.html',
                               message='Database tables not found. Please initialize the database first.',
                               action_url='/init-db',
                               action_text='Initialize Database'), 500
    raise


@app.route('/')
def home():
    """Dashboard home page with statistics"""
    try:
        # Get statistics (counts are already optimized at database level)
        stats = {
            'users': Users.query.count(),
            'caregivers': Caregiver.query.count(),
            'members': Member.query.count(),
            'addresses': Address.query.count(),
            'jobs': Job.query.count(),
            'appointments': Appointment.query.count(),
            'job_applications': JobApplication.query.count()
        }

        recent_users = Users.query.options(
            joinedload(Users.caregiver),
            joinedload(Users.member)
        ).order_by(Users.user_id.desc()).limit(5).all()
        recent_appointments = Appointment.query.options(
            joinedload(Appointment.caregiver).joinedload(Caregiver.user),
            joinedload(Appointment.member).joinedload(Member.user)
        ).order_by(Appointment.appointment_date.desc()).limit(5).all()

        return render_template('home.html', stats=stats,
                               recent_users=recent_users,
                               recent_appointments=recent_appointments)
    except Exception as e:
        # If tables don't exist, show helpful message
        error_msg = str(e)
        if 'does not exist' in error_msg or 'UndefinedTable' in error_msg:
            return render_template('error.html',
                                   message='Database tables not found. Please initialize the database first.',
                                   action_url='/init-db',
                                   action_text='Initialize Database')
        return render_template('error.html',
                               message=f'Database error: {error_msg}',
                               action_url='/',
                               action_text='Go Home')


@app.route('/users')
def users():
    """Display all users with filtering"""
    # Get filter parameters
    city_filter = request.args.get('city', '')
    status_filter = request.args.get('status', '')
    search_term = request.args.get('search', '').strip()

    # Build query
    query = Users.query.options(
        joinedload(Users.caregiver),
        joinedload(Users.member)
    )

    # Apply search filter (name, email, or phone number)
    if search_term and len(search_term) > 0:
        search_pattern = f'%{search_term}%'
        # Use LOWER() for case-insensitive search (MySQL compatible)
        query = query.filter(
            or_(
                func.lower(Users.given_name).like(func.lower(search_pattern)),
                func.lower(Users.surname).like(func.lower(search_pattern)),
                func.lower(Users.email).like(func.lower(search_pattern)),
                func.lower(Users.phone_number).like(func.lower(search_pattern))
            )
        )

    # Apply city filter
    if city_filter:
        query = query.filter(Users.city == city_filter)

    # Apply status filter using EXISTS subqueries
    if status_filter == 'caregiver':
        query = query.filter(exists(select(1).where(
            Caregiver.caregiver_user_id == Users.user_id)))
    elif status_filter == 'member':
        query = query.filter(exists(select(1).where(
            Member.member_user_id == Users.user_id)))
    elif status_filter == 'both':
        query = query.filter(
            exists(select(1).where(
                Caregiver.caregiver_user_id == Users.user_id)),
            exists(select(1).where(
                Member.member_user_id == Users.user_id))
        )
    elif status_filter == 'none':
        query = query.filter(
            ~exists(select(1).where(
                Caregiver.caregiver_user_id == Users.user_id)),
            ~exists(select(1).where(
                Member.member_user_id == Users.user_id))
        )

    users_list = query.order_by(Users.user_id).all()

    # Get unique cities for filter dropdown (optimized with distinct)
    cities = sorted([c[0] for c in db.session.query(
        Users.city).distinct().filter(Users.city.isnot(None)).all()])

    return render_template('users.html', users=users_list, cities=cities, selected_city=city_filter, selected_status=status_filter, search_term=search_term)


@app.route('/caregivers')
def caregivers():
    """Display all caregivers with filtering"""
    # Get filter parameters
    caregiving_type_filter = request.args.get('caregiving_type', '')
    city_filter = request.args.get('city', '')
    gender_filter = request.args.get('gender', '')
    min_rate = request.args.get('min_rate', '')
    max_rate = request.args.get('max_rate', '')

    # Build query with eager loading
    query = Caregiver.query.options(
        joinedload(Caregiver.user),
        joinedload(Caregiver.appointments),
        joinedload(Caregiver.job_applications)
    )

    # Apply filters
    if caregiving_type_filter:
        query = query.filter(
            Caregiver.caregiving_type == caregiving_type_filter)

    if city_filter:
        query = query.join(Users).filter(
            Users.city == city_filter)

    if gender_filter:
        query = query.filter(Caregiver.gender == gender_filter)

    # Apply hourly rate range filters
    if min_rate:
        try:
            min_rate_value = float(min_rate)
            query = query.filter(
                Caregiver.hourly_rate >= min_rate_value)
        except ValueError:
            pass  # Ignore invalid min_rate values

    if max_rate:
        try:
            max_rate_value = float(max_rate)
            query = query.filter(
                Caregiver.hourly_rate <= max_rate_value)
        except ValueError:
            pass  # Ignore invalid max_rate values

    caregivers_list = query.order_by(
        Caregiver.caregiver_user_id).all()

    # Get unique values for filter dropdowns (optimized with distinct)
    cities = sorted([c[0] for c in db.session.query(Users.city).join(
        Caregiver, Caregiver.caregiver_user_id == Users.user_id
    ).distinct().filter(Users.city.isnot(None)).all()])
    genders = sorted([g[0] for g in db.session.query(
        Caregiver.gender).distinct().filter(Caregiver.gender.isnot(None)).all()])

    return render_template('caregivers.html',
                           caregivers=caregivers_list,
                           caregiving_types=CAREGIVING_TYPES,
                           cities=cities,
                           genders=genders,
                           selected_caregiving_type=caregiving_type_filter,
                           selected_city=city_filter,
                           selected_gender=gender_filter,
                           min_rate=min_rate,
                           max_rate=max_rate)


@app.route('/members')
def members():
    """Display all members"""
    members_list = Member.query.options(
        joinedload(Member.user),
        joinedload(Member.address),
        joinedload(Member.jobs),
        joinedload(Member.appointments)
    ).order_by(Member.member_user_id).all()
    return render_template('members.html', members=members_list)


@app.route('/addresses')
def addresses():
    """Display all addresses"""
    addresses_list = Address.query.options(
        joinedload(Address.member).joinedload(Member.user)
    ).order_by(Address.member_user_id).all()
    return render_template('addresses.html', addresses=addresses_list)


@app.route('/jobs')
def jobs():
    """Display all jobs with filtering"""
    # Get filter parameters
    caregiving_type_filter = request.args.get('caregiving_type', '')
    town_filter = request.args.get('town', '')
    member_id_filter = request.args.get('member_id', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    # Build query
    query = Job.query.options(
        joinedload(Job.member).joinedload(Member.user),
        joinedload(Job.member).joinedload(Member.address),
        joinedload(Job.applications)
    )

    # Apply caregiving type filter
    if caregiving_type_filter:
        query = query.filter(
            Job.required_caregiving_type == caregiving_type_filter)

    # Apply town filter
    if town_filter:
        query = query.join(Member, Job.member_user_id == Member.member_user_id).join(
            Address, Member.member_user_id == Address.member_user_id).filter(
            Address.town == town_filter)

    # Apply member ID filter
    if member_id_filter:
        try:
            member_id_value = int(member_id_filter)
            query = query.filter(
                Job.member_user_id == member_id_value)
        except ValueError:
            pass  # Ignore invalid member_id values

    # Apply date filters
    query = apply_date_range_filter(
        query, Job.date_posted, from_date, to_date)

    jobs_list = query.order_by(Job.job_id).all()

    # Get unique values for filter dropdowns (optimized with distinct)
    towns = sorted([t[0] for t in db.session.query(Address.town).join(
        Member, Address.member_user_id == Member.member_user_id
    ).join(Job, Job.member_user_id == Member.member_user_id).distinct().all()])

    # Get unique member IDs with names (optimized)
    member_ids = sorted([(m.member_user_id, f"{u.given_name} {u.surname}")
                         for m, u in db.session.query(Member, Users).join(
                             Users, Member.member_user_id == Users.user_id
    ).join(Job, Job.member_user_id == Member.member_user_id).distinct().all()],
        key=lambda x: x[0])

    # Get unique dates from jobs (optimized with distinct)
    available_dates = sorted(
        [d[0] for d in db.session.query(Job.date_posted).distinct().all()])

    return render_template('jobs.html',
                           jobs=jobs_list,
                           caregiving_types=CAREGIVING_TYPES,
                           towns=towns,
                           member_ids=member_ids,
                           available_dates=available_dates,
                           selected_caregiving_type=caregiving_type_filter,
                           selected_town=town_filter,
                           member_id=member_id_filter,
                           from_date=from_date,
                           to_date=to_date)


@app.route('/job-applications')
def job_applications():
    """Display all job applications with filtering"""
    try:
        with app.app_context():
            # Get filter parameters
            caregiving_type_filter = request.args.get('caregiving_type', '')
            caregiver_id_filter = request.args.get('caregiver_id', '')
            member_id_filter = request.args.get('member_id', '')
            job_id_filter = request.args.get('job_id', '')
            from_date = request.args.get('from_date', '')
            to_date = request.args.get('to_date', '')

            # Build query
            query = JobApplication.query.options(
                joinedload(JobApplication.caregiver).joinedload(
                    Caregiver.user),
                joinedload(JobApplication.job).joinedload(
                    Job.member).joinedload(Member.user)
            )

            # Apply caregiving type filter using subquery
            if caregiving_type_filter:
                query = query.filter(
                    exists(select(1).where(
                        Job.job_id == JobApplication.job_id,
                        Job.required_caregiving_type == caregiving_type_filter
                    ))
                )

            # Apply caregiver ID filter
            if caregiver_id_filter:
                try:
                    caregiver_id_value = int(caregiver_id_filter)
                    query = query.filter(
                        JobApplication.caregiver_user_id == caregiver_id_value)
                except ValueError:
                    pass  # Ignore invalid caregiver_id values

            # Apply member ID filter using subquery
            if member_id_filter:
                try:
                    member_id_value = int(member_id_filter)
                    query = query.filter(
                        exists(select(1).where(
                            Job.job_id == JobApplication.job_id,
                            Job.member_user_id == member_id_value
                        ))
                    )
                except ValueError:
                    pass  # Ignore invalid member_id values

            # Apply job ID filter
            if job_id_filter:
                try:
                    job_id_value = int(job_id_filter)
                    query = query.filter(JobApplication.job_id == job_id_value)
                except ValueError:
                    pass  # Ignore invalid job_id values

            # Apply date filters
            query = apply_date_range_filter(
                query, JobApplication.date_applied, from_date, to_date)

            applications = query.order_by(
                JobApplication.date_applied.desc()).all()

            # Get available IDs for dropdowns (optimized with distinct)
            # Get unique caregiver IDs with names
            caregiver_ids = sorted([(c.caregiver_user_id, f"{u.given_name} {u.surname}")
                                   for c, u in db.session.query(Caregiver, Users).join(
                                       Users, Caregiver.caregiver_user_id == Users.user_id
            ).join(JobApplication, JobApplication.caregiver_user_id == Caregiver.caregiver_user_id).distinct().all()],
                key=lambda x: x[0])

            # Get unique member IDs with names
            member_ids = sorted([(m.member_user_id, f"{u.given_name} {u.surname}")
                                for m, u in db.session.query(Member, Users).join(
                                    Users, Member.member_user_id == Users.user_id
            ).join(Job, Job.member_user_id == Member.member_user_id).join(
                                    JobApplication, JobApplication.job_id == Job.job_id
            ).distinct().all()],
                key=lambda x: x[0])

            # Get unique job IDs
            job_ids = sorted([j[0] for j in db.session.query(
                JobApplication.job_id).distinct().all()])

            # Get unique dates from job applications (optimized)
            available_dates = sorted([d[0] for d in db.session.query(
                JobApplication.date_applied).distinct().all()])

            return render_template('job_applications.html',
                                   job_applications=applications,
                                   caregiving_types=CAREGIVING_TYPES,
                                   caregiver_ids=caregiver_ids,
                                   member_ids=member_ids,
                                   job_ids=job_ids,
                                   available_dates=available_dates,
                                   selected_caregiving_type=caregiving_type_filter,
                                   caregiver_id=caregiver_id_filter,
                                   member_id=member_id_filter,
                                   job_id=job_id_filter,
                                   from_date=from_date,
                                   to_date=to_date)
    except ProgrammingError as e:
        if 'does not exist' in str(e) or 'UndefinedTable' in str(e):
            return render_template('error.html',
                                   message='Database tables not found. Please initialize the database first.',
                                   action_url='/init-db',
                                   action_text='Initialize Database'), 500
        raise


@app.route('/appointments')
def appointments():
    """Display all appointments with filtering"""
    # Get filter parameters
    caregiver_id_filter = request.args.get('caregiver_id', '')
    member_id_filter = request.args.get('member_id', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    from_time = request.args.get('from_time', '')
    to_time = request.args.get('to_time', '')
    min_hours = request.args.get('min_hours', '')
    max_hours = request.args.get('max_hours', '')
    status_filter = request.args.get('status', '')

    # Build query
    query = Appointment.query.options(
        joinedload(Appointment.caregiver).joinedload(
            Caregiver.user),
        joinedload(Appointment.member).joinedload(Member.user)
    )

    # Apply caregiver ID filter
    if caregiver_id_filter:
        try:
            caregiver_id_value = int(caregiver_id_filter)
            query = query.filter(
                Appointment.caregiver_user_id == caregiver_id_value)
        except ValueError:
            pass  # Ignore invalid caregiver_id values

    # Apply member ID filter
    if member_id_filter:
        try:
            member_id_value = int(member_id_filter)
            query = query.filter(
                Appointment.member_user_id == member_id_value)
        except ValueError:
            pass  # Ignore invalid member_id values

    # Apply date filters
    query = apply_date_range_filter(
        query, Appointment.appointment_date, from_date, to_date)

    # Apply time filters
    if from_time:
        try:
            # Parse HH:MM format
            hour, minute = map(int, from_time.split(':'))
            from_time_obj = time(hour, minute)
            query = query.filter(
                Appointment.appointment_time >= from_time_obj)
        except (ValueError, AttributeError):
            pass  # Ignore invalid time values

    if to_time:
        try:
            # Parse HH:MM format
            hour, minute = map(int, to_time.split(':'))
            to_time_obj = time(hour, minute)
            query = query.filter(
                Appointment.appointment_time <= to_time_obj)
        except (ValueError, AttributeError):
            pass  # Ignore invalid time values

    # Apply work hours filters
    query = apply_numeric_range_filter(
        query, Appointment.work_hours, min_hours, max_hours)

    # Apply status filter
    if status_filter:
        query = query.filter(
            Appointment.status == status_filter)

    appointments_list = query.order_by(
        Appointment.appointment_date.desc()).all()

    # Get available values for filter dropdowns (optimized with distinct)
    # Get unique caregiver IDs with names
    caregiver_ids = sorted([(c.caregiver_user_id, f"{u.given_name} {u.surname}")
                           for c, u in db.session.query(Caregiver, Users).join(
                               Users, Caregiver.caregiver_user_id == Users.user_id
    ).join(Appointment, Appointment.caregiver_user_id == Caregiver.caregiver_user_id).distinct().all()],
        key=lambda x: x[0])

    # Get unique member IDs with names
    member_ids = sorted([(m.member_user_id, f"{u.given_name} {u.surname}")
                        for m, u in db.session.query(Member, Users).join(
                            Users, Member.member_user_id == Users.user_id
    ).join(Appointment, Appointment.member_user_id == Member.member_user_id).distinct().all()],
        key=lambda x: x[0])

    # Get unique dates from appointments (optimized)
    available_dates = sorted([d[0] for d in db.session.query(
        Appointment.appointment_date).distinct().all()])

    # Generate time options with 30-minute intervals (00:00 to 23:30)
    available_times = []
    for hour in range(24):
        for minute in [0, 30]:
            available_times.append(time(hour, minute))

    return render_template('appointments.html',
                           appointments=appointments_list,
                           caregiver_ids=caregiver_ids,
                           member_ids=member_ids,
                           available_dates=available_dates,
                           available_times=available_times,
                           appointment_statuses=APPOINTMENT_STATUSES,
                           caregiver_id=caregiver_id_filter,
                           member_id=member_id_filter,
                           from_date=from_date,
                           to_date=to_date,
                           from_time=from_time,
                           to_time=to_time,
                           min_hours=min_hours,
                           max_hours=max_hours,
                           selected_status=status_filter)


# ==================== USER ROUTES ====================

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Edit a user"""
    try:
        with app.app_context():
            user = Users.query.options(
                joinedload(Users.caregiver),
                joinedload(Users.member).joinedload(Member.address)
            ).get_or_404(user_id)

            if request.method == 'POST':
                new_email = request.form.get('email', '').strip()
                new_phone_number = request.form.get('phone_number', '').strip()

                if not new_phone_number:
                    flash('Phone number is required.', 'error')
                    return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                # Check if email is being changed and already exists
                if new_email != user.email:
                    existing_email = Users.query.filter(
                        Users.email == new_email).first()
                    if existing_email:
                        flash(
                            'Email already exists. Please use a different email.', 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                # Check if phone number is being changed and already exists
                if new_phone_number != user.phone_number:
                    existing_phone = Users.query.filter(
                        Users.phone_number == new_phone_number).first()
                    if existing_phone:
                        flash(
                            'Phone number already exists. Please use a different phone number.', 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                # Check if user wants to be a caregiver or member
                is_caregiver = request.form.get('is_caregiver') == 'on'
                is_member = request.form.get('is_member') == 'on'

                # Initialize caregiver variables
                caregiving_type = None
                hourly_rate_value = None

                # Validate caregiver fields if caregiver is selected
                if is_caregiver:
                    caregiving_type = request.form.get(
                        'caregiving_type', '').strip()
                    hourly_rate = request.form.get('hourly_rate', '').strip()

                    if not caregiving_type:
                        flash(
                            'Caregiving type is required when creating a caregiver.', 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                    if caregiving_type not in CAREGIVING_TYPES:
                        flash(
                            f'Invalid caregiving type. Must be one of: {", ".join(CAREGIVING_TYPES)}', 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                    if not hourly_rate:
                        flash(
                            'Hourly rate is required when creating a caregiver.', 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                    is_valid, hourly_rate_value, error_msg = validate_hourly_rate(
                        hourly_rate)
                    if not is_valid:
                        flash(error_msg, 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                # Validate member address fields if member is selected
                if is_member:
                    house_number = request.form.get('house_number', '').strip()
                    street = request.form.get('street', '').strip()
                    town = request.form.get('town', '').strip()

                    if not house_number:
                        flash(
                            'House number is required when creating a member.', 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                    if not street:
                        flash('Street is required when creating a member.', 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                    if not town:
                        flash('Town is required when creating a member.', 'error')
                        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                # Update user fields
                # Validate password
                password = request.form.get('password', '').strip()
                password_valid, password_error = validate_password(password)
                if not password_valid:
                    flash(password_error, 'error')
                    return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)

                user.email = new_email
                user.given_name = request.form.get('given_name', '').strip()
                user.surname = request.form.get('surname', '').strip()
                user.city = request.form.get('city', '').strip() or None
                user.phone_number = new_phone_number
                user.profile_description = request.form.get(
                    'profile_description', '').strip() or None
                user.password = password

                # Handle caregiver
                if is_caregiver:
                    if user.caregiver:
                        # Update existing caregiver
                        user.caregiver.photo = request.form.get(
                            'photo', '').strip() or None
                        user.caregiver.gender = request.form.get(
                            'gender', '').strip() or None
                        user.caregiver.caregiving_type = caregiving_type
                        user.caregiver.hourly_rate = hourly_rate_value
                    else:
                        # Create new caregiver
                        new_caregiver = Caregiver(
                            caregiver_user_id=user.user_id,
                            photo=request.form.get(
                                'photo', '').strip() or None,
                            gender=request.form.get(
                                'gender', '').strip() or None,
                            caregiving_type=caregiving_type,
                            hourly_rate=hourly_rate_value
                        )
                        db.session.add(new_caregiver)
                else:
                    # Remove caregiver if exists
                    if user.caregiver:
                        db.session.delete(user.caregiver)

                # Handle member
                if is_member:
                    house_number = request.form.get('house_number', '').strip()
                    street = request.form.get('street', '').strip()
                    town = request.form.get('town', '').strip()

                    if user.member:
                        # Update existing member
                        user.member.house_rules = request.form.get(
                            'house_rules', '').strip() or None
                        user.member.dependent_description = request.form.get(
                            'dependent_description', '').strip() or None

                        # Update or create address
                        if user.member.address:
                            user.member.address.house_number = house_number
                            user.member.address.street = street
                            user.member.address.town = town
                        else:
                            new_address = Address(
                                member_user_id=user.member.member_user_id,
                                house_number=house_number,
                                street=street,
                                town=town
                            )
                            db.session.add(new_address)
                    else:
                        # Create new member
                        new_member = Member(
                            member_user_id=user.user_id,
                            house_rules=request.form.get(
                                'house_rules', '').strip() or None,
                            dependent_description=request.form.get(
                                'dependent_description', '').strip() or None
                        )
                        db.session.add(new_member)
                        db.session.flush()

                        # Create address
                        new_address = Address(
                            member_user_id=new_member.member_user_id,
                            house_number=house_number,
                            street=street,
                            town=town
                        )
                        db.session.add(new_address)
                else:
                    # Remove member if exists (cascade will delete address)
                    if user.member:
                        db.session.delete(user.member)

                db.session.commit()
                flash('User updated successfully!', 'success')
                return redirect(url_for('users'))

            # GET request - load existing caregiver/member data
            return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)
    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e).lower()
        if 'email' in error_msg and ('unique' in error_msg or 'duplicate' in error_msg):
            flash('Email already exists. Please use a different email.', 'error')
        elif 'phone_number' in error_msg or ('phone' in error_msg and ('unique' in error_msg or 'duplicate' in error_msg)):
            flash(
                'Phone number already exists. Please use a different phone number.', 'error')
        else:
            flash(f'Error updating user: {str(e)}', 'error')
        return render_template('edit_user.html', user=user, caregiving_types=CAREGIVING_TYPES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'error')
        return redirect(url_for('users'))


@app.route('/users/create', methods=['GET', 'POST'])
def create_user():
    """Create a new user"""
    try:
        with app.app_context():
            if request.method == 'POST':
                # Get and clean email
                email = request.form.get('email', '').strip()

                # Validate email format
                email_valid, email_error = validate_email(email)
                if not email_valid:
                    flash(email_error, 'error')
                    return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                # Get and clean phone number
                phone_number = request.form.get('phone_number', '').strip()

                # Validate phone number format
                phone_valid, phone_error = validate_phone_number(phone_number)
                if not phone_valid:
                    flash(phone_error, 'error')
                    return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                # Check if email already exists
                is_unique, error_msg = check_email_uniqueness(email)
                if not is_unique:
                    flash(error_msg, 'error')
                    return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                # Check if phone number already exists
                is_unique, error_msg = check_phone_uniqueness(phone_number)
                if not is_unique:
                    flash(error_msg, 'error')
                    return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                # Check if user wants to be a caregiver or member
                is_caregiver = request.form.get('is_caregiver') == 'on'
                is_member = request.form.get('is_member') == 'on'

                # Initialize caregiver variables
                caregiving_type = None
                hourly_rate_value = None

                # Validate caregiver fields if caregiver is selected
                if is_caregiver:
                    caregiving_type = request.form.get(
                        'caregiving_type', '').strip()
                    hourly_rate = request.form.get('hourly_rate', '').strip()

                    if not caregiving_type:
                        flash(
                            'Caregiving type is required when creating a caregiver.', 'error')
                        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                    if caregiving_type not in CAREGIVING_TYPES:
                        flash(
                            f'Invalid caregiving type. Must be one of: {", ".join(CAREGIVING_TYPES)}', 'error')
                        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                    if not hourly_rate:
                        flash(
                            'Hourly rate is required when creating a caregiver.', 'error')
                        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                    try:
                        hourly_rate_value = float(hourly_rate)
                        if hourly_rate_value < 0:
                            flash('Hourly rate must be a positive number.', 'error')
                            return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)
                    except ValueError:
                        flash('Hourly rate must be a valid number.', 'error')
                        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                # Validate password
                password = request.form.get('password', '').strip()
                password_valid, password_error = validate_password(password)
                if not password_valid:
                    flash(password_error, 'error')
                    return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                # Create new user
                new_user = Users(
                    email=email,
                    given_name=request.form.get('given_name', '').strip(),
                    surname=request.form.get('surname', '').strip(),
                    city=request.form.get('city', '').strip() or None,
                    phone_number=phone_number,
                    profile_description=request.form.get(
                        'profile_description', '').strip() or None,
                    password=password
                )
                db.session.add(new_user)
                db.session.flush()  # Flush to get the user_id

                # Create caregiver if selected
                if is_caregiver:
                    new_caregiver = Caregiver(
                        caregiver_user_id=new_user.user_id,
                        photo=request.form.get('photo', '').strip() or None,
                        gender=request.form.get('gender', '').strip() or None,
                        caregiving_type=caregiving_type,
                        hourly_rate=hourly_rate_value
                    )
                    db.session.add(new_caregiver)

                # Create member if selected
                if is_member:
                    # Validate address fields (required for member)
                    house_number = request.form.get('house_number', '').strip()
                    street = request.form.get('street', '').strip()
                    town = request.form.get('town', '').strip()

                    if not house_number:
                        flash(
                            'House number is required when creating a member.', 'error')
                        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                    if not street:
                        flash('Street is required when creating a member.', 'error')
                        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                    if not town:
                        flash('Town is required when creating a member.', 'error')
                        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)

                    new_member = Member(
                        member_user_id=new_user.user_id,
                        house_rules=request.form.get(
                            'house_rules', '').strip() or None,
                        dependent_description=request.form.get(
                            'dependent_description', '').strip() or None
                    )
                    db.session.add(new_member)
                    db.session.flush()  # Flush to get the member_user_id

                    # Create address (required for member)
                    new_address = Address(
                        member_user_id=new_member.member_user_id,
                        house_number=house_number,
                        street=street,
                        town=town
                    )
                    db.session.add(new_address)

                try:
                    db.session.commit()
                    # Reset the sequence to the max user_id to prevent future conflicts
                    reset_user_sequence()
                    flash('User created successfully!', 'success')
                    return redirect(url_for('users'))
                except IntegrityError as ie:
                    db.session.rollback()
                    error_str = str(ie).lower()
                    # Check if it's a primary key sequence issue
                    if 'users_pkey' in error_str or ('user_id' in error_str and 'already exists' in error_str):
                        # Fix the sequence and retry
                        reset_user_sequence()
                        # Retry creating the user and related records
                        db.session.add(new_user)
                        db.session.flush()

                        # Recreate caregiver if needed
                        if is_caregiver:
                            retry_caregiver = Caregiver(
                                caregiver_user_id=new_user.user_id,
                                photo=request.form.get(
                                    'photo', '').strip() or None,
                                gender=request.form.get(
                                    'gender', '').strip() or None,
                                caregiving_type=caregiving_type,
                                hourly_rate=hourly_rate_value
                            )
                            db.session.add(retry_caregiver)

                        # Recreate member if needed
                        if is_member:
                            # Get address fields (required for member)
                            house_number = request.form.get(
                                'house_number', '').strip()
                            street = request.form.get('street', '').strip()
                            town = request.form.get('town', '').strip()

                            retry_member = Member(
                                member_user_id=new_user.user_id,
                                house_rules=request.form.get(
                                    'house_rules', '').strip() or None,
                                dependent_description=request.form.get(
                                    'dependent_description', '').strip() or None
                            )
                            db.session.add(retry_member)
                            db.session.flush()

                            # Recreate address (required for member)
                            retry_address = Address(
                                member_user_id=retry_member.member_user_id,
                                house_number=house_number,
                                street=street,
                                town=town
                            )
                            db.session.add(retry_address)

                        db.session.commit()
                        # Reset sequence again after successful creation
                        reset_user_sequence()
                        flash('User created successfully!', 'success')
                        return redirect(url_for('users'))
                    raise  # Re-raise if it's a different IntegrityError
            return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)
    except IntegrityError as e:
        db.session.rollback()
        # Check if it's an email or phone number constraint violation
        error_msg = str(e).lower()
        if 'email' in error_msg and ('unique' in error_msg or 'duplicate' in error_msg):
            flash(
                'Email already exists in the database. Please use a different email.', 'error')
        elif 'phone_number' in error_msg or ('phone' in error_msg and ('unique' in error_msg or 'duplicate' in error_msg)):
            flash(
                'Phone number already exists in the database. Please use a different phone number.', 'error')
        elif 'unique' in error_msg or 'duplicate' in error_msg:
            flash(
                'A field with this value already exists. Please check email and phone number.', 'error')
        else:
            flash(
                f'Error creating user: Database constraint violation. {str(e)}', 'error')
        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating user: {str(e)}', 'error')
        return render_template('create_user.html', caregiving_types=CAREGIVING_TYPES)


@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete a user"""
    try:
        with app.app_context():
            user = Users.query.get_or_404(user_id)
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Cannot delete user: User has related records (caregiver/member).', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    return redirect(url_for('users'))


# ==================== CAREGIVER ROUTES ====================

@app.route('/caregivers/create', methods=['GET', 'POST'])
def create_caregiver():
    """Create a new caregiver"""
    try:
        with app.app_context():
            if request.method == 'POST':
                # Get and clean email
                email = request.form.get('email', '').strip()

                # Validate email format
                email_valid, email_error = validate_email(email)
                if not email_valid:
                    flash(email_error, 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                # Get and clean phone number
                phone_number = request.form.get('phone_number', '').strip()

                # Validate phone number format
                phone_valid, phone_error = validate_phone_number(phone_number)
                if not phone_valid:
                    flash(phone_error, 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                # Check if email already exists
                existing_user = Users.query.filter(
                    Users.email == email).first()
                if existing_user:
                    flash(
                        'Email already exists. Please use a different email.', 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                # Check if phone number already exists
                existing_phone = Users.query.filter(
                    Users.phone_number == phone_number).first()
                if existing_phone:
                    flash(
                        'Phone number already exists. Please use a different phone number.', 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                # Validate caregiver-specific fields
                caregiving_type = request.form.get(
                    'caregiving_type', '').strip()
                hourly_rate = request.form.get('hourly_rate', '').strip()

                if not caregiving_type:
                    flash('Caregiving type is required.', 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                if caregiving_type not in CAREGIVING_TYPES:
                    flash(
                        f'Invalid caregiving type. Must be one of: {", ".join(CAREGIVING_TYPES)}', 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                if not hourly_rate:
                    flash('Hourly rate is required.', 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                is_valid, hourly_rate_value, error_msg = validate_hourly_rate(
                    hourly_rate)
                if not is_valid:
                    flash(error_msg, 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                # Validate password
                password = request.form.get('password', '').strip()
                password_valid, password_error = validate_password(password)
                if not password_valid:
                    flash(password_error, 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

                # Create new user
                new_user = Users(
                    email=email,
                    given_name=request.form.get('given_name', '').strip(),
                    surname=request.form.get('surname', '').strip(),
                    city=request.form.get('city', '').strip() or None,
                    phone_number=phone_number,
                    profile_description=request.form.get(
                        'profile_description', '').strip() or None,
                    password=password
                )
                db.session.add(new_user)
                db.session.flush()  # Flush to get the user_id

                # Create new caregiver
                new_caregiver = Caregiver(
                    caregiver_user_id=new_user.user_id,
                    photo=request.form.get('photo', '').strip() or None,
                    gender=request.form.get('gender', '').strip() or None,
                    caregiving_type=caregiving_type,
                    hourly_rate=hourly_rate_value
                )
                db.session.add(new_caregiver)

                try:
                    db.session.commit()
                    # Reset the sequence to the max user_id to prevent future conflicts
                    reset_user_sequence()
                    flash('Caregiver created successfully!', 'success')
                    return redirect(url_for('caregivers'))
                except IntegrityError as ie:
                    db.session.rollback()
                    error_str = str(ie).lower()
                    # Check if it's a primary key sequence issue
                    if 'users_pkey' in error_str or ('user_id' in error_str and 'already exists' in error_str):
                        reset_user_sequence()
                        flash(
                            'Error creating caregiver: Primary key conflict. Please try again. Sequence was reset.', 'error')
                        return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)
                    elif 'email' in error_str and ('unique' in error_str or 'duplicate' in error_str):
                        flash(
                            'Email already exists in the database. Please use a different email.', 'error')
                    elif 'phone_number' in error_str or ('phone' in error_str and ('unique' in error_str or 'duplicate' in error_str)):
                        flash(
                            'Phone number already exists in the database. Please use a different phone number.', 'error')
                    elif 'unique' in error_str or 'duplicate' in error_str:
                        flash(
                            'A field with this value already exists. Please check email and phone number.', 'error')
                    else:
                        flash(
                            f'Error creating caregiver: Database constraint violation. {str(ie)}', 'error')
                    return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)

            return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating caregiver: {str(e)}', 'error')
        return render_template('create_caregiver.html', caregiving_types=CAREGIVING_TYPES)


@app.route('/caregivers/<int:caregiver_id>/edit', methods=['GET', 'POST'])
def edit_caregiver(caregiver_id):
    """Edit a caregiver"""
    try:
        with app.app_context():
            caregiver = Caregiver.query.options(
                joinedload(Caregiver.user)).get_or_404(caregiver_id)
            if request.method == 'POST':
                # Validate caregiver-specific fields only
                caregiving_type = request.form.get(
                    'caregiving_type', '').strip()
                hourly_rate = request.form.get('hourly_rate', '').strip()

                if not caregiving_type:
                    flash('Caregiving type is required.', 'error')
                    return render_template('edit_caregiver.html', caregiver=caregiver, caregiving_types=CAREGIVING_TYPES)

                if caregiving_type not in CAREGIVING_TYPES:
                    flash(
                        f'Invalid caregiving type. Must be one of: {", ".join(CAREGIVING_TYPES)}', 'error')
                    return render_template('edit_caregiver.html', caregiver=caregiver, caregiving_types=CAREGIVING_TYPES)

                if not hourly_rate:
                    flash('Hourly rate is required.', 'error')
                    return render_template('edit_caregiver.html', caregiver=caregiver, caregiving_types=CAREGIVING_TYPES)

                is_valid, hourly_rate_value, error_msg = validate_hourly_rate(
                    hourly_rate)
                if not is_valid:
                    flash(error_msg, 'error')
                    return render_template('edit_caregiver.html', caregiver=caregiver, caregiving_types=CAREGIVING_TYPES)

                # Update only caregiver-specific fields
                caregiver.gender = request.form.get(
                    'gender', '').strip() or None
                caregiver.caregiving_type = caregiving_type
                caregiver.hourly_rate = hourly_rate_value
                caregiver.photo = request.form.get('photo', '').strip() or None
                db.session.commit()
                flash('Caregiver updated successfully!', 'success')
                return redirect(url_for('caregivers'))
            return render_template('edit_caregiver.html', caregiver=caregiver, caregiving_types=CAREGIVING_TYPES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating caregiver: {str(e)}', 'error')
        return redirect(url_for('caregivers'))


@app.route('/caregivers/<int:caregiver_id>/delete', methods=['POST'])
def delete_caregiver(caregiver_id):
    """Delete a caregiver"""
    try:
        with app.app_context():
            caregiver = Caregiver.query.get_or_404(caregiver_id)
            db.session.delete(caregiver)
            db.session.commit()
            flash('Caregiver deleted successfully!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Cannot delete caregiver: Caregiver has related records.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting caregiver: {str(e)}', 'error')
    return redirect(url_for('caregivers'))


# ==================== MEMBER ROUTES ====================

@app.route('/members/create', methods=['GET', 'POST'])
def create_member():
    """Create a new member"""
    try:
        with app.app_context():
            if request.method == 'POST':
                # Get and clean email
                email = request.form.get('email', '').strip()

                # Validate email format
                email_valid, email_error = validate_email(email)
                if not email_valid:
                    flash(email_error, 'error')
                    return render_template('create_member.html')

                # Get and clean phone number
                phone_number = request.form.get('phone_number', '').strip()

                # Validate phone number format
                phone_valid, phone_error = validate_phone_number(phone_number)
                if not phone_valid:
                    flash(phone_error, 'error')
                    return render_template('create_member.html')

                # Check if email already exists
                existing_user = Users.query.filter(
                    Users.email == email).first()
                if existing_user:
                    flash(
                        'Email already exists. Please use a different email.', 'error')
                    return render_template('create_member.html')

                # Check if phone number already exists
                existing_phone = Users.query.filter(
                    Users.phone_number == phone_number).first()
                if existing_phone:
                    flash(
                        'Phone number already exists. Please use a different phone number.', 'error')
                    return render_template('create_member.html')

                # Validate member address fields (required)
                house_number = request.form.get('house_number', '').strip()
                street = request.form.get('street', '').strip()
                town = request.form.get('town', '').strip()

                if not house_number:
                    flash('House number is required when creating a member.', 'error')
                    return render_template('create_member.html')

                if not street:
                    flash('Street is required when creating a member.', 'error')
                    return render_template('create_member.html')

                if not town:
                    flash('Town is required when creating a member.', 'error')
                    return render_template('create_member.html')

                # Validate password
                password = request.form.get('password', '').strip()
                password_valid, password_error = validate_password(password)
                if not password_valid:
                    flash(password_error, 'error')
                    return render_template('create_member.html')

                # Create new user
                new_user = Users(
                    email=email,
                    given_name=request.form.get('given_name', '').strip(),
                    surname=request.form.get('surname', '').strip(),
                    city=request.form.get('city', '').strip() or None,
                    phone_number=phone_number,
                    profile_description=request.form.get(
                        'profile_description', '').strip() or None,
                    password=password
                )
                db.session.add(new_user)
                db.session.flush()  # Flush to get the user_id

                # Create new member
                new_member = Member(
                    member_user_id=new_user.user_id,
                    house_rules=request.form.get(
                        'house_rules', '').strip() or None,
                    dependent_description=request.form.get(
                        'dependent_description', '').strip() or None
                )
                db.session.add(new_member)
                db.session.flush()  # Flush to get the member_user_id

                # Create address (required for member)
                new_address = Address(
                    member_user_id=new_member.member_user_id,
                    house_number=house_number,
                    street=street,
                    town=town
                )
                db.session.add(new_address)

                try:
                    db.session.commit()
                    # Reset the sequence to the max user_id to prevent future conflicts
                    reset_user_sequence()
                    flash('Member created successfully!', 'success')
                    return redirect(url_for('members'))
                except IntegrityError as ie:
                    db.session.rollback()
                    error_str = str(ie).lower()
                    # Check if it's a primary key sequence issue
                    if 'users_pkey' in error_str or ('user_id' in error_str and 'already exists' in error_str):
                        reset_user_sequence()
                        flash(
                            'Error creating member: Primary key conflict. Please try again. Sequence was reset.', 'error')
                        return render_template('create_member.html')
                    elif 'email' in error_str and ('unique' in error_str or 'duplicate' in error_str):
                        flash(
                            'Email already exists in the database. Please use a different email.', 'error')
                    elif 'phone_number' in error_str or ('phone' in error_str and ('unique' in error_str or 'duplicate' in error_str)):
                        flash(
                            'Phone number already exists in the database. Please use a different phone number.', 'error')
                    elif 'unique' in error_str or 'duplicate' in error_str:
                        flash(
                            'A field with this value already exists. Please check email and phone number.', 'error')
                    else:
                        flash(
                            f'Error creating member: Database constraint violation. {str(ie)}', 'error')
                    return render_template('create_member.html')

            return render_template('create_member.html')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating member: {str(e)}', 'error')
        return render_template('create_member.html')


@app.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
def edit_member(member_id):
    """Edit a member"""
    try:
        with app.app_context():
            member = Member.query.options(
                joinedload(Member.user),
                joinedload(Member.address)
            ).get_or_404(member_id)
            if request.method == 'POST':
                # Validate address fields (required for member)
                house_number = request.form.get('house_number', '').strip()
                street = request.form.get('street', '').strip()
                town = request.form.get('town', '').strip()

                if not house_number:
                    flash('House number is required.', 'error')
                    return render_template('edit_member.html', member=member)

                if not street:
                    flash('Street is required.', 'error')
                    return render_template('edit_member.html', member=member)

                if not town:
                    flash('Town is required.', 'error')
                    return render_template('edit_member.html', member=member)

                # Update only member-specific fields
                member.house_rules = request.form.get(
                    'house_rules', '').strip() or None
                member.dependent_description = request.form.get(
                    'dependent_description', '').strip() or None

                # Update or create address
                if member.address:
                    member.address.house_number = house_number
                    member.address.street = street
                    member.address.town = town
                else:
                    new_address = Address(
                        member_user_id=member.member_user_id,
                        house_number=house_number,
                        street=street,
                        town=town
                    )
                    db.session.add(new_address)

                db.session.commit()
                flash('Member updated successfully!', 'success')
                return redirect(url_for('members'))
            return render_template('edit_member.html', member=member)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating member: {str(e)}', 'error')
        return redirect(url_for('members'))


@app.route('/members/<int:member_id>/delete', methods=['POST'])
def delete_member(member_id):
    """Delete a member"""
    try:
        with app.app_context():
            member = Member.query.get_or_404(member_id)
            db.session.delete(member)
            db.session.commit()
            flash('Member deleted successfully!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Cannot delete member: Member has related records.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting member: {str(e)}', 'error')
    return redirect(url_for('members'))


# ==================== ADDRESS ROUTES ====================

@app.route('/addresses/<int:member_id>/edit', methods=['GET', 'POST'])
def edit_address(member_id):
    """Edit an address"""
    try:
        with app.app_context():
            address = Address.query.options(
                joinedload(Address.member).joinedload(Member.user)
            ).get_or_404(member_id)
            if request.method == 'POST':
                address.house_number = request.form.get('house_number')
                address.street = request.form.get('street')
                address.town = request.form.get('town')
                db.session.commit()
                flash('Address updated successfully!', 'success')
                return redirect(url_for('addresses'))
            return render_template('edit_address.html', address=address)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating address: {str(e)}', 'error')
        return redirect(url_for('addresses'))


@app.route('/addresses/<int:member_id>/delete', methods=['POST'])
def delete_address(member_id):
    """Delete an address"""
    try:
        with app.app_context():
            address = Address.query.get_or_404(member_id)
            db.session.delete(address)
            db.session.commit()
            flash('Address deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting address: {str(e)}', 'error')
    return redirect(url_for('addresses'))


# ==================== JOB ROUTES ====================

@app.route('/jobs/create', methods=['GET', 'POST'])
def create_job():
    """Create a new job"""
    try:
        with app.app_context():
            # Get all members for dropdown
            all_members = Member.query.options(
                joinedload(Member.user)
            ).all()
            member_choices = [(m.member_user_id, f"{m.user.given_name} {m.user.surname}")
                              for m in all_members]
            member_choices.sort(key=lambda x: x[0])  # Sort by ID

            if request.method == 'POST':
                # Validate member selection
                member_id = request.form.get('member_user_id', '').strip()
                if not member_id:
                    flash('Member is required.', 'error')
                    return render_template('create_job.html',
                                           member_choices=member_choices,
                                           caregiving_types=CAREGIVING_TYPES)

                try:
                    member_id_value = int(member_id)
                except ValueError:
                    flash('Invalid member ID.', 'error')
                    return render_template('create_job.html',
                                           member_choices=member_choices,
                                           caregiving_types=CAREGIVING_TYPES)

                # Check if member exists
                member = Member.query.get(member_id_value)
                if not member:
                    flash('Selected member does not exist.', 'error')
                    return render_template('create_job.html',
                                           member_choices=member_choices,
                                           caregiving_types=CAREGIVING_TYPES)

                # Validate required caregiving type
                required_caregiving_type = request.form.get(
                    'required_caregiving_type', '').strip()
                if not required_caregiving_type:
                    flash('Required caregiving type is required.', 'error')
                    return render_template('create_job.html',
                                           member_choices=member_choices,
                                           caregiving_types=CAREGIVING_TYPES)

                if required_caregiving_type not in CAREGIVING_TYPES:
                    flash(
                        f'Invalid caregiving type. Must be one of: {", ".join(CAREGIVING_TYPES)}', 'error')
                    return render_template('create_job.html',
                                           member_choices=member_choices,
                                           caregiving_types=CAREGIVING_TYPES)

                # Validate date posted
                date_posted_str = request.form.get('date_posted', '').strip()
                if not date_posted_str:
                    flash('Date posted is required.', 'error')
                    return render_template('create_job.html',
                                           member_choices=member_choices,
                                           caregiving_types=CAREGIVING_TYPES)

                try:
                    date_posted_value = date.fromisoformat(date_posted_str)
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                    return render_template('create_job.html',
                                           member_choices=member_choices,
                                           caregiving_types=CAREGIVING_TYPES)

                # Create new job
                new_job = Job(
                    member_user_id=member_id_value,
                    required_caregiving_type=required_caregiving_type,
                    other_requirements=request.form.get(
                        'other_requirements', '').strip() or None,
                    date_posted=date_posted_value
                )
                db.session.add(new_job)

                try:
                    db.session.commit()
                    flash('Job created successfully!', 'success')
                    return redirect(url_for('jobs'))
                except IntegrityError as ie:
                    db.session.rollback()
                    error_str = str(ie).lower()
                    if 'member' in error_str or 'foreign key' in error_str:
                        flash(
                            'Invalid member selected. Please select a valid member.', 'error')
                    else:
                        flash(
                            f'Error creating job: Database constraint violation. {str(ie)}', 'error')
                    return render_template('create_job.html',
                                           member_choices=member_choices,
                                           caregiving_types=CAREGIVING_TYPES)

            return render_template('create_job.html',
                                   member_choices=member_choices,
                                   caregiving_types=CAREGIVING_TYPES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating job: {str(e)}', 'error')
        return render_template('create_job.html',
                               member_choices=[],
                               caregiving_types=CAREGIVING_TYPES)


@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    """Edit a job"""
    try:
        with app.app_context():
            job = Job.query.options(
                joinedload(Job.member).joinedload(Member.user)
            ).get_or_404(job_id)
            if request.method == 'POST':
                # Validate required caregiving type
                required_caregiving_type = request.form.get(
                    'required_caregiving_type', '').strip()
                if not required_caregiving_type:
                    flash('Required caregiving type is required.', 'error')
                    return render_template('edit_job.html', job=job, caregiving_types=CAREGIVING_TYPES)

                if required_caregiving_type not in CAREGIVING_TYPES:
                    flash(
                        f'Invalid caregiving type. Must be one of: {", ".join(CAREGIVING_TYPES)}', 'error')
                    return render_template('edit_job.html', job=job, caregiving_types=CAREGIVING_TYPES)

                # Validate date posted
                date_posted_str = request.form.get('date_posted', '').strip()
                if not date_posted_str:
                    flash('Date posted is required.', 'error')
                    return render_template('edit_job.html', job=job, caregiving_types=CAREGIVING_TYPES)

                try:
                    date_posted_value = date.fromisoformat(date_posted_str)
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                    return render_template('edit_job.html', job=job, caregiving_types=CAREGIVING_TYPES)

                job.required_caregiving_type = required_caregiving_type
                job.other_requirements = request.form.get(
                    'other_requirements', '').strip() or None
                job.date_posted = date_posted_value
                db.session.commit()
                flash('Job updated successfully!', 'success')
                return redirect(url_for('jobs'))
            return render_template('edit_job.html', job=job, caregiving_types=CAREGIVING_TYPES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating job: {str(e)}', 'error')
        return redirect(url_for('jobs'))


@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job"""
    try:
        with app.app_context():
            job = Job.query.get_or_404(job_id)
            db.session.delete(job)
            db.session.commit()
            flash('Job deleted successfully!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Cannot delete job: Job has related records.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting job: {str(e)}', 'error')
    return redirect(url_for('jobs'))


# ==================== JOB APPLICATION ROUTES ====================

@app.route('/job-applications/create', methods=['GET', 'POST'])
def create_job_application():
    """Create a new job application"""
    try:
        with app.app_context():
            # Get all caregivers for dropdown
            all_caregivers = Caregiver.query.options(
                joinedload(Caregiver.user)
            ).all()
            caregiver_choices = [(c.caregiver_user_id, f"{c.user.given_name} {c.user.surname}")
                                 for c in all_caregivers]
            caregiver_choices.sort(key=lambda x: x[0])  # Sort by ID

            # Get all jobs for dropdown
            all_jobs = Job.query.options(
                joinedload(Job.member).joinedload(Member.user)
            ).all()
            job_choices = [(j.job_id, f"Job {j.job_id} - {j.member.user.given_name} {j.member.user.surname} ({j.required_caregiving_type})")
                           for j in all_jobs]
            job_choices.sort(key=lambda x: x[0])  # Sort by ID

            if request.method == 'POST':
                # Validate caregiver selection
                caregiver_id = request.form.get(
                    'caregiver_user_id', '').strip()
                if not caregiver_id:
                    flash('Caregiver is required.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                try:
                    caregiver_id_value = int(caregiver_id)
                except ValueError:
                    flash('Invalid caregiver ID.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                # Check if caregiver exists
                caregiver = Caregiver.query.get(caregiver_id_value)
                if not caregiver:
                    flash('Selected caregiver does not exist.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                # Validate job selection
                job_id = request.form.get('job_id', '').strip()
                if not job_id:
                    flash('Job is required.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                try:
                    job_id_value = int(job_id)
                except ValueError:
                    flash('Invalid job ID.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                # Check if job exists
                job = Job.query.get(job_id_value)
                if not job:
                    flash('Selected job does not exist.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                # Check if application already exists
                existing_application = JobApplication.query.filter_by(
                    caregiver_user_id=caregiver_id_value,
                    job_id=job_id_value
                ).first()
                if existing_application:
                    flash('This caregiver has already applied for this job.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                # Validate date applied
                date_applied_str = request.form.get('date_applied', '').strip()
                if not date_applied_str:
                    flash('Date applied is required.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                try:
                    date_applied_value = date.fromisoformat(date_applied_str)
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

                # Create new job application
                new_application = JobApplication(
                    caregiver_user_id=caregiver_id_value,
                    job_id=job_id_value,
                    date_applied=date_applied_value
                )
                db.session.add(new_application)

                try:
                    db.session.commit()
                    flash('Job application created successfully!', 'success')
                    return redirect(url_for('job_applications'))
                except IntegrityError as ie:
                    db.session.rollback()
                    error_str = str(ie).lower()
                    if 'job_application_pkey' in error_str or ('duplicate' in error_str and 'key' in error_str):
                        flash(
                            'This caregiver has already applied for this job.', 'error')
                    elif 'caregiver' in error_str or 'foreign key' in error_str:
                        flash(
                            'Invalid caregiver selected. Please select a valid caregiver.', 'error')
                    elif 'job' in error_str or 'foreign key' in error_str:
                        flash(
                            'Invalid job selected. Please select a valid job.', 'error')
                    else:
                        flash(
                            f'Error creating job application: Database constraint violation. {str(ie)}', 'error')
                    return render_template('create_job_application.html',
                                           caregiver_choices=caregiver_choices,
                                           job_choices=job_choices)

            return render_template('create_job_application.html',
                                   caregiver_choices=caregiver_choices,
                                   job_choices=job_choices)
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating job application: {str(e)}', 'error')
        return render_template('create_job_application.html',
                               caregiver_choices=[],
                               job_choices=[])


@app.route('/job-applications/<int:caregiver_id>/<int:job_id>/delete', methods=['POST'])
def delete_job_application(caregiver_id, job_id):
    """Delete a job application"""
    try:
        with app.app_context():
            application = JobApplication.query.filter_by(
                caregiver_user_id=caregiver_id,
                job_id=job_id
            ).first_or_404()
            db.session.delete(application)
            db.session.commit()
            flash('Job application deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting job application: {str(e)}', 'error')
    return redirect(url_for('job_applications'))


# ==================== APPOINTMENT ROUTES ====================

@app.route('/appointments/create', methods=['GET', 'POST'])
def create_appointment():
    """Create a new appointment"""
    try:
        with app.app_context():
            # Get all caregivers for dropdown
            all_caregivers = Caregiver.query.options(
                joinedload(Caregiver.user)
            ).all()
            caregiver_choices = [(c.caregiver_user_id, f"{c.user.given_name} {c.user.surname}")
                                 for c in all_caregivers]
            caregiver_choices.sort(key=lambda x: x[0])  # Sort by ID

            # Get all members for dropdown
            all_members = Member.query.options(
                joinedload(Member.user)
            ).all()
            member_choices = [(m.member_user_id, f"{m.user.given_name} {m.user.surname}")
                              for m in all_members]
            member_choices.sort(key=lambda x: x[0])  # Sort by ID

            if request.method == 'POST':
                # Validate caregiver selection
                caregiver_id = request.form.get(
                    'caregiver_user_id', '').strip()
                if not caregiver_id:
                    flash('Caregiver is required.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                try:
                    caregiver_id_value = int(caregiver_id)
                except ValueError:
                    flash('Invalid caregiver ID.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                # Check if caregiver exists
                caregiver = Caregiver.query.get(caregiver_id_value)
                if not caregiver:
                    flash('Selected caregiver does not exist.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                # Validate member selection
                member_id = request.form.get('member_user_id', '').strip()
                if not member_id:
                    flash('Member is required.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                try:
                    member_id_value = int(member_id)
                except ValueError:
                    flash('Invalid member ID.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                # Check if member exists
                member = Member.query.get(member_id_value)
                if not member:
                    flash('Selected member does not exist.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                # Validate appointment date
                appointment_date_str = request.form.get(
                    'appointment_date', '').strip()
                if not appointment_date_str:
                    flash('Appointment date is required.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                try:
                    appointment_date_value = date.fromisoformat(
                        appointment_date_str)
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                # Validate appointment date is at least tomorrow
                is_valid_date, date_error_msg = validate_appointment_date(
                    appointment_date_value)
                if not is_valid_date:
                    flash(date_error_msg, 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                # Validate appointment time
                appointment_time_str = request.form.get(
                    'appointment_time', '').strip()
                if not appointment_time_str:
                    flash('Appointment time is required.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                try:
                    # Parse HH:MM format
                    hour, minute = map(int, appointment_time_str.split(':'))
                    appointment_time_value = time(hour, minute)
                except (ValueError, AttributeError):
                    flash('Invalid time format. Please use HH:MM format.', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                # Validate work hours
                work_hours_str = request.form.get('work_hours', '').strip()
                is_valid, work_hours_value, error_msg = validate_work_hours(
                    work_hours_str)
                if not is_valid:
                    flash(error_msg, 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

                # Create new appointment (status defaults to 'pending' in the model)
                new_appointment = Appointment(
                    caregiver_user_id=caregiver_id_value,
                    member_user_id=member_id_value,
                    appointment_date=appointment_date_value,
                    appointment_time=appointment_time_value,
                    work_hours=work_hours_value
                )
                db.session.add(new_appointment)

                try:
                    db.session.commit()
                    flash('Appointment created successfully!', 'success')
                    return redirect(url_for('appointments'))
                except IntegrityError as ie:
                    db.session.rollback()
                    error_str = str(ie).lower()
                    if 'caregiver' in error_str or 'foreign key' in error_str:
                        flash(
                            'Invalid caregiver selected. Please select a valid caregiver.', 'error')
                    elif 'member' in error_str or 'foreign key' in error_str:
                        flash(
                            'Invalid member selected. Please select a valid member.', 'error')
                    else:
                        flash(
                            f'Error creating appointment: Database constraint violation. {str(ie)}', 'error')
                    return render_template('create_appointment.html',
                                           caregiver_choices=caregiver_choices,
                                           member_choices=member_choices)

            return render_template('create_appointment.html',
                                   caregiver_choices=caregiver_choices,
                                   member_choices=member_choices)
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating appointment: {str(e)}', 'error')
        return render_template('create_appointment.html',
                               caregiver_choices=[],
                               member_choices=[])


@app.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    """Edit an appointment"""
    try:
        with app.app_context():
            appointment = Appointment.query.options(
                joinedload(Appointment.caregiver).joinedload(Caregiver.user),
                joinedload(Appointment.member).joinedload(Member.user)
            ).get_or_404(appointment_id)
            if request.method == 'POST':
                # Validate appointment date
                appointment_date_str = request.form.get(
                    'appointment_date', '').strip()
                if not appointment_date_str:
                    flash('Appointment date is required.', 'error')
                    return render_template('edit_appointment.html',
                                           appointment=appointment,
                                           appointment_statuses=APPOINTMENT_STATUSES)

                try:
                    appointment_date_value = date.fromisoformat(
                        appointment_date_str)
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                    return render_template('edit_appointment.html',
                                           appointment=appointment,
                                           appointment_statuses=APPOINTMENT_STATUSES)

                # Validate appointment date is at least tomorrow
                is_valid_date, date_error_msg = validate_appointment_date(
                    appointment_date_value)
                if not is_valid_date:
                    flash(date_error_msg, 'error')
                    return render_template('edit_appointment.html',
                                           appointment=appointment,
                                           appointment_statuses=APPOINTMENT_STATUSES)

                appointment.appointment_date = appointment_date_value

                # Validate appointment time
                appointment_time_str = request.form.get(
                    'appointment_time', '').strip()
                if not appointment_time_str:
                    flash('Appointment time is required.', 'error')
                    return render_template('edit_appointment.html',
                                           appointment=appointment,
                                           appointment_statuses=APPOINTMENT_STATUSES)

                try:
                    appointment.appointment_time = time.fromisoformat(
                        appointment_time_str)
                except ValueError:
                    flash('Invalid time format. Please use HH:MM format.', 'error')
                    return render_template('edit_appointment.html',
                                           appointment=appointment,
                                           appointment_statuses=APPOINTMENT_STATUSES)

                # Validate work hours
                work_hours_str = request.form.get('work_hours', '').strip()
                is_valid, work_hours_value, error_msg = validate_work_hours(
                    work_hours_str)
                if not is_valid:
                    flash(error_msg, 'error')
                    return render_template('edit_appointment.html',
                                           appointment=appointment,
                                           appointment_statuses=APPOINTMENT_STATUSES)
                appointment.work_hours = work_hours_value

                # Validate status
                status = request.form.get('status', '').strip()
                if not status:
                    flash('Status is required.', 'error')
                    return render_template('edit_appointment.html',
                                           appointment=appointment,
                                           appointment_statuses=APPOINTMENT_STATUSES)

                if status not in APPOINTMENT_STATUSES:
                    flash(
                        f'Invalid status. Must be one of: {", ".join(APPOINTMENT_STATUSES)}', 'error')
                    return render_template('edit_appointment.html',
                                           appointment=appointment,
                                           appointment_statuses=APPOINTMENT_STATUSES)

                appointment.status = status
                db.session.commit()
                flash('Appointment updated successfully!', 'success')
                return redirect(url_for('appointments'))
            return render_template('edit_appointment.html',
                                   appointment=appointment,
                                   appointment_statuses=APPOINTMENT_STATUSES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating appointment: {str(e)}', 'error')
        return redirect(url_for('appointments'))


@app.route('/appointments/<int:appointment_id>/accept', methods=['POST'])
def accept_appointment(appointment_id):
    """Accept an appointment (change status to accepted)"""
    try:
        with app.app_context():
            appointment = Appointment.query.get_or_404(appointment_id)
            if appointment.status != 'pending':
                flash('Only pending appointments can be accepted.', 'error')
            else:
                appointment.status = 'accepted'
                db.session.commit()
                flash('Appointment accepted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error accepting appointment: {str(e)}', 'error')
    return redirect(url_for('appointments'))


@app.route('/appointments/<int:appointment_id>/decline', methods=['POST'])
def decline_appointment(appointment_id):
    """Decline an appointment (change status to declined)"""
    try:
        with app.app_context():
            appointment = Appointment.query.get_or_404(appointment_id)
            if appointment.status != 'pending':
                flash('Only pending appointments can be declined.', 'error')
            else:
                appointment.status = 'declined'
                db.session.commit()
                flash('Appointment declined successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error declining appointment: {str(e)}', 'error')
    return redirect(url_for('appointments'))


@app.route('/appointments/<int:appointment_id>/delete', methods=['POST'])
def delete_appointment(appointment_id):
    """Delete an appointment"""
    try:
        with app.app_context():
            appointment = Appointment.query.get_or_404(appointment_id)
            db.session.delete(appointment)
            db.session.commit()
            flash('Appointment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting appointment: {str(e)}', 'error')
    return redirect(url_for('appointments'))


if __name__ == '__main__':
    app.run(debug=True)
