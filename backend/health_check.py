#!/usr/bin/env python3
"""
System health check script.

Checks:
- Database connection
- All tables exist
- Basic data integrity
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect, text
from app.db.session import engine, SessionLocal
from app.models.employee import Employee
from app.models.terminal import Terminal
from app.models.event import Event
from app.models.schedule import Schedule


def check_database_connection():
    """Check if database is accessible."""
    print("🔍 Checking database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("  ✓ Database connection OK")
        return True
    except Exception as e:
        print(f"  ✗ Database connection FAILED: {e}")
        return False


def check_tables():
    """Check if all required tables exist."""
    print("\n🔍 Checking tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ["employees", "terminals", "events", "schedules"]
    
    all_ok = True
    for table in required_tables:
        if table in tables:
            print(f"  ✓ Table '{table}' exists")
        else:
            print(f"  ✗ Table '{table}' MISSING")
            all_ok = False
    
    return all_ok


def check_data():
    """Check basic data integrity."""
    print("\n🔍 Checking data...")
    db = SessionLocal()
    
    try:
        emp_count = db.query(Employee).count()
        term_count = db.query(Terminal).count()
        event_count = db.query(Event).count()
        schedule_count = db.query(Schedule).count()
        
        print(f"  📊 Employees: {emp_count}")
        print(f"  📊 Terminals: {term_count}")
        print(f"  📊 Events: {event_count}")
        print(f"  📊 Schedules: {schedule_count}")
        
        if emp_count == 0:
            print("  ⚠️  No employees found - run seed data?")
        if term_count == 0:
            print("  ⚠️  No terminals found - run seed data?")
        
        return True
    except Exception as e:
        print(f"  ✗ Data check FAILED: {e}")
        return False
    finally:
        db.close()


def check_indexes():
    """Check if critical indexes exist."""
    print("\n🔍 Checking indexes...")
    inspector = inspect(engine)
    
    critical_indexes = {
        "employees": ["ix_employees_nfc_uid"],
        "events": ["ix_events_employee_id", "ix_events_ts"],
        "schedules": ["ix_schedules_day"],
    }
    
    all_ok = True
    for table, required_indexes in critical_indexes.items():
        indexes = inspector.get_indexes(table)
        index_names = [idx['name'] for idx in indexes]
        
        for idx_name in required_indexes:
            if idx_name in index_names:
                print(f"  ✓ Index '{idx_name}' on '{table}'")
            else:
                print(f"  ✗ Index '{idx_name}' MISSING on '{table}'")
                all_ok = False
    
    return all_ok


def main():
    print("="*60)
    print("🏥 SYSTEM HEALTH CHECK")
    print("="*60)
    
    checks = [
        check_database_connection(),
        check_tables(),
        check_data(),
        check_indexes(),
    ]
    
    print("\n" + "="*60)
    if all(checks):
        print("✓ ALL CHECKS PASSED - System is healthy!")
        print("="*60)
        return 0
    else:
        print("✗ SOME CHECKS FAILED - Please review above")
        print("\nTo fix issues:")
        print("  1. Run: python init_db.py")
        print("  2. Or run: alembic upgrade head")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
