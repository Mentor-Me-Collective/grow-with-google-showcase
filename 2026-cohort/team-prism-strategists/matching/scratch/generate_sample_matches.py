import os
import sys
import datetime
import random
import uuid
import pandas as pd

# Add matching directory to path
matching_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(matching_dir)

from backend.database import SessionLocal
from backend import models, auth
from matching_algorithm_v1 import compute_match_score, match_quality_label

def populate_sample_matches():
    from backend.seed import seed_db
    print("Re-seeding database tables with gender fields...")
    seed_db(force_recreate=True)
    
    db = SessionLocal()
    print("Querying seeded mentees and mentors...")
    mentees = db.query(models.Mentee).join(models.User).filter(
        models.User.email.like("%@mentoring-me.demo%")
    ).limit(20).all()
    
    female_mentors = db.query(models.Mentor).join(models.User).filter(
        models.User.email.like("%@mentoring-me.demo%"),
        models.Mentor.gender == "Woman"
    ).limit(25).all()
    
    male_mentors = db.query(models.Mentor).join(models.User).filter(
        models.User.email.like("%@mentoring-me.demo%"),
        models.Mentor.gender == "Man"
    ).limit(25).all()
    
    mentors = female_mentors + male_mentors
    random.shuffle(mentors)
    
    print(f"Found {len(mentees)} sample mentees and {len(mentors)} sample mentors (Female: {len(female_mentors)}, Male: {len(male_mentors)}).")
    
    statuses = ["ACCEPTED", "ACCEPTED", "ACCEPTED", "REQUESTED", "DECLINED"]
    matches_created = 0
    
    for mentee in mentees:
        # Compute match scores for top 3 mentors for each mentee
        mentor_scores = []
        for mentor in mentors:
            mentee_dict = {
                'DevType': mentee.dev_type or '',
                'YearsCodePro': mentee.years_code_pro or 1.0,
                'exp_tier': mentee.exp_tier or '0-2y',
                'JobFactors': mentee.job_factors or '',
                'OrgSize': mentee.org_size or ''
            }
            mentor_dict = {
                'DevType': mentor.dev_type or '',
                'YearsCodePro': mentor.years_code_pro or 5.0,
                'exp_tier': mentor.exp_tier or '5-10y',
                'JobFactors': mentor.job_factors or '',
                'OrgSize': mentor.org_size or ''
            }
            score, breakdown = compute_match_score(mentee_dict, mentor_dict)
            mentor_scores.append((mentor, score, breakdown))
            
        # Pick top 2 mentors
        mentor_scores.sort(key=lambda x: x[1], reverse=True)
        top_pairs = mentor_scores[:2]
        
        for mentor, score, breakdown in top_pairs:
            match_id = str(uuid.uuid4())
            status = random.choice(statuses)
            created_dt = datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 30))
            
            # Check if match already exists
            existing = db.query(models.Match).filter(
                models.Match.mentee_id == mentee.id,
                models.Match.mentor_id == mentor.id
            ).first()
            
            if not existing:
                match = models.Match(
                    id=match_id,
                    mentee_id=mentee.id,
                    mentor_id=mentor.id,
                    role_score=breakdown['role'],
                    experience_score=breakdown['experience'],
                    career_stage_score=breakdown['career_stage'],
                    goals_score=breakdown['goals'],
                    practical_score=breakdown['practical'],
                    total_score=score,
                    match_quality=match_quality_label(score),
                    status=status,
                    created_at=created_dt
                )
                db.add(match)
                matches_created += 1
                
                # Add sample mentorship notes / milestones for accepted connections
                if status == "ACCEPTED":
                    note = models.MentorshipNote(
                        id=str(uuid.uuid4()),
                        mentor_id=mentor.id,
                        mentee_id=mentee.id,
                        title=f"1-on-1 Strategy Session & Career Review",
                        session_date=created_dt + datetime.timedelta(days=2),
                        topics_covered="Discussed technical onboarding, architecture patterns, and portfolio projects.",
                        action_items="Complete code review checklist & update LinkedIn profile.",
                        milestone_status=random.choice(["COMPLETED", "IN_PROGRESS"]),
                        created_at=created_dt,
                        updated_at=created_dt
                    )
                    db.add(note)

    db.commit()
    print(f"Successfully created {matches_created} realistic match records and mentorship session logs!")
    db.close()

if __name__ == '__main__':
    populate_sample_matches()
