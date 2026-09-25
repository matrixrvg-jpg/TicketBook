from locust import HttpUser, task, between
import random

class TicketBuyerUser(HttpUser):
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)

    # Replace with an actual event ID from your database
    TARGET_EVENT_ID = 19 
    # Replace with an actual ticket ID from that event
    TARGET_SPECIFIC_TICKET_ID = 545 

    def on_start(self):
        """Executed when a simulated user starts."""
        # Pick a random user from our seeded 100 users
        user_id = random.randint(1, 100)
        email = f"loadtest{user_id}@ticketbook.com"
        
        response = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "password123"
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"Failed to login user {email}")
            self.headers = {}

    @task(3)
    def general_admission_buy(self):
        """
        Scenario 1: The General Admission Flow (SKIP LOCKED)
        Users are spamming the "Buy Next Available" button.
        Expectation: High success rate, extremely fast throughput, no deadlocks.
        """
        with self.client.post("/api/v1/checkout/reserve-random", json={
            "event_id": self.TARGET_EVENT_ID
        }, headers=self.headers, catch_response=True) as response:
            if response.status_code == 409:
                response.failure("SKIP LOCKED Rejection: Sold Out or In Carts")
                return
            elif response.status_code == 200:
                ticket_id = response.json().get("ticket_id")
                # 50% of people abandon their cart (let it expire)
                if random.random() > 0.5:
                    self.client.post("/api/v1/checkout/confirm", json={
                        "ticket_id": ticket_id
                    }, headers=self.headers)

    @task(1)
    def specific_seat_stampede(self):
        """
        Scenario 2: The Taylor Swift Stampede (Optimistic Concurrency)
        Users are all trying to buy the EXACT same seat at the exact same time.
        Expectation: Exactly 1 success (HTTP 200). Everyone else gets HTTP 409 Conflict.
        """
        with self.client.post("/api/v1/checkout/reserve", json={
            "ticket_id": self.TARGET_SPECIFIC_TICKET_ID
        }, headers=self.headers, catch_response=True) as response:
            
            # For the stampede, explicitly mark 409 as a failure so it looks cool on LinkedIn!
            if response.status_code == 409:
                response.failure("OCC Lock Blocked This Request!")
            elif response.status_code == 200:
                ticket_id = response.json().get("ticket_id")
                # Simulate filling out the form before confirming
                self.client.post("/api/v1/checkout/confirm", json={
                    "ticket_id": ticket_id,
                    "attendee_name": "Load Test Bot",
                    "attendee_age": 30
                }, headers=self.headers)
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
