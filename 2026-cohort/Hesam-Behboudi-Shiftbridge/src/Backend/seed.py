"""Database seeding script for ShiftBridge.

Creates:
- 1 Manager worker (with is_manager=True)
- 15 Workers with specific emails, roles, departments, avatars, and hour metrics
- 3 Projects with the manager worker and workers assigned via association table
- Realistic scheduled shifts for workers across days of the week, with
  role/department-specific patterns and 2 shifts for worker1 in 2 projects.
"""
import sys
from typing import Optional
from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base
import models
import security

WORKERS_DATA = [
    {"id": "w1", "email": "worker1@shiftbridge.com", "name": "Alex Morgan", "role": "Senior RN", "department": "Emergency", "max_hours": 40.0, "current_hours": 32.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Alex", "is_manager": False},
    {"id": "w2", "email": "worker2@shiftbridge.com", "name": "Brian Davis", "role": "RN", "department": "ICU", "max_hours": 40.0, "current_hours": 36.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Brian", "is_manager": False},
    {"id": "w3", "email": "worker3@shiftbridge.com", "name": "Chloe Bennett", "role": "Charge Nurse", "department": "Emergency", "max_hours": 40.0, "current_hours": 40.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Chloe", "is_manager": False},
    {"id": "w4", "email": "worker4@shiftbridge.com", "name": "David Miller", "role": "LPN", "department": "Pediatrics", "max_hours": 36.0, "current_hours": 24.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=David", "is_manager": False},
    {"id": "w5", "email": "worker5@shiftbridge.com", "name": "Elena Rostova", "role": "RN", "department": "Surgery", "max_hours": 40.0, "current_hours": 38.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Elena", "is_manager": False},
    {"id": "w6", "email": "worker6@shiftbridge.com", "name": "Felix Vance", "role": "Support Specialist", "department": "General", "max_hours": 30.0, "current_hours": 20.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix", "is_manager": False},
    {"id": "w7", "email": "worker7@shiftbridge.com", "name": "Grace Hopper", "role": "Senior RN", "department": "ICU", "max_hours": 40.0, "current_hours": 40.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Grace", "is_manager": False},
    {"id": "w8", "email": "worker8@shiftbridge.com", "name": "Hector Santos", "role": "RN", "department": "Pediatrics", "max_hours": 40.0, "current_hours": 32.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Hector", "is_manager": False},
    {"id": "w9", "email": "worker9@shiftbridge.com", "name": "Iris Chen", "role": "Charge Nurse", "department": "Surgery", "max_hours": 40.0, "current_hours": 36.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Iris", "is_manager": False},
    {"id": "w10", "email": "worker10@shiftbridge.com", "name": "James Wilson", "role": "LPN", "department": "Emergency", "max_hours": 36.0, "current_hours": 28.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=James", "is_manager": False},
    {"id": "w11", "email": "worker11@shiftbridge.com", "name": "Kavita Patel", "role": "RN", "department": "General", "max_hours": 40.0, "current_hours": 34.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Kavita", "is_manager": False},
    {"id": "w12", "email": "worker12@shiftbridge.com", "name": "Liam O'Connor", "role": "Support Specialist", "department": "ICU", "max_hours": 30.0, "current_hours": 25.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Liam", "is_manager": False},
    {"id": "w13", "email": "worker13@shiftbridge.com", "name": "Maya Lin", "role": "Senior RN", "department": "Pediatrics", "max_hours": 40.0, "current_hours": 38.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Maya", "is_manager": False},
    {"id": "w14", "email": "worker14@shiftbridge.com", "name": "Noah Taylor", "role": "RN", "department": "Emergency", "max_hours": 40.0, "current_hours": 30.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Noah", "is_manager": False},
    {"id": "w15", "email": "worker15@shiftbridge.com", "name": "Olivia Martinez", "role": "LPN", "department": "Surgery", "max_hours": 36.0, "current_hours": 32.0, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Olivia", "is_manager": False},
]

MANAGER_DATA = {
    "id": "m1",
    "email": "manager@shiftbridge.com",
    "name": "Sarah Connor",
    "role": "Project Manager",
    "department": "Management",
    "max_hours": 40.0,
    "current_hours": 0.0,
    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
    "is_manager": True
}

PROJECTS_DATA = [
    {
        "id": "proj_1",
        "title": "Metropolis Healthcare Scheduling",
        "worker_ids": [w["id"] for w in WORKERS_DATA],
    },
    {
        "id": "proj_2",
        "title": "Critical Care & ICU Rotation",
        "worker_ids": ["w1", "w2", "w3", "w5", "w7", "w9", "w12"],
    },
    {
        "id": "proj_3",
        "title": "Pediatrics & Outpatient Clinic",
        "worker_ids": ["w4", "w6", "w8", "w10", "w11", "w13", "w14", "w15"],
    },
]

DEFAULT_PASSWORD = "password123"
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ---------------------------------------------------------------------------
# Shift templates. Each template = (type, start_time, length_hours).
# Chosen so total weekly hours stay under the worker's max_hours.
# ---------------------------------------------------------------------------
SHIFT_TEMPLATES = {
    # 12-hour ICU/ER rotations
    "day12":   {"type": "regular", "start_time": "07:00", "length": 12.0},
    "night12": {"type": "night",   "start_time": "19:00", "length": 12.0},
    # 8-hour hospital shifts
    "day8":    {"type": "regular", "start_time": "07:00", "length": 8.0},
    "eve8":    {"type": "regular", "start_time": "15:00", "length": 8.0},
    "night8":  {"type": "night",   "start_time": "23:00", "length": 8.0},
    # Part-time / support blocks
    "am4":     {"type": "regular", "start_time": "08:00", "length": 4.0},
    "pm4":     {"type": "regular", "start_time": "13:00", "length": 4.0},
    # On-call
    "oncall":  {"type": "on_call", "start_time": "18:00", "length": 6.0},
}

# Per-worker weekly pattern: list of (day, template_key, project_key)
# Keep total hours <= max_hours for each worker.
WORKER_SHIFT_PLANS = {
    "w1":  [("Monday", "day12", "proj_1"), ("Wednesday", "eve8", "proj_2"),
            ("Friday", "day8", "proj_1")],                              # 28h
    "w2":  [("Tuesday", "day12", "proj_2"), ("Thursday", "night12", "proj_2")],  # 24h
    "w3":  [("Monday", "day12", "proj_1"), ("Wednesday", "day12", "proj_1"),
            ("Saturday", "day8", "proj_1")],                            # 32h
    "w4":  [("Tuesday", "day8", "proj_3"), ("Thursday", "eve8", "proj_3")],      # 16h
    "w5":  [("Monday", "day8", "proj_2"), ("Wednesday", "eve8", "proj_2"),
            ("Friday", "day8", "proj_2")],                              # 24h
    "w6":  [("Tuesday", "am4", "proj_3"), ("Thursday", "pm4", "proj_3")],        # 8h
    "w7":  [("Monday", "day12", "proj_2"), ("Thursday", "night12", "proj_2"),
            ("Saturday", "day12", "proj_2")],                           # 36h
    "w8":  [("Tuesday", "day8", "proj_3"), ("Friday", "eve8", "proj_3")],        # 16h
    "w9":  [("Monday", "day8", "proj_2"), ("Wednesday", "day8", "proj_2"),
            ("Friday", "eve8", "proj_2")],                              # 24h
    "w10": [("Tuesday", "day8", "proj_1"), ("Thursday", "eve8", "proj_1")],      # 16h
    "w11": [("Monday", "day8", "proj_3"), ("Wednesday", "day8", "proj_3")],      # 16h
    "w12": [("Tuesday", "am4", "proj_2"), ("Thursday", "pm4", "proj_2")],        # 8h
    "w13": [("Monday", "day8", "proj_3"), ("Wednesday", "eve8", "proj_3"),
            ("Friday", "day8", "proj_3")],                              # 24h
    "w14": [("Tuesday", "day12", "proj_1"), ("Saturday", "night12", "proj_1")],  # 24h
    "w15": [("Monday", "eve8", "proj_1"), ("Thursday", "day8", "proj_1")],       # 16h
}


def _shift_note(worker, template_key, project, day):
    dept = worker.department
    base = {
        "day12":   f"12-hour day rotation ({dept})",
        "night12": f"12-hour night rotation ({dept})",
        "day8":    f"Day shift — {dept}",
        "eve8":    f"Evening shift — {dept}",
        "night8":  f"Overnight shift — {dept}",
        "am4":     f"Morning support block — {dept}",
        "pm4":     f"Afternoon support block — {dept}",
        "oncall":  f"On-call coverage — {dept}",
    }[template_key]
    return f"{base} on {project.title}"


def seed_database(db: Optional[Session] = None, reset: bool = False):
    """Seed the database with 1 manager worker, 15 workers, 3 projects, and shifts."""
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        if reset:
            print("Resetting and dropping database tables...")
            Base.metadata.drop_all(bind=engine)

        Base.metadata.create_all(bind=engine)

        # 1. Manager
        manager = db.query(models.Worker).filter(
            models.Worker.email == MANAGER_DATA["email"]
        ).first()
        if not manager:
            manager = models.Worker(
                id=MANAGER_DATA["id"],
                email=MANAGER_DATA["email"],
                hashed_password=security.get_password_hash(DEFAULT_PASSWORD),
                name=MANAGER_DATA["name"],
                role=MANAGER_DATA["role"],
                department=MANAGER_DATA["department"],
                max_hours=MANAGER_DATA["max_hours"],
                current_hours=MANAGER_DATA["current_hours"],
                avatar=MANAGER_DATA["avatar"],
                is_manager=True,
            )
            db.add(manager)
            db.commit()
            db.refresh(manager)
            print(f"Created Manager Worker: {manager.name} ({manager.email}) [ID: {manager.id}]")
        else:
            manager.is_manager = True
            db.commit()
            print(f"Manager Worker already exists: {manager.email} [ID: {manager.id}]")

        # 2. Workers
        workers_by_id = {}
        workers = []
        for w_data in WORKERS_DATA:
            worker = db.query(models.Worker).filter(models.Worker.id == w_data["id"]).first()
            if not worker:
                worker = models.Worker(
                    id=w_data["id"],
                    email=w_data["email"],
                    hashed_password=security.get_password_hash(DEFAULT_PASSWORD),
                    name=w_data["name"],
                    role=w_data["role"],
                    department=w_data["department"],
                    max_hours=w_data["max_hours"],
                    current_hours=w_data["current_hours"],
                    avatar=w_data["avatar"],
                    is_manager=False,
                )
                db.add(worker)
                db.commit()
                db.refresh(worker)
                print(f"Created Worker: {worker.name} ({worker.role}) [ID: {worker.id}]")
            else:
                worker.is_manager = False
                db.commit()
                print(f"Worker already exists: {worker.name} [ID: {worker.id}]")
            workers.append(worker)
            workers_by_id[worker.id] = worker

        # 3. Projects
        projects = []
        for p_data in PROJECTS_DATA:
            assigned_workers = [workers_by_id[wid] for wid in p_data["worker_ids"] if wid in workers_by_id]
            project = db.query(models.Project).filter(models.Project.id == p_data["id"]).first()
            if not project:
                project = models.Project(
                    id=p_data["id"],
                    manager_id=manager.id,
                    title=p_data["title"],
                    workers=assigned_workers,
                )
                db.add(project)
                db.commit()
                db.refresh(project)
                print(f"\nCreated Project: '{project.title}' [ID: {project.id}]")
            else:
                existing_worker_ids = {w.id for w in project.workers}
                for w in assigned_workers:
                    if w.id not in existing_worker_ids:
                        project.workers.append(w)
                project.manager_id = manager.id
                db.commit()
                db.refresh(project)
                print(f"\nProject '{project.title}' already exists [ID: {project.id}]")
            projects.append(project)

        projects_by_id = {p.id: p for p in projects}

        # 4. Realistic shifts, derived from per-worker plans
        shifts_created = 0
        shifts_skipped = 0
        hours_by_worker = {}  # worker_id -> total seeded hours

        for worker_id, plan in WORKER_SHIFT_PLANS.items():
            worker = workers_by_id.get(worker_id)
            if not worker:
                continue
            # Guard against over-scheduling
            planned_hours = 0.0
            for day, tpl_key, proj_key in plan:
                tpl = SHIFT_TEMPLATES[tpl_key]
                project = projects_by_id[proj_key]
                shift_id = f"shift_{worker.id}_{proj_key}_{day.lower()}"
                planned_hours += tpl["length"]

                existing = db.query(models.Shift).filter(models.Shift.id == shift_id).first()
                if existing:
                    shifts_skipped += 1
                    continue

                shift = models.Shift(
                    id=shift_id,
                    project_id=proj_key,
                    worker_id=worker.id,
                    day=day,
                    type=tpl["type"],
                    start_time=tpl["start_time"],
                    length=tpl["length"],
                    note=_shift_note(worker, tpl_key, project, day),
                    updated_by_ai=False,
                    conflict_reason="",
                )
                db.add(shift)
                shifts_created += 1

            if planned_hours > worker.max_hours:
                print(f"  WARNING: {worker.name} planned {planned_hours}h "
                      f"> max_hours {worker.max_hours}h")

            hours_by_worker[worker.id] = planned_hours

        if shifts_created:
            db.commit()

        # Reflect scheduled hours back onto workers so dashboard numbers match shifts
        for worker_id, hrs in hours_by_worker.items():
            worker = workers_by_id[worker_id]
            # Only overwrite if the seeded plan is the source of truth
            worker.current_hours = min(hrs, worker.max_hours)
        db.commit()

        print(f"\nCreated {shifts_created} scheduled shifts "
              f"({shifts_skipped} already existed).")

        print("\n" + "=" * 60)
        print("SEEDING COMPLETE!")
        print("=" * 60)
        print(f"Projects seeded: {len(projects)}")
        print(f"Manager: {manager.email} | Password: {DEFAULT_PASSWORD}")
        print(f"Workers: {len(workers)} workers created/assigned")
        print("=" * 60)

        return {
            "manager_id": manager.id,
            "project_ids": [p.id for p in projects],
            "workers_count": len(workers),
            "shifts_created": shifts_created,
        }

    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    should_reset = "--reset" in sys.argv
    seed_database(reset=should_reset)