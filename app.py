from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'devsecret')

from werkzeug.security import generate_password_hash, check_password_hash

# We'll use the ORM models and engine defined in script.py for DB access
from script import get_engine, User, Caregiver, Member, Address, Job, Appointment, JobApplication
from sqlalchemy.orm import sessionmaker

# Session factory using script.py's engine
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, future=True)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register/caregiver', methods=['GET', 'POST'])
def register_caregiver():
    if request.method == 'POST':
        form = request.form
        with SessionLocal() as db:
            # create user (hash password)
            raw_pw = form.get('password')
            hashed = generate_password_hash(raw_pw)
            user = User(email=form.get('email'), given_name=form.get('given_name'), surname=form.get('surname'), city=form.get('city'), phone_number=form.get('phone'), profile_description=form.get('bio'), password=hashed)
            db.add(user)
            db.flush()
            # create caregiver
            cg = Caregiver(caregiver_user_id=user.user_id, photo=form.get('photo') or '', gender=form.get('gender'), caregiving_type=form.get('care_type'), hourly_rate=form.get('hourly_rate') or 0)
            db.add(cg)
            db.commit()
            # set flask session
            flash('Caregiver registered successfully.', 'success')
            session.clear()
            session['user_id'] = user.user_id
            session['user_role'] = 'caregiver'
            session['user_name'] = f"{user.given_name} {user.surname}"
            return redirect(url_for('profile', caregiver_id=user.user_id))
    return render_template('register_caregiver.html')


