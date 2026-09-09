import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend import models, auth
import uuid

db = SessionLocal()

showcase_mentors = [
    {
        'email': 'amanda.malahlela@mentoring-me.org',
        'name': 'Amanda Malahlela',
        'country': 'South Africa',
        'dev_type': 'Data Analyst;Data Engineer;Database Administrator;Developer, full-stack',
        'years': 6.5,
        'tier': '5-10y',
        'job_factors': 'Opportunities for professional development;Diversity of the company or organization;Flex time or a flexible schedule',
        'org_size': '1,000 to 4,999 employees',
        'gender': 'Woman',
        'is_ally': True,
        'details': 'Data Analytics Lead & Grow with Google Scholar. Passionate about helping women transition into Python data pipelines, SQL modeling, and cloud data warehousing.'
    },
    {
        'email': 'medha.yasa@mentoring-me.org',
        'name': 'Medha Yasa',
        'country': 'United Kingdom',
        'dev_type': 'DevOps specialist;Engineer, site reliability;Developer, back-end;Cloud Infrastructure',
        'years': 7.0,
        'tier': '5-10y',
        'job_factors': 'Opportunities for professional development;Flex time or a flexible schedule;Remote work options',
        'org_size': '500 to 999 employees',
        'gender': 'Woman',
        'is_ally': True,
        'details': 'IT Automation & Cloud Architecture Lead. Specializes in CI/CD automation, Python scripting, Docker containerization, and navigating mid-career promotions.'
    },
    {
        'email': 'martha.afful@mentoring-me.org',
        'name': 'Martha Afful',
        'country': 'Ghana',
        'dev_type': 'Data scientist or machine learning specialist;Developer, back-end;Data Analyst',
        'years': 8.0,
        'tier': '5-10y',
        'job_factors': 'Opportunities for professional development;Diversity of the company or organization;Remote work options',
        'org_size': '100 to 499 employees',
        'gender': 'Woman',
        'is_ally': True,
        'details': 'Advanced Analytics Lead & Senior Mentor. Dedicated to supporting early-career female engineers in statistical algorithm design, machine learning pipelines, and career roadmaps.'
    }
]

for m_data in showcase_mentors:
    existing = db.query(models.User).filter(models.User.email == m_data['email']).first()
    if not existing:
        u = models.User(
            id=str(uuid.uuid4()),
            email=m_data['email'],
            password_hash=auth.get_password_hash('Password123!'),
            name=m_data['name'],
            role='MENTOR',
            is_active=True,
            is_verified=True,
            two_factor_enabled=False
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        
        m_prof = models.Mentor(
            id=u.id,
            name=m_data['name'],
            gender=m_data['gender'],
            country=m_data['country'],
            ed_level="Master's degree",
            dev_type=m_data['dev_type'],
            years_code_pro=m_data['years'],
            exp_tier=m_data['tier'],
            job_factors=m_data['job_factors'],
            org_size=m_data['org_size'],
            is_active=True,
            is_diversity_ally=m_data['is_ally'],
            additional_details=m_data['details']
        )
        db.add(m_prof)
        db.commit()
        print(f"Created showcase mentor: {m_data['name']} ({m_data['email']})")
    else:
        print(f"Showcase mentor already exists: {m_data['name']}")

db.close()
