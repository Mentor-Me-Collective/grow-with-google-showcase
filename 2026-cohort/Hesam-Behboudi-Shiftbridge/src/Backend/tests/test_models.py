import pytest
from datetime import datetime, timedelta
import models

def test_project_and_shift_creation(db):
    # Create manager and workers
    manager = models.User(
        email="manager@example.com",
        hashed_password="fakehashmanager",
        full_name="Manager Alice"
    )
    worker1 = models.User(
        email="worker1@example.com",
        hashed_password="fakehashworker1",
        full_name="Worker Bob"
    )
    worker2 = models.User(
        email="worker2@example.com",
        hashed_password="fakehashworker2",
        full_name="Worker Charlie"
    )
    db.add_all([manager, worker1, worker2])
    db.commit()

    # Create Project with manager_id, title, workers
    project = models.Project(
        manager_id=manager.id,
        title="Main Bridge Construction",
        workers=[worker1, worker2]
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    assert project.id is not None
    assert project.manager_id == manager.id
    assert project.title == "Main Bridge Construction"
    assert len(project.workers) == 2
    assert worker1 in project.workers
    assert worker2 in project.workers
    assert project.manager.email == "manager@example.com"

    # Create Shift with project_id, owner_id, start_date, length
    shift_start = datetime(2026, 11, 7, 8, 0, 0)
    shift = models.Shift(
        project_id=project.id,
        owner_id=worker1.id,
        start_date=shift_start,
        length=8
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)

    assert shift.id is not None
    assert shift.project_id == project.id
    assert shift.owner_id == worker1.id
    assert shift.start_date == shift_start
    assert shift.length == 8

    # Verify relationships
    assert shift.project.title == "Main Bridge Construction"
    assert shift.owner.full_name == "Worker Bob"
    assert len(project.shifts) == 1
    assert project.shifts[0].id == shift.id

    # Verify reverse user relationships
    assert project in worker1.projects
    assert project in manager.managed_projects
    assert shift in worker1.shifts

def test_project_add_workers_dynamically(db):
    manager = models.User(email="mgr2@example.com", hashed_password="pw")
    worker = models.User(email="w3@example.com", hashed_password="pw")
    db.add_all([manager, worker])
    db.commit()

    project = models.Project(manager_id=manager.id, title="Subway Extension")
    db.add(project)
    db.commit()
    assert len(project.workers) == 0

    project.workers.append(worker)
    db.commit()
    db.refresh(project)
    assert len(project.workers) == 1
    assert project.workers[0].email == "w3@example.com"

def test_shift_cascade_delete(db):
    manager = models.User(email="mgr3@example.com", hashed_password="pw")
    worker = models.User(email="w4@example.com", hashed_password="pw")
    db.add_all([manager, worker])
    db.commit()

    project = models.Project(manager_id=manager.id, title="Highway Repair")
    db.add(project)
    db.commit()

    shift = models.Shift(
        project_id=project.id,
        owner_id=worker.id,
        start_date=datetime.now(),
        length=4
    )
    db.add(shift)
    db.commit()

    shift_id = shift.id
    # Delete project, shifts should be cascaded
    db.delete(project)
    db.commit()

    assert db.query(models.Shift).filter(models.Shift.id == shift_id).first() is None
