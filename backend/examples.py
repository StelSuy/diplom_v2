"""
Examples of using the TimeTracker API with Python requests library.

Install requirements:
    pip install requests

Usage:
    python examples.py
"""
import requests
from datetime import date, datetime, timedelta
import json


BASE_URL = "http://localhost:8000/api"


class TimeTrackerClient:
    """Client for TimeTracker API."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
    
    def login(self, username: str = "admin", password: str = "admin123") -> str:
        """Get access token."""
        resp = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        resp.raise_for_status()
        self.token = resp.json()["access_token"]
        return self.token
    
    @property
    def headers(self):
        """Get headers with auth token."""
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}
    
    # Employees
    
    def get_employees(self):
        """Get all employees."""
        resp = requests.get(f"{self.base_url}/employees", headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def create_employee(self, full_name: str, nfc_uid: str, position: str = None):
        """Create new employee."""
        data = {
            "full_name": full_name,
            "nfc_uid": nfc_uid,
        }
        if position:
            data["position"] = position
        
        resp = requests.post(
            f"{self.base_url}/employees",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    # Schedules
    
    def get_schedule(self, date_from: date, date_to: date, employee_id: int = None):
        """Get schedule for date range."""
        params = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        }
        if employee_id:
            params["employee_id"] = employee_id
        
        resp = requests.get(
            f"{self.base_url}/schedule",
            headers=self.headers,
            params=params
        )
        resp.raise_for_status()
        return resp.json()
    
    def set_schedule_cell(
        self, 
        employee_id: int, 
        day: date, 
        code: str = None,
        start_hhmm: str = None,
        end_hhmm: str = None
    ):
        """Set schedule cell (create or update)."""
        data = {
            "employee_id": employee_id,
            "day": day.isoformat(),
        }
        
        if code is not None:
            data["code"] = code
        if start_hhmm:
            data["start_hhmm"] = start_hhmm
        if end_hhmm:
            data["end_hhmm"] = end_hhmm
        
        resp = requests.post(
            f"{self.base_url}/schedule/cell",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    def clear_schedule_cell(self, employee_id: int, day: date):
        """Clear schedule cell (delete)."""
        return self.set_schedule_cell(employee_id, day, code="")
    
    # Statistics
    
    def get_employee_stats(self, employee_id: int):
        """Get employee work time statistics."""
        resp = requests.get(
            f"{self.base_url}/stats/employee/{employee_id}",
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.json()
    
    def get_daily_stats(self, employee_id: int, from_date: date, to_date: date):
        """Get daily statistics for employee."""
        params = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        }
        resp = requests.get(
            f"{self.base_url}/stats/employee/{employee_id}/daily",
            headers=self.headers,
            params=params
        )
        resp.raise_for_status()
        return resp.json()


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===\n")
    
    client = TimeTrackerClient()
    
    # 1. Login
    print("1. Logging in...")
    token = client.login()
    print(f"   Token: {token[:20]}...\n")
    
    # 2. Get employees
    print("2. Getting employees...")
    employees = client.get_employees()
    print(f"   Found {len(employees)} employees")
    for emp in employees[:3]:
        print(f"   - {emp['full_name']} (ID: {emp['id']})")
    print()
    
    # 3. Get schedule
    print("3. Getting schedule for this month...")
    today = date.today()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    schedule = client.get_schedule(first_day, last_day)
    print(f"   Found {len(schedule['items'])} schedule entries")
    print()


def example_schedule_management():
    """Schedule management example."""
    print("=== Schedule Management Example ===\n")
    
    client = TimeTrackerClient()
    client.login()
    
    employees = client.get_employees()
    if not employees:
        print("No employees found!")
        return
    
    emp_id = employees[0]['id']
    today = date.today()
    
    # Create schedule with code format
    print(f"1. Setting schedule for employee {emp_id} with code '8-17'...")
    result = client.set_schedule_cell(emp_id, today, code="8-17")
    print(f"   Saved: {result['start_hhmm']} - {result['end_hhmm']}\n")
    
    # Create schedule with explicit time
    tomorrow = today + timedelta(days=1)
    print(f"2. Setting schedule for tomorrow with explicit time...")
    result = client.set_schedule_cell(
        emp_id, 
        tomorrow, 
        start_hhmm="09:00", 
        end_hhmm="18:00",
        code="ОФ"
    )
    print(f"   Saved: {result['start_hhmm']} - {result['end_hhmm']} (code: {result['code']})\n")
    
    # Get schedule
    print("3. Getting schedule...")
    schedule = client.get_schedule(today, tomorrow, employee_id=emp_id)
    print(f"   Schedule items: {len(schedule['items'])}")
    for item in schedule['items']:
        print(f"   - {item['day']}: {item['start_hhmm']}-{item['end_hhmm']} ({item['code'] or 'no code'})")
    print()
    
    # Clear schedule
    print("4. Clearing schedule for today...")
    client.clear_schedule_cell(emp_id, today)
    print("   Cleared!\n")


def example_statistics():
    """Statistics example."""
    print("=== Statistics Example ===\n")
    
    client = TimeTrackerClient()
    client.login()
    
    employees = client.get_employees()
    if not employees:
        print("No employees found!")
        return
    
    emp_id = employees[0]['id']
    
    # Get overall stats
    print(f"1. Getting overall stats for employee {emp_id}...")
    stats = client.get_employee_stats(emp_id)
    print(f"   Total worked: {stats['total_hms']}")
    print(f"   Has open shift: {stats['has_open_shift']}")
    print(f"   Total intervals: {len(stats['intervals'])}")
    print(f"   Anomalies: {len(stats['anomalies'])}")
    print()
    
    # Get daily stats
    print("2. Getting daily stats for this month...")
    today = date.today()
    first_day = today.replace(day=1)
    
    daily = client.get_daily_stats(emp_id, first_day, today)
    print(f"   Total for period: {daily['total_hms']}")
    print(f"   Days with data: {len([d for d in daily['items'] if d['worked_minutes'] > 0])}")
    
    # Show last 5 days
    print("\n   Last 5 days:")
    for item in daily['items'][-5:]:
        if item['worked_minutes'] > 0:
            print(f"   - {item['date_local']}: {item['worked_hms']}")
    print()


def example_error_handling():
    """Error handling example."""
    print("=== Error Handling Example ===\n")
    
    client = TimeTrackerClient()
    client.login()
    
    # Try to create schedule with invalid data
    print("1. Trying to create schedule with invalid time range...")
    try:
        client.set_schedule_cell(
            employee_id=1,
            day=date.today(),
            start_hhmm="17:00",
            end_hhmm="08:00"  # End before start!
        )
    except requests.HTTPError as e:
        print(f"   ✓ Caught error: {e.response.json()['detail']}\n")
    
    # Try to create schedule with invalid code
    print("2. Trying to create schedule with invalid code format...")
    try:
        client.set_schedule_cell(
            employee_id=1,
            day=date.today(),
            code="invalid"  # Should be "H-H"
        )
    except requests.HTTPError as e:
        print(f"   ✓ Caught error: {e.response.json()['detail']}\n")
    
    # Try to access without auth
    print("3. Trying to access API without token...")
    try:
        client.token = None
        client.get_employees()
    except ValueError as e:
        print(f"   ✓ Caught error: {e}\n")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("TimeTracker API Examples")
    print("="*60 + "\n")
    
    try:
        example_basic_usage()
        print("\n" + "-"*60 + "\n")
        
        example_schedule_management()
        print("\n" + "-"*60 + "\n")
        
        example_statistics()
        print("\n" + "-"*60 + "\n")
        
        example_error_handling()
        
    except requests.RequestException as e:
        print(f"\n❌ API Error: {e}")
        print("\nMake sure the server is running:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
