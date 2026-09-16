from locust import HttpUser, task, between
import random

class TicketBuyerUser(HttpUser):
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)

    # Replace with an actual event ID from your database
    TARGET_EVENT_ID = 1 
    # Replace with an actual ticket ID from that event
    TARGET_SPECIFIC_TICKET_ID = 1 

    @task(3)
    def general_admission_buy(self):
        """
        Scenario 1: The General Admission Flow (SKIP LOCKED)
        Users are spamming the "Buy Next Available" button.
        Expectation: High success rate, extremely fast throughput, no deadlocks.
        """
        self.client.post("/api/v1/checkout/reserve-random", json={
            "event_id": self.TARGET_EVENT_ID,
            "user_id": random.randint(1, 1000) # Mock different users
        })

    @task(1)
    def specific_seat_stampede(self):
        """
        Scenario 2: The Taylor Swift Stampede (Optimistic Concurrency)
        Users are all trying to buy the EXACT same seat at the exact same time.
        Expectation: Exactly 1 success (HTTP 200). Everyone else gets HTTP 409 Conflict.
        """
        with self.client.post("/api/v1/checkout/reserve", json={
            "ticket_id": self.TARGET_SPECIFIC_TICKET_ID,
            "user_id": random.randint(1, 1000)
        }, catch_response=True) as response:
            
            # For the stampede, a 409 Conflict is actually a SUCCESSFUL test of our OCC lock!
            if response.status_code == 409:
                response.success()
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
