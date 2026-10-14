# Lab 5: Multi-Container Application with Docker Compose

## Project Overview
This project is a multi-container web application built using Docker Compose as part of Laboratory Work No. 5. It orchestrates a Python Flask backend API, a PostgreSQL relational database, a Redis caching layer, and an optional Nginx reverse proxy.

---

## Project Architecture & Components
- **Backend API (`api/`):** Python Flask application handling HTTP requests, user creation, database transactions, and Redis caching.
- **Database (`db`):** PostgreSQL 15 container storing persistent user data.
- **Cache (`redis`):** Redis 7 container handling high-performance caching for user lookups.
- **Reverse Proxy (`nginx`):** Nginx web server routing incoming traffic to the backend API.
- **Network & Volumes:** Connected via a custom bridge network (`backend`) with named volumes (`postgres_data`, `redis_data`) to ensure persistent storage.

---

## Project Structure
```text
lab5-compose/
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
├── api/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── config.py
├── nginx/
│   └── nginx.conf
└── README.md
```
## Environment Configuration
1.Copy the example environment file:
```
cp .env.example .env
```
2.Verify or update your .env variables:
```
DB_USER=labuser
DB_PASSWORD=labpassword123
DB_NAME=labdb
API_PORT=5000
```
## How to Run the Application
1. Build and start all containers in detached mode:
```
docker compose up --build -d
```

2. Check container statuses:
```
docker compose ps
```

3. View logs:
```
docker compose logs -f
```

## Testing Endpoints
You can test the API endpoints using curl:
- Root Info:
```
curl http://localhost:5000/
```

- Health Check:
```
curl http://localhost:5000/health
```

- Database Connection Test:
```
curl http://localhost:5000/db-test
```

- Redis Cache Connection Test:
```
curl http://localhost:5000/cache-test
```

- Create a User (POST):
```
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

- Get All Users (GET):
```
curl http://localhost:5000/users
```

- Get User by ID (Cached / Database):
```
First request fetches from database and caches result
curl http://localhost:5000/users/1

Subsequent requests fetch directly from Redis cache
curl http://localhost:5000/users/1
```

## Troubleshooting & Management
- Stop and remove containers (preserving volumes):
```
docker compose down
```

- Full reset (clearing persistent database volumes):
```
docker compose down -v
```

- Rebuild images without cache:
```
docker compose build --no-cache
```
