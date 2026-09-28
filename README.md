# Ticketbook: High-Concurrency Distributed Reservation Engine

![Tech Stack](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue) ![Redis](https://img.shields.io/badge/Redis-alpine-red) ![React](https://img.shields.io/badge/React-18-blue) ![Docker](https://img.shields.io/badge/Docker-Ready-blue)

A distributed, multi-tenant ticketing and reservation backend engineered from scratch to solve the "Taylor Swift Ticket Stampede" problem using a two-speed database concurrency model.

---

## ⚡ The Problem & The Architecture
When building a system that handles live inventory, the architecture must inherently protect itself from race conditions and leaky boundaries. A one-size-fits-all database locking strategy destroys throughput.

To solve this, I implemented a **Two-Speed Data Access Layer**:

1. **The Stampede Scenario (Optimistic Concurrency Control):** 
   For Reserved Seating (VIP), where exact state matters, I implemented OCC using `version_id`. If 5,000 users try to buy the exact same seat simultaneously, the database mathematically guarantees exactly 1 request succeeds while instantly rejecting the others without deadlocking.

2. **Maximum Throughput (PostgreSQL SKIP LOCKED):** 
   For General Admission, users just want the *next available* ticket. I implemented atomic `FOR UPDATE SKIP LOCKED` queries. This bypasses lock contention entirely, allowing the database to chew through thousands of concurrent requests and rapidly assign tickets without creating massive locking queues.

---

## 📈 Load Testing & Proven Metrics

I aggressively load-tested the architecture locally using **Locust**, simulating 500 virtual users heavily spamming the endpoints.

**The Results (Locust on a single local machine):**
- Sustained **270+ Requests Per Second (RPS)**.
- **17ms Median Latency** on Optimistic Concurrency Rejections.
- **18ms Median Latency** on SKIP LOCKED Ticket Assignments.
- **Zero Database Crashes** under maximum thread-pool starvation (solved via strict `DB_POOL_SIZE` tuning and multi-worker ASGI setup).

*(Upload your Locust Screenshots here)*

---

## 🚀 How to Run Locally (One-Click Setup)

This project is fully Dockerized. You do not need to install Python, Node, PostgreSQL, or Redis on your machine.

**1. Clone the Repository:**
```bash
git clone https://github.com/YourUsername/Ticketbook.git
cd Ticketbook
```

**2. Start the entire Stack:**
```bash
docker compose up --build -d
```

**3. Access the Application:**
- **Frontend (React):** [http://localhost:3000](http://localhost:3000)
- **Backend API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🚦 How to run the Load Tests
If you want to verify the concurrency logic yourself:

1. Exec into the backend container or use your local python environment.
2. Run the preparation script to seed 5,000 tickets and 100 users:
   ```bash
   python scripts/prepare_load_test.py
   ```
3. Run Locust:
   ```bash
   locust -f load_tests/locustfile.py
   ```
4. Open the Locust UI at `http://localhost:8089` and start Swarming!
