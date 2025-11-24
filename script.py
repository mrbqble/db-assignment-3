"""
Database helper script for Assignment 3 — SQLAlchemy interface.

Usage:
  - Set `DATABASE_URL` env var (e.g. postgresql+psycopg2://user:pass@host/dbname)
  - Run: `python script.py --create-tables` to create tables (idempotent)
  - Run: `python script.py --seed` to insert sample data (only if missing)
  - Run: `python script.py --run-queries` to execute and print all required queries
  - Or `python script.py --full-run` to do all of the above.

This script implements the schema provided in the assignment and the required
Part 2 operations: update, delete, simple queries, complex queries,
derived-attribute calculations and a view creation.
"""

import os
import argparse
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
	create_engine,
	Column,
	Integer,
	String,
	Date,
	Time,
	Float,
	Text,
	ForeignKey,
	Numeric,
	Table,
	select,
	func,
	text,
)
from sqlalchemy.orm import declarative_base, relationship, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/assignment_db")

Base = declarative_base()


class User(Base):
	__tablename__ = "user_account"
	user_id = Column(Integer, primary_key=True)
	email = Column(String(255), unique=True, nullable=False)
	given_name = Column(String(100), nullable=False)
	surname = Column(String(100), nullable=False)
	city = Column(String(100))
	phone_number = Column(String(50))
	profile_description = Column(Text)
	password = Column(String(255), nullable=False)

	caregiver = relationship("Caregiver", back_populates="user", uselist=False)
	member = relationship("Member", back_populates="user", uselist=False)


class Caregiver(Base):
	__tablename__ = "caregiver"
	caregiver_user_id = Column(Integer, ForeignKey("user_account.user_id"), primary_key=True)
	photo = Column(String(255))
	gender = Column(String(20))
	caregiving_type = Column(String(100))
	hourly_rate = Column(Numeric(10, 2))

	user = relationship("User", back_populates="caregiver")
	applications = relationship("JobApplication", back_populates="caregiver")
	appointments = relationship("Appointment", back_populates="caregiver")


class Member(Base):
	__tablename__ = "member"
	member_user_id = Column(Integer, ForeignKey("user_account.user_id"), primary_key=True)
	house_rules = Column(Text)
	dependent_description = Column(Text)

	user = relationship("User", back_populates="member")
	address = relationship("Address", back_populates="member", uselist=False)
	jobs = relationship("Job", back_populates="member")
	appointments = relationship("Appointment", back_populates="member")


class Address(Base):
	__tablename__ = "address"
	id = Column(Integer, primary_key=True, autoincrement=True)
	member_user_id = Column(Integer, ForeignKey("member.member_user_id"), nullable=False)
	house_number = Column(String(50))
	street = Column(String(255))
	town = Column(String(255))

	member = relationship("Member", back_populates="address")


class Job(Base):
	__tablename__ = "job"
	job_id = Column(Integer, primary_key=True)
	member_user_id = Column(Integer, ForeignKey("member.member_user_id"), nullable=False)
	required_caregiving_type = Column(String(255))
	other_requirements = Column(Text)
	date_posted = Column(Date, default=date.today)

	member = relationship("Member", back_populates="jobs")
	applications = relationship("JobApplication", back_populates="job")


class JobApplication(Base):
	__tablename__ = "job_application"
	id = Column(Integer, primary_key=True, autoincrement=True)
	caregiver_user_id = Column(Integer, ForeignKey("caregiver.caregiver_user_id"), nullable=False)
	job_id = Column(Integer, ForeignKey("job.job_id"), nullable=False)
	date_applied = Column(Date, default=date.today)

	caregiver = relationship("Caregiver", back_populates="applications")
	job = relationship("Job", back_populates="applications")


class Appointment(Base):
	__tablename__ = "appointment"
	appointment_id = Column(Integer, primary_key=True)
	caregiver_user_id = Column(Integer, ForeignKey("caregiver.caregiver_user_id"), nullable=False)
	member_user_id = Column(Integer, ForeignKey("member.member_user_id"), nullable=False)
	appointment_date = Column(Date)
	appointment_time = Column(Time)
	work_hours = Column(Float)
	status = Column(String(50))

	caregiver = relationship("Caregiver", back_populates="appointments")
	member = relationship("Member", back_populates="appointments")


