from datetime import date
from sqlalchemy import Column, Integer, String, Numeric, Date, Time, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, validates
from flask_sqlalchemy import SQLAlchemy

# Create db instance - will be initialized with app in app.py
db = SQLAlchemy()

# Standardized caregiving types - single source of truth
CAREGIVING_TYPES = ['babysitter',
                    'caregiver for elderly', 'playmate for children']

# Standardized appointment statuses - single source of truth
APPOINTMENT_STATUSES = ['pending', 'accepted', 'declined']


class Users(db.Model):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    given_name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    city = Column(String(100))
    phone_number = Column(String(20), unique=True, nullable=False)
    profile_description = Column(Text)
    password = Column(String(255), nullable=False)

    # Relationships
    caregiver = relationship(
        'Caregiver', back_populates='user', uselist=False, cascade='all, delete-orphan')
    member = relationship('Member', back_populates='user',
                          uselist=False, cascade='all, delete-orphan')


class Caregiver(db.Model):
    __tablename__ = 'caregiver'
    __table_args__ = (
        CheckConstraint(
            "caregiving_type IN ('babysitter', 'caregiver for elderly', 'playmate for children')",
            name='check_caregiving_type'
        ),
    )
    caregiver_user_id = Column(Integer, ForeignKey(
        'users.user_id', ondelete='CASCADE'), primary_key=True)
    photo = Column(String(255))
    gender = Column(String(10))
    caregiving_type = Column(String(50), nullable=False)
    hourly_rate = Column(Numeric(6, 2), nullable=False)

    # Relationships
    user = relationship('Users', back_populates='caregiver')
    appointments = relationship(
        'Appointment', back_populates='caregiver', cascade='all, delete-orphan')
    job_applications = relationship(
        'JobApplication', back_populates='caregiver', cascade='all, delete-orphan')

    @validates('caregiving_type')
    def validate_caregiving_type(self, key: str, value: str) -> str:
        """Validate caregiving_type against allowed values"""
        if value not in CAREGIVING_TYPES:
            raise ValueError(
                f"caregiving_type must be one of {CAREGIVING_TYPES}, got '{value}'")
        return value


class Member(db.Model):
    __tablename__ = 'member'
    member_user_id = Column(Integer, ForeignKey(
        'users.user_id', ondelete='CASCADE'), primary_key=True)
    house_rules = Column(Text)
    dependent_description = Column(Text)

    # Relationships
    user = relationship('Users', back_populates='member')
    address = relationship('Address', back_populates='member',
                           uselist=False, cascade='all, delete-orphan')
    jobs = relationship('Job', back_populates='member',
                        cascade='all, delete-orphan')
    appointments = relationship(
        'Appointment', back_populates='member', cascade='all, delete-orphan')


class Address(db.Model):
    __tablename__ = 'address'
    member_user_id = Column(Integer, ForeignKey(
        'member.member_user_id', ondelete='CASCADE'), primary_key=True)
    house_number = Column(String(10), nullable=False)
    street = Column(String(100), nullable=False)
    town = Column(String(100), nullable=False)

    # Relationships
    member = relationship('Member', back_populates='address')


class Job(db.Model):
    __tablename__ = 'job'
    __table_args__ = (
        CheckConstraint(
            "required_caregiving_type IN ('babysitter', 'caregiver for elderly', 'playmate for children')",
            name='check_required_caregiving_type'
        ),
    )
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    member_user_id = Column(Integer, ForeignKey(
        'member.member_user_id', ondelete='CASCADE'), nullable=False)
    required_caregiving_type = Column(String(50), nullable=False)
    other_requirements = Column(Text)
    date_posted = Column(Date, nullable=False, default=date.today)

    # Relationships
    member = relationship('Member', back_populates='jobs')
    applications = relationship(
        'JobApplication', back_populates='job', cascade='all, delete-orphan')

    @validates('required_caregiving_type')
    def validate_required_caregiving_type(self, key: str, value: str) -> str:
        """Validate required_caregiving_type against allowed values"""
        if value not in CAREGIVING_TYPES:
            raise ValueError(
                f"required_caregiving_type must be one of {CAREGIVING_TYPES}, got '{value}'")
        return value


class JobApplication(db.Model):
    __tablename__ = 'job_application'
    caregiver_user_id = Column(Integer, ForeignKey(
        'caregiver.caregiver_user_id', ondelete='CASCADE'), primary_key=True)
    job_id = Column(Integer, ForeignKey(
        'job.job_id', ondelete='CASCADE'), primary_key=True)
    date_applied = Column(Date, nullable=False, default=date.today)

    # Relationships
    caregiver = relationship('Caregiver', back_populates='job_applications')
    job = relationship('Job', back_populates='applications')


class Appointment(db.Model):
    __tablename__ = 'appointment'
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'declined')",
            name='check_appointment_status'
        ),
        CheckConstraint(
            "work_hours > 0 AND work_hours <= 24",
            name='check_work_hours_positive'
        ),
    )
    appointment_id = Column(Integer, primary_key=True, autoincrement=True)
    caregiver_user_id = Column(Integer, ForeignKey(
        'caregiver.caregiver_user_id', ondelete='CASCADE'), nullable=False)
    member_user_id = Column(Integer, ForeignKey(
        'member.member_user_id', ondelete='CASCADE'), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    work_hours = Column(Numeric(4, 1), nullable=False)
    status = Column(String(20), nullable=False, default='pending')

    # Relationships
    caregiver = relationship('Caregiver', back_populates='appointments')
    member = relationship('Member', back_populates='appointments')

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate status against allowed values"""
        if value not in APPOINTMENT_STATUSES:
            raise ValueError(
                f"status must be one of {APPOINTMENT_STATUSES}, got '{value}'")
        return value

    @validates('work_hours')
    def validate_work_hours(self, key: str, value: float) -> float:
        """Validate work hours - must be positive and not exceed 24 hours"""
        if value <= 0:
            raise ValueError("Work hours must be a positive number.")
        if value > 24:
            raise ValueError("Work hours cannot exceed 24 hours.")
        return value
