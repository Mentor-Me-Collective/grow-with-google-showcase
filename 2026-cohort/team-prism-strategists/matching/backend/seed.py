import os
import pandas as pd
import random
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from . import models
from .auth import get_password_hash

# Lists of realistic names for seeding
FEMALE_FIRST_NAMES = [
    "Emily", "Hannah", "Madison", "Ashley", "Sarah", "Alexis", "Samantha", "Jessica", "Elizabeth", "Taylor", 
    "Lauren", "Megan", "Kayla", "Rachel", "Amanda", "Jennifer", "Melissa", "Nicole", "Stephanie",
    "Heather", "Katherine", "Amy", "Angela", "Rebecca", "Michelle", "Laura", "Kimberly", "Christina", "Patricia"
]
GENERAL_FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
    "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", 
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", 
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
]

def seed_db(force_recreate: bool = False):
    print("Initializing database tables...")
    # Always ensure tables exist (safe, uses checkfirst=True internally)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    if force_recreate:
        # On PostgreSQL, drop_all + create_all causes a UniqueViolation on pg_type.
        # Instead, safely clear all seeded data by deleting rows, preserving schema.
        print("Clearing existing seeded data (truncating rows)...")
        try:
            db.query(models.MentorshipNote).delete(synchronize_session=False)
            db.query(models.Match).delete(synchronize_session=False)
            db.query(models.Mentee).delete(synchronize_session=False)
            db.query(models.Mentor).delete(synchronize_session=False)
            # Delete all non-admin seeded users (those with @mentoring-me.demo emails except admin)
            db.query(models.User).filter(
                models.User.email.like("%@mentoring-me.demo%"),
                models.User.role != "ADMIN"
            ).delete(synchronize_session=False)
            db.commit()
            print("Existing seeded data cleared.")
        except Exception as e:
            db.rollback()
            print(f"Warning: Could not clear data: {e}")
    
    # Locate the CSV file
    csv_paths = [
        'so2020_cleaned.csv', 
        'so2020.csv', 
        'matching/so2020.csv', 
        'matching/so2020_cleaned.csv',
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'so2020_cleaned.csv'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'so2020.csv')
    ]
    csv_path = None
    for path in csv_paths:
        if os.path.exists(path):
            csv_path = path
            break
            
    if not csv_path:
        print("Error: Could not find survey CSV file to seed from.")
        return
        
    print(f"Reading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Total rows in CSV: {df.shape[0]}")
    
    # Clean fields and set defaults
    df['YearsCodePro'] = pd.to_numeric(df['YearsCodePro'], errors='coerce').fillna(0.0)
    df['DevType'] = df['DevType'].fillna('Not stated')
    df['JobFactors'] = df['JobFactors'].fillna('Not stated')
    df['OrgSize'] = df['OrgSize'].fillna('Not stated')
    df['Country'] = df['Country'].fillna('Not stated')
    df['EdLevel'] = df['EdLevel'].fillna('Not stated')
    
    # Build experience tiers
    def get_exp_tier(years):
        if years <= 2: return '0-2y'
        elif years <= 5: return '2-5y'
        elif years <= 10: return '5-10y'
        elif years <= 20: return '10-20y'
        else: return '20y+'
    
    df['exp_tier'] = df['YearsCodePro'].apply(get_exp_tier)
    
    print("Preparing user profiles...")
    default_pw_hash = get_password_hash("password123")
    
    existing_user_ids = set(u[0] for u in db.query(models.User.id).all())
    existing_user_emails = set(u[0] for u in db.query(models.User.email).all())
    
    users_to_insert = []
    mentees_to_insert = []
    mentors_to_insert = []
    
    mentee_count = len(db.query(models.Mentee).all())
    mentor_count = len(db.query(models.Mentor).all())
    max_to_seed = 1000  # Seed up to 1000 of each to keep database lightweight
    
    for _, row in df.iterrows():
        resp_id = int(row['Respondent'])
        gender = row['Gender']
        exp_years = float(row['YearsCodePro'])
        tier = row['exp_tier']
        
        user_uuid = f"user-uuid-{resp_id}"
        email = f"user_{resp_id}@mentoring-me.demo"
        
        if user_uuid in existing_user_ids or email in existing_user_emails:
            continue
        
        is_mentee = (gender == 'Woman') and (tier in ['0-2y', '5-10y'])
        is_mentor = (exp_years >= 5.0) and not is_mentee
        
        if not is_mentee and not is_mentor:
            continue
            
        role = "MENTEE" if is_mentee else "MENTOR"
        
        if role == "MENTEE":
            if mentee_count >= max_to_seed:
                continue
            mentee_count += 1
        else:
            if mentor_count >= max_to_seed:
                continue
            mentor_count += 1
            
        users_to_insert.append(models.User(
            id=user_uuid,
            email=email,
            password_hash=default_pw_hash,
            role=role
        ))
        
        # Deterministic random seed per user
        random.seed(resp_id)
        
        if role == "MENTEE":
            real_name = f"{random.choice(FEMALE_FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            mentees_to_insert.append(models.Mentee(
                id=user_uuid,
                name=real_name,
                gender="Woman",
                country=row['Country'],
                ed_level=row['EdLevel'],
                dev_type=row['DevType'],
                years_code_pro=exp_years,
                exp_tier=tier,
                job_factors=row['JobFactors'],
                org_size=row['OrgSize']
            ))
        else:
            mentor_gender = "Woman" if gender == "Woman" else "Man"
            if mentor_gender == "Woman":
                first_name = random.choice(FEMALE_FIRST_NAMES)
                is_ally = True
            else:
                first_name = random.choice(GENERAL_FIRST_NAMES)
                is_ally = random.choice([True, True, False])  # High proportion of D&I allies
            real_name = f"{first_name} {random.choice(LAST_NAMES)}"
            mentors_to_insert.append(models.Mentor(
                id=user_uuid,
                name=real_name,
                gender=mentor_gender,
                country=row['Country'],
                ed_level=row['EdLevel'],
                dev_type=row['DevType'],
                years_code_pro=exp_years,
                exp_tier=tier,
                job_factors=row['JobFactors'],
                org_size=row['OrgSize'],
                is_active=True,
                is_diversity_ally=is_ally,
                max_mentees=3
            ))
            
    print(f"Bulk saving {len(users_to_insert)} users to database...")
    db.add_all(users_to_insert)
    db.commit()
    
    print(f"Bulk saving {len(mentees_to_insert)} mentees...")
    db.add_all(mentees_to_insert)
    db.commit()
    
    print(f"Bulk saving {len(mentors_to_insert)} mentors...")
    db.add_all(mentors_to_insert)
    db.commit()
    
    # Create admin user if not already present
    admin_exists = db.query(models.User).filter(
        (models.User.email == "admin@mentoring-me.demo") | (models.User.email == "admin@mentorme.demo")
    ).first()
    if not admin_exists:
        admin_uuid = "admin-uuid-001"
        admin_user = models.User(
            id=admin_uuid,
            email="admin@mentoring-me.demo",
            name="Admin Demo",
            password_hash=get_password_hash("adminpassword"),
            role="ADMIN",
            two_factor_enabled=False,
            is_verified=True,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
    
    print("Database seeding complete!")
    print(f"Seeded Mentees: {mentee_count}")
    print(f"Seeded Mentors: {mentor_count}")
    print("Admin Account: admin@mentoring-me.demo / adminpassword")
    print("Sample Account Password: password123")
    db.close()

if __name__ == '__main__':
    seed_db()