def get_engine(url: Optional[str] = None):
	url = url or DATABASE_URL
	engine = create_engine(url, echo=False, future=True)
	return engine


def create_tables(engine):
	print("Creating tables (if not exists)...")
	Base.metadata.create_all(engine)


def seed_sample_data(session: Session):
	"""Insert sample data only when there is insufficient data.

	The function checks counts and inserts sample rows to ensure queries return results.
	"""
	# Minimal checks
	user_count = session.scalar(func.count(User.user_id))
	if user_count and user_count >= 50:
		print("Sufficient users already present — skipping seeding.")
		return

	print("Seeding sample data...")

	# Create users
	users = []
	sample_users = [
		(1, "arman@example.com", "Arman", "Armanov", "Astana", "+77770000001", "Caregiver and parent", "pass1"),
		(2, "amina@example.com", "Amina", "Aminova", "Astana", "+77770000002", "Member posting jobs", "pass2"),
		(3, "nurs@example.com", "Nurs", "Nurman", "Almaty", "+77770000003", "Caregiver", "pass3"),
		(4, "ellie@example.com", "Ellie", "Evans", "Astana", "+77770000004", "Member", "pass4"),
		(5, "john@example.com", "John", "Doe", "Astana", "+77770000005", "Caregiver", "pass5"),
		(6, "jane@example.com", "Jane", "Roe", "Astana", "+77770000006", "Member", "pass6"),
		(7, "sam@example.com", "Sam", "Sagat", "Astana", "+77770000007", "Caregiver", "pass7"),
		(8, "liza@example.com", "Liza", "Khan", "Astana", "+77770000008", "Member", "pass8"),
		(9, "kate@example.com", "Kate", "Smith", "Astana", "+77770000009", "Caregiver", "pass9"),
		(10, "bob@example.com", "Bob", "Brown", "Astana", "+77770000010", "Member", "pass10"),
	]

	for u in sample_users:
		users.append(User(user_id=u[0], email=u[1], given_name=u[2], surname=u[3], city=u[4], phone_number=u[5], profile_description=u[6], password=u[7]))

	session.add_all(users)
	session.flush()

	# Create caregivers (tie to users 1,3,5,7,9)
	caregivers = [
		Caregiver(caregiver_user_id=1, photo="/photos/1.jpg", gender="M", caregiving_type="Babysitter", hourly_rate=Decimal("9.50")),
		Caregiver(caregiver_user_id=3, photo="/photos/3.jpg", gender="M", caregiving_type="Elderly Care", hourly_rate=Decimal("12.00")),
		Caregiver(caregiver_user_id=5, photo="/photos/5.jpg", gender="M", caregiving_type="Babysitter", hourly_rate=Decimal("8.50")),
		Caregiver(caregiver_user_id=7, photo="/photos/7.jpg", gender="M", caregiving_type="Nanny", hourly_rate=Decimal("11.00")),
		Caregiver(caregiver_user_id=9, photo="/photos/9.jpg", gender="F", caregiving_type="Elderly Care", hourly_rate=Decimal("15.00")),
	]
	session.add_all(caregivers)

	# Members (2,4,6,8,10)
	members = [
		Member(member_user_id=2, house_rules="No pets. Quiet hours 10pm-7am.", dependent_description="Toddler, 2 years"),
		Member(member_user_id=4, house_rules="No smoking. No pets.", dependent_description="Elderly, needs assistance"),
		Member(member_user_id=6, house_rules="No pets.", dependent_description="Infant care"),
		Member(member_user_id=8, house_rules="Pets allowed.", dependent_description="Child with special needs"),
		Member(member_user_id=10, house_rules="No pets.", dependent_description="Elderly with dementia"),
	]
	session.add_all(members)

	# Addresses
	addresses = [
		Address(member_user_id=2, house_number="12A", street="Kabanbay Batyr", town="Astana"),
		Address(member_user_id=4, house_number="5", street="Abylai Khan", town="Astana"),
		Address(member_user_id=6, house_number="7", street="Kabanbay Batyr", town="Astana"),
		Address(member_user_id=8, house_number="21", street="Tole Bi", town="Almaty"),
		Address(member_user_id=10, house_number="3", street="Main St", town="Astana"),
	]
	session.add_all(addresses)

	# Jobs
	jobs = [
		Job(job_id=100, member_user_id=2, required_caregiving_type="Babysitter", other_requirements="soft-spoken, patient", date_posted=date(2025,1,10)),
		Job(job_id=101, member_user_id=4, required_caregiving_type="Elderly Care", other_requirements="No pets. Experience with dementia", date_posted=date(2025,2,1)),
		Job(job_id=102, member_user_id=6, required_caregiving_type="Babysitter", other_requirements="soft-spoken", date_posted=date(2025,3,3)),
		Job(job_id=103, member_user_id=8, required_caregiving_type="Nanny", other_requirements="CPR certified", date_posted=date(2025,4,5)),
		Job(job_id=104, member_user_id=10, required_caregiving_type="Elderly Care", other_requirements="No pets.", date_posted=date(2025,5,6)),
	]
	session.add_all(jobs)

	# Job applications
	applications = [
		JobApplication(caregiver_user_id=1, job_id=100, date_applied=date(2025,1,11)),
		JobApplication(caregiver_user_id=3, job_id=101, date_applied=date(2025,2,2)),
		JobApplication(caregiver_user_id=5, job_id=100, date_applied=date(2025,1,12)),
		JobApplication(caregiver_user_id=7, job_id=103, date_applied=date(2025,4,6)),
		JobApplication(caregiver_user_id=9, job_id=104, date_applied=date(2025,5,7)),
		JobApplication(caregiver_user_id=1, job_id=102, date_applied=date(2025,3,4)),
	]
	session.add_all(applications)

	# Appointments (some accepted)
	appointments = [
		Appointment(appointment_id=1000, caregiver_user_id=1, member_user_id=2, appointment_date=date(2025,1,15), appointment_time=time(9,0), work_hours=4.0, status="accepted"),
		Appointment(appointment_id=1001, caregiver_user_id=5, member_user_id=2, appointment_date=date(2025,1,18), appointment_time=time(14,0), work_hours=3.0, status="accepted"),
		Appointment(appointment_id=1002, caregiver_user_id=3, member_user_id=4, appointment_date=date(2025,2,10), appointment_time=time(10,0), work_hours=5.0, status="accepted"),
		Appointment(appointment_id=1003, caregiver_user_id=7, member_user_id=8, appointment_date=date(2025,4,10), appointment_time=time(8,0), work_hours=6.0, status="pending"),
		Appointment(appointment_id=1004, caregiver_user_id=9, member_user_id=10, appointment_date=date(2025,5,10), appointment_time=time(12,0), work_hours=2.5, status="accepted"),
	]
	session.add_all(appointments)

	session.commit()
	print("Seeding completed.")


