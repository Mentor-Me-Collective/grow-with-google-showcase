import pytest
import models
from seed import seed_database, WORKERS_DATA, MANAGER_DATA, PROJECT_TITLE

def test_seed_database(db):
    result = seed_database(db=db, reset=True)
    
    assert result["manager_id"] is not None
    assert result["project_id"] is not None
    assert result["workers_count"] == 15
    assert result["shifts_created"] == 15

    # Verify Manager
    manager = db.query(models.User).filter(models.User.email == MANAGER_DATA["email"]).first()
    assert manager is not None
    assert manager.id == result["manager_id"]

    # Verify Workers
    workers = db.query(models.User).filter(models.User.email != MANAGER_DATA["email"]).all()
    assert len(workers) == 15

    # Verify Project
    project = db.query(models.Project).filter(models.Project.title == PROJECT_TITLE).first()
    assert project is not None
    assert project.manager_id == manager.id
    assert len(project.workers) == 15

    # Verify Shifts
    shifts = db.query(models.Shift).filter(models.Shift.project_id == project.id).all()
    assert len(shifts) == 15

    # Test Idempotency (calling seed again without reset should not duplicate)
    result_idempotent = seed_database(db=db, reset=False)
    assert result_idempotent["workers_count"] == 15
    assert result_idempotent["shifts_created"] == 0

    total_users = db.query(models.User).count()
    assert total_users == 16  # 1 manager + 15 workers