@app.route('/register/member', methods=['GET', 'POST'])
def register_member():
    if request.method == 'POST':
        form = request.form
        with SessionLocal() as db:
            raw_pw = form.get('password')
            hashed = generate_password_hash(raw_pw)
            user = User(email=form.get('email'), given_name=form.get('given_name'), surname=form.get('surname'), city=form.get('city'), phone_number=form.get('phone'), password=hashed)
            db.add(user)
            db.flush()
            member = Member(member_user_id=user.user_id, house_rules=form.get('house_rules'), dependent_description=form.get('dependent'))
            db.add(member)
            db.flush()
            addr = Address(member_user_id=member.member_user_id, house_number=form.get('house_number'), street=form.get('street'), town=form.get('town'))
            db.add(addr)
            db.commit()
            flash('Member registered successfully.', 'success')
            session.clear()
            session['user_id'] = user.user_id
            session['user_role'] = 'member'
            session['user_name'] = f"{user.given_name} {user.surname}"
            return redirect(url_for('member_dashboard', member_id=user.user_id))
    return render_template('register_member.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = request.form
        email = form.get('email')
        password = form.get('password')
        with SessionLocal() as dbs:
            user = dbs.query(User).filter(User.email == email).first()
            if not user:
                flash('Invalid email or password', 'error')
                return redirect(url_for('login'))
            stored = user.password or ''
            ok = False
            try:
                ok = check_password_hash(stored, password)
            except Exception:
                ok = False
            if not ok:
                # fallback: plain text match for legacy seeds
                if stored == password:
                    ok = True
                    # re-hash and store
                    user.password = generate_password_hash(password)
                    dbs.commit()
            if not ok:
                flash('Invalid email or password', 'error')
                return redirect(url_for('login'))
            # determine role
            role = 'member' if dbs.query(Member).filter(Member.member_user_id == user.user_id).first() else None
            role = 'caregiver' if role is None and dbs.query(Caregiver).filter(Caregiver.caregiver_user_id == user.user_id).first() else role
            session.clear()
            session['user_id'] = user.user_id
            session['user_role'] = role
            session['user_name'] = f"{user.given_name} {user.surname}"
            flash('Logged in successfully.', 'success')
            # redirect based on role
            if role == 'member':
                return redirect(url_for('member_dashboard', member_id=user.user_id))
            if role == 'caregiver':
                return redirect(url_for('profile', caregiver_id=user.user_id))
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    caregivers = []
    allow_search = session.get('user_role') == 'member'
    if request.method == 'POST':
        # server-side enforcement: only members can search
        if not allow_search:
            flash('Only logged-in members can search for caregivers. Please log in as a member.', 'warning')
            return redirect(url_for('login'))
        ctype = request.form.get('care_type')
        city = request.form.get('city')
        with SessionLocal() as db:
            q = db.query(Caregiver).join(User).filter(Caregiver.caregiving_type.ilike(f"%{ctype}%"))
            if city:
                q = q.filter(User.city.ilike(f"%{city}%"))
            caregivers = q.all()
    return render_template('search.html', caregivers=caregivers, allow_search=allow_search)


@app.route('/profile/<int:caregiver_id>', methods=['GET', 'POST'])
def profile(caregiver_id):
    with SessionLocal() as db:
        caregiver = db.get(Caregiver, caregiver_id)
        user = caregiver.user if caregiver else None
        # determine whether to show contact info
        show_contact = False
        if session.get('user_role') == 'member' and session.get('user_id'):
            member_id = int(session.get('user_id'))
            accepted = db.query(Appointment).filter(Appointment.member_user_id == member_id, Appointment.caregiver_user_id == caregiver_id, Appointment.status == 'accepted').first()
            show_contact = bool(accepted)
        elif session.get('user_role') == 'caregiver' and session.get('user_id') == caregiver_id:
            show_contact = True

        if request.method == 'POST':
            # create a pending appointment (member_id from session if logged-in member, otherwise from form)
            if session.get('user_role') == 'member' and session.get('user_id'):
                member_id = int(session.get('user_id'))
            else:
                try:
                    member_id = int(request.form.get('member_id'))
                except Exception:
                    flash('Member id is required to request appointment.', 'error')
                    return redirect(url_for('profile', caregiver_id=caregiver_id))
            appt = Appointment(caregiver_user_id=caregiver_id, member_user_id=member_id, appointment_date=request.form.get('date'), appointment_time=request.form.get('time'), work_hours=float(request.form.get('hours') or 1), status='pending')
            db.add(appt)
            db.commit()
            flash('Appointment request created (pending).', 'success')
            return redirect(url_for('profile', caregiver_id=caregiver_id))
        return render_template('profile.html', caregiver=caregiver, user=user, show_contact=show_contact)


@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    with SessionLocal() as db:
        if request.method == 'POST':
            # Only members may post jobs
            if session.get('user_role') != 'member':
                flash('Only members may post job advertisements. Please log in as a member.', 'error')
                return redirect(url_for('login'))
            member_id = int(request.form.get('member_id'))
            job = Job(member_user_id=member_id, required_caregiving_type=request.form.get('required_type'), other_requirements=request.form.get('other_requirements'))
            db.add(job)
            db.commit()
            flash('Job posted successfully.', 'success')
            return redirect(url_for('jobs'))
        jobs = db.query(Job).all()
        # fetch members for job creation dropdown
        members = db.query(Member).join(User).all()
        return render_template('jobs.html', jobs=jobs, members=members)


@app.route('/jobs/apply/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    """Allow a caregiver to apply to a job. Form must provide `caregiver_id`."""
    # prefer session caregiver id when logged-in caregiver
    if session.get('user_role') == 'caregiver' and session.get('user_id'):
        caregiver_id = int(session.get('user_id'))
    else:
        caregiver_id = request.form.get('caregiver_id')
        if not caregiver_id:
            flash('Caregiver ID is required to apply.', 'error')
            return redirect(url_for('jobs'))
        try:
            caregiver_id = int(caregiver_id)
        except ValueError:
            flash('Invalid caregiver id.', 'error')
            return redirect(url_for('jobs'))

    with SessionLocal() as db:
        # Check if job exists
        job = db.get(Job, job_id)
        cg = db.get(Caregiver, caregiver_id)
        if not job or not cg:
            flash('Job or caregiver not found.', 'error')
            return redirect(url_for('jobs'))
        # Prevent duplicate applications by same caregiver for same job
        exists = db.query(JobApplication).filter(JobApplication.caregiver_user_id == caregiver_id, JobApplication.job_id == job_id).first()
        if exists:
            flash('You have already applied to this job.', 'info')
            return redirect(url_for('jobs'))
        app_row = JobApplication(caregiver_user_id=caregiver_id, job_id=job_id)
        db.add(app_row)
        db.commit()
        flash('Application submitted.', 'success')
    return redirect(url_for('jobs'))


@app.route('/jobs/<int:job_id>/applicants')
def view_applicants(job_id):
    """Show applicants for a specific job. Optionally accepts `member_id` as query param to indicate ownership."""
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            flash('Job not found.', 'error')
            return redirect(url_for('jobs'))
        # Only the member who posted the job may view applicants
        if session.get('user_role') != 'member' or session.get('user_id') != job.member_user_id:
            flash('Only the member who posted this job may view applicants.', 'error')
            return redirect(url_for('jobs'))
        rows = db.query(JobApplication).filter(JobApplication.job_id == job_id).all()
        applicants = []
        for a in rows:
            user = db.get(User, a.caregiver_user_id)
            applicants.append({'id': a.caregiver_user_id, 'given_name': user.given_name if user else None, 'surname': user.surname if user else None, 'date_applied': a.date_applied})
        return render_template('applicants.html', applicants=applicants, job=job)


@app.route('/dashboard/member/<int:member_id>')
def member_dashboard(member_id):
    with SessionLocal() as db:
        appts = db.query(Appointment).filter(Appointment.member_user_id == member_id).all()
        return render_template('dashboard.html', appointments=appts, member_id=member_id)


@app.route('/dashboard/caregiver/<int:caregiver_id>')
def caregiver_dashboard(caregiver_id):
    # Caregiver can view their appointment requests and accept/decline
    if session.get('user_role') != 'caregiver' or session.get('user_id') != caregiver_id:
        flash('You are not authorized to view this caregiver dashboard.', 'error')
        return redirect(url_for('home'))
    with SessionLocal() as db:
        appts = db.query(Appointment).filter(Appointment.caregiver_user_id == caregiver_id).all()
        return render_template('caregiver_dashboard.html', appointments=appts, caregiver_id=caregiver_id)


@app.route('/appointments/<int:appointment_id>/respond', methods=['POST'])
def respond_appointment(appointment_id):
    # caregiver accepts or declines an appointment
    action = request.form.get('action')
    with SessionLocal() as db:
        appt = db.get(Appointment, appointment_id)
        if not appt:
            flash('Appointment not found.', 'error')
            return redirect(url_for('home'))
        # only the caregiver for this appointment may respond
        if session.get('user_role') != 'caregiver' or session.get('user_id') != appt.caregiver_user_id:
            flash('Not authorized to respond to this appointment.', 'error')
            return redirect(url_for('home'))
        if action == 'accept':
            appt.status = 'accepted'
            db.commit()
            flash('Appointment accepted.', 'success')
        elif action == 'decline':
            appt.status = 'declined'
            db.commit()
            flash('Appointment declined.', 'info')
        else:
            flash('Unknown action.', 'error')
    return redirect(url_for('caregiver_dashboard', caregiver_id=session.get('user_id')))



if __name__ == '__main__':
    app.run(debug=True)