def update_phone_number(session: Session, given_name: str, surname: str, new_phone: str):
	stmt = select(User).where(User.given_name == given_name, User.surname == surname)
	user = session.scalar(stmt)
	if user:
		print(f"Updating phone for {given_name} {surname} to {new_phone}")
		user.phone_number = new_phone
		session.commit()
	else:
		print("User not found for update.")


def add_commission_to_caregivers(session: Session):
	print("Applying commission to caregivers' hourly rates...")
	caregivers = session.scalars(select(Caregiver)).all()
	for c in caregivers:
		rate = Decimal(c.hourly_rate)
		if rate < Decimal("10"):
			c.hourly_rate = (rate + Decimal("0.3")).quantize(Decimal("0.01"))
		else:
			c.hourly_rate = (rate * Decimal("1.10")).quantize(Decimal("0.01"))
	session.commit()
	print("Commission applied.")


def delete_jobs_by_member(session: Session, member_given_name: str, member_surname: str):
	print(f"Deleting jobs posted by {member_given_name} {member_surname}...")
	member_user = session.scalar(select(User).where(User.given_name == member_given_name, User.surname == member_surname))
	if not member_user:
		print("Member not found.")
		return
	member = session.scalar(select(Member).where(Member.member_user_id == member_user.user_id))
	if not member:
		print("Member record not found.")
		return
	deleted = session.execute(text("DELETE FROM job WHERE member_user_id = :mid RETURNING job_id"), {"mid": member.member_user_id})
	session.commit()
	print("Deleted jobs.")


