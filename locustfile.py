"""
Load testing script for TaxMate AI using Locust

Usage:
    Web UI: locust -f locustfile.py --host=http://localhost:5000
    Command line: locust -f locustfile.py --host=http://localhost:5000 -u 100 -r 10 -t 10m --headless
    
    -u: Number of users
    -r: Spawn rate (users per second)
    -t: Test duration (10m = 10 minutes)
"""

from locust import HttpUser, task, between, events
from random import randint, choice
import json
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaxMateUser(HttpUser):
    """Simulated TaxMate AI user"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_email = None
        self.user_password = os.getenv("LOAD_TEST_PASSWORD", "TestOnly-Load-123!")
        self.user_id = None
        self.filing_id = None
    
    def on_start(self):
        """Called when user starts"""
        # Generate unique user for this session
        self.user_email = f"user_{randint(1000, 9999999)}@taxmate.test"
        self.register_user()
        self.login()
    
    def on_stop(self):
        """Called when user stops"""
        if self.user_id:
            self.logout()
    
    def register_user(self):
        """Register a new user"""
        try:
            response = self.client.post(
                "/api/auth/register",
                json={
                    "email": self.user_email,
                    "name": "Test User",
                    "phone": "9876543210",
                    "pan": "ABCDE1234F",
                    "age": 35,
                    "state": "Maharashtra",
                    "password": self.user_password
                },
                catch_response=True
            )
            
            if response.status_code == 200:
                self.user_id = response.json().get("id")
                response.success()
            else:
                response.failure(f"Registration failed: {response.status_code}")
                logger.warning(f"Registration failed: {response.text}")
        except Exception as e:
            logger.error(f"Registration error: {e}")
    
    def login(self):
        """Login user"""
        try:
            response = self.client.post(
                "/api/auth/login",
                json={
                    "username": self.user_email,
                    "password": self.user_password
                },
                catch_response=True
            )
            
            if response.status_code == 200:
                response.success()
                logger.info(f"User {self.user_email} logged in")
            else:
                response.failure(f"Login failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Login error: {e}")
    
    def logout(self):
        """Logout user"""
        try:
            self.client.post(
                "/api/auth/logout",
                catch_response=True
            )
        except Exception as e:
            logger.error(f"Logout error: {e}")
    
    @task(3)
    def view_profile(self):
        """View user profile"""
        self.client.get(
            "/api/auth/me",
            name="/api/auth/me"
        )
    
    @task(5)
    def create_tax_filing(self):
        """Create a new tax filing"""
        filing_data = {
            "filing_year": 2024,
            "income_data": {
                "salary": randint(500000, 2000000),
                "interest": randint(0, 100000),
                "dividend": randint(0, 100000),
                "rental_income": randint(0, 50000),
                "professional_fees": 0
            },
            "deductions_data": {
                "investments": randint(0, 150000),
                "health_insurance": randint(0, 50000),
                "education_loan_interest": 0,
                "home_loan_interest": randint(0, 200000),
                "donations": randint(0, 50000),
                "medical_expenses": 0,
                "other": 0
            },
            "tds_paid": randint(0, 200000),
            "advance_tax_paid": randint(0, 100000)
        }
        
        response = self.client.post(
            "/api/tax/filings",
            json=filing_data,
            name="/api/tax/filings",
            catch_response=True
        )
        
        if response.status_code == 200:
            self.filing_id = response.json().get("id")
            response.success()
        else:
            response.failure(f"Filing creation failed: {response.status_code}")
    
    @task(4)
    def list_tax_filings(self):
        """List user's tax filings"""
        self.client.get(
            "/api/tax/filings",
            name="/api/tax/filings"
        )
    
    @task(2)
    def analyze_tax_filing(self):
        """Analyze a tax filing"""
        if self.filing_id:
            response = self.client.post(
                f"/api/tax/filings/{self.filing_id}/analyze",
                name="/api/tax/filings/[id]/analyze",
                catch_response=True
            )
            
            if response.status_code != 200:
                response.failure(f"Analysis failed: {response.status_code}")
            else:
                response.success()
    
    @task(1)
    def get_dashboard_data(self):
        """Get dashboard data"""
        self.client.get(
            "/api/dashboard",
            name="/api/dashboard",
            catch_response=True
        )
    
    @task(1)
    def check_health(self):
        """Check API health"""
        self.client.get(
            "/health",
            name="/health"
        )


# Event handlers for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    logger.info("=" * 80)
    logger.info("TaxMate AI Load Test Started")
    logger.info(f"Target: {environment.host}")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    logger.info("=" * 80)
    logger.info("TaxMate AI Load Test Completed")
    logger.info("=" * 80)
    
    # Print summary statistics
    print("\n📊 LOAD TEST RESULTS:")
    print("=" * 80)
    
    for name, stats in environment.stats_history.items():
        if hasattr(stats, 'total'):
            total_requests = stats.total.num_requests
            failed = stats.total.num_failures
            avg_response_time = stats.total.avg_response_time
            
            print(f"\n{name}")
            print(f"  Total Requests: {total_requests}")
            print(f"  Failed: {failed}")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("Load testing script for TaxMate AI")
    print("=" * 80)
    print("Usage:")
    print("  Web UI:       locust -f locustfile.py --host=http://localhost:5000")
    print("  Headless:     locust -f locustfile.py --host=http://localhost:5000 -u 100 -r 10 -t 10m --headless")
    print("=" * 80)
