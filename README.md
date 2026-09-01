# RosterReady Backend

## Final Year Project

This is the backend for my **Final Year Project**. The application will handle CRUD functionality and provide additional features such as a **CSP solver**. It is built using **FastAPI** for the backend framework and **MySQL** to store the data. 

### Project Overview

**RosterReady** is an application that generates schedules for teams or organizations based on various factors like availability, shifts, and other constraints. The goal is to automate and streamline the scheduling process to meet specific needs of users and teams.

### About This Repository

- The backend is a work in progress.
- It is my first time using **FastAPI** and my first time working with **Python** in the backend.
- Expect frequent commits where files might be completely changed or even deleted as the project evolves.

### Development Process

Let's see how it goes with using YouTube tutorials and the FastAPI docs without getting any errors..

### Features (Planned):

- **CRUD Functionality**: Basic Create, Read, Update, Delete functionality for users, teams, and schedules.
- **CSP Solver**: Implementing a Constraint Satisfaction Problem (CSP) solver to create optimal schedules based on user-defined constraints

### Technologies Used

- **FastAPI**: A modern, fast web framework for building APIs with Python 3.7+.
- **MySQL**: A relational database used to store application data.
- **SQLAlchemy**: An ORM (Object Relational Mapper) for interacting with the MySQL database.
- **Python**: The primary programming language used for the backend development.

### Future Improvements

- **Authentication & Authorization**
- **Middleware**
- **JWT**
- **Unit Testing**
- **Hosting**

## Normalized PostgreSQL schema

The replacement scheduling schema lives in `app/domain`. It supports team
memberships, per-member working limits, dated shift instances, time-off
requests, skills, solver metadata, roster assignments, and an assignment audit
trail without duplicating team or weekday data on assignments.

Alembic is the schema source of truth. Configure `DATABASE_URL` using
`.env.example`, then create or upgrade the schema with:

```bash
alembic upgrade head
```

The existing MySQL-backed routes remain available temporarily while their APIs
are migrated to the new domain. `MYSQL_URL` is therefore accepted as a legacy
fallback during this transition.

### Local PostgreSQL

The development database runs locally and does not use a hosted service:

```bash
docker compose up -d postgres
DATABASE_URL=postgresql+psycopg://rosterready:rosterready-local@localhost:5432/rosterready alembic upgrade head
```

Its data is stored in the `rosterready-postgres-data` Docker volume. Stop the
container with `docker compose stop postgres` without deleting the data.