def delete_members_by_street(session: Session, street_name: str):
	print(f"Deleting members who live on {street_name}...")
	# find addresses matching the street
	addr_rows = session.scalars(select(Address).where(func.lower(Address.street) == street_name.lower())).all()
	member_ids = [a.member_user_id for a in addr_rows]
	if not member_ids:
		print("No members found on that street.")
		return
	# delete addresses, appointments, jobs, member and user rows safely via cascade assumptions
	session.execute(text("DELETE FROM appointment WHERE member_user_id = ANY(:mids)"), {"mids": member_ids})
	session.execute(text("DELETE FROM job_application WHERE job_id IN (SELECT job_id FROM job WHERE member_user_id = ANY(:mids))"), {"mids": member_ids})
	session.execute(text("DELETE FROM job WHERE member_user_id = ANY(:mids)"), {"mids": member_ids})
	session.execute(text("DELETE FROM address WHERE member_user_id = ANY(:mids)"), {"mids": member_ids})
	session.execute(text("DELETE FROM member WHERE member_user_id = ANY(:mids)"), {"mids": member_ids})
	# optionally delete user accounts as well
	session.execute(text("DELETE FROM user_account WHERE user_id = ANY(:mids)"), {"mids": member_ids})
	session.commit()
	print("Deleted members and related records.")


def simple_queries(session: Session):
	print("\nSimple Queries:\n")
	# 5.1 Select caregiver and member names for the accepted appointments.
	q1 = (
		session.query(Caregiver, Member)
		.join(Appointment, Caregiver.caregiver_user_id == Appointment.caregiver_user_id)
		.join(Member, Member.member_user_id == Appointment.member_user_id)
		.filter(Appointment.status == "accepted")
	)
	print("5.1 Caregiver and member names for accepted appointments:")
	for c, m in q1:
		# some caregivers/members may not have user relationship if DB differs
		cg_name = f"{c.user.given_name} {c.user.surname}" if c.user else f"caregiver_id={c.caregiver_user_id}"
		mb_name = f"{m.user.given_name} {m.user.surname}" if m.user else f"member_id={m.member_user_id}"
		print(f"Caregiver: {cg_name} - Member: {mb_name}")

	# 5.2 List job ids that contain 'soft-spoken' in other requirements.
	print("\n5.2 Jobs with 'soft-spoken' in other_requirements:")
	rows = session.scalars(select(Job.job_id).where(func.lower(Job.other_requirements).like("%soft-spoken%"))).all()
	print(rows)

	# 5.3 List the work hours of all babysitter positions.
	print("\n5.3 Work hours of all babysitter positions (appointments for members who posted babysitter jobs):")
	babysitter_member_ids = [j.member_user_id for j in session.scalars(select(Job).where(func.lower(Job.required_caregiving_type).like("%babysitter%"))).all()]
	if babysitter_member_ids:
		wh2 = session.scalars(select(Appointment.work_hours).where(Appointment.member_user_id.in_(babysitter_member_ids))).all()
	else:
		wh2 = []
	print(wh2)

	# 5.4 List the members who are looking for Elderly Care in Astana and have "No pets." rule.
	print("\n5.4 Members looking for Elderly Care in Astana with 'No pets.' rule:")
	q54 = (
		session.query(Member)
		.join(Job, Job.member_user_id == Member.member_user_id)
		.join(Address, Address.member_user_id == Member.member_user_id)
		.filter(func.lower(Job.required_caregiving_type).like("%elderly%"))
		.filter(func.lower(Address.town) == "astana")
		.filter(func.lower(Member.house_rules).like("%no pets%"))
		.distinct()
	)
	for m in q54:
		name = f"{m.user.given_name} {m.user.surname}" if m.user else f"member_id={m.member_user_id}"
		print(f"Member: {name} (user_id={m.member_user_id})")


def complex_queries(session: Session):
	print("\nComplex Queries:\n")
	# 6.1 Count the number of applicants for each job posted by a member
	print("6.1 Applicant counts per job:")
	rows = session.execute(
		select(Job.job_id, func.count(JobApplication.id).label("app_count")).outerjoin(JobApplication, Job.job_id == JobApplication.job_id).group_by(Job.job_id)
	)
	for r in rows:
		print(r)

	# 6.2 Total hours spent by care givers for all accepted appointments
	print("\n6.2 Total hours for accepted appointments:")
	total_hours = session.scalar(select(func.coalesce(func.sum(Appointment.work_hours), 0)).where(Appointment.status == "accepted"))
	print(total_hours)

	# 6.3 Average pay of caregivers based on accepted appointments (average hourly_rate among caregivers with accepted appointments)
	print("\n6.3 Average caregiver hourly rate for accepted appointments:")
	avg_pay = session.scalar(
		select(func.avg(Caregiver.hourly_rate)).where(Caregiver.caregiver_user_id.in_(select(Appointment.caregiver_user_id).where(Appointment.status == "accepted")))
	)
	print(avg_pay)

	# 6.4 Caregivers who earn above average based on accepted appointments
	print("\n6.4 Caregivers earning above average (hourly_rate) among caregivers with accepted appointments:")
	if avg_pay is not None:
		rows = session.scalars(select(Caregiver).where(Caregiver.hourly_rate > avg_pay)).all()
		for c in rows:
			print(f"{c.user.given_name} {c.user.surname}: {c.hourly_rate}")
	else:
		print("No accepted appointments or no caregivers found.")


def derived_attribute_and_view(session: Session):
	print("\nDerived Attribute and View Operations:\n")
	# 7. Calculate the total cost to pay for a caregiver for all accepted appointments.
	print("7. Total cost to pay caregivers for accepted appointments (per caregiver):")
	rows = session.execute(
		select(
			Caregiver.caregiver_user_id,
			func.sum(Appointment.work_hours * Caregiver.hourly_rate).label("total_pay")
		).join(Appointment, Caregiver.caregiver_user_id == Appointment.caregiver_user_id).where(Appointment.status == "accepted").group_by(Caregiver.caregiver_user_id)
	)
	for r in rows:
		# fetch caregiver name
		cg = session.get(Caregiver, r.caregiver_user_id)
		name = f"{cg.user.given_name} {cg.user.surname}" if cg and cg.user else f"caregiver_id={r.caregiver_user_id}"
		print(f"Caregiver {name} (id={r.caregiver_user_id}) - Total Pay: {r.total_pay}")

	# 8. View Operation: create a view that shows job applications and applicants
	print("\n8. Creating view `job_applicants_view` (if not exists) and showing rows:")
	create_view_sql = text(
		"""
		CREATE VIEW IF NOT EXISTS job_applicants_view AS
		SELECT ja.id as application_id, ja.job_id, j.member_user_id as job_posted_by,
			   u_app.given_name as applicant_given_name, u_app.surname as applicant_surname,
			   ja.date_applied
		FROM job_application ja
		JOIN job j ON ja.job_id = j.job_id
		JOIN user_account u_app ON ja.caregiver_user_id = u_app.user_id
		"""
	)
	session.execute(create_view_sql)
	session.commit()

	rows = session.execute(text("SELECT * FROM job_applicants_view LIMIT 50"))
	for r in rows:
		print(dict(r))


def main():
	parser = argparse.ArgumentParser(description="Assignment 3 DB helper using SQLAlchemy")
	parser.add_argument("--create-tables", action="store_true")
	parser.add_argument("--seed", action="store_true")
	parser.add_argument("--run-queries", action="store_true")
	parser.add_argument("--full-run", action="store_true", help="create tables, seed, then run queries")
	args = parser.parse_args()

	engine = get_engine()
	SessionLocal = sessionmaker(bind=engine, future=True)

	if args.create_tables or args.full_run:
		create_tables(engine)

	with SessionLocal() as session:
		if args.seed or args.full_run:
			seed_sample_data(session)

		if args.full_run or args.run_queries:
			# 3.1 Update phone number of Arman Armanov
			update_phone_number(session, "Arman", "Armanov", "+77773414141")

			# 3.2 Add commission fee to caregivers
			add_commission_to_caregivers(session)

			# 4.1 Delete the jobs posted by Amina Aminova
			delete_jobs_by_member(session, "Amina", "Aminova")

			# 4.2 Delete all members who live on Kabanbay Batyr street
			delete_members_by_street(session, "Kabanbay Batyr")

			# Simple queries
			simple_queries(session)

			# Complex queries
			complex_queries(session)

			# Derived attribute and view
			derived_attribute_and_view(session)


if __name__ == "__main__":
	main()

