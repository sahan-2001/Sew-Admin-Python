# Sew-Admin Apparel ERP (Python FastAPI Version)

This is a **secure, module-wise Python backend** for the Sew-Admin Apparel ERP system. It has been reimagined from its typical Laravel roots to a modern Python stack using **FastAPI**. 

## Technology Stack

* **Core Framework:** FastAPI (High performance, modern Python backend)
* **Database ORM:** SQLAlchemy (Supports MySQL, Postgres, SQLite)
* **Data Validation:** Pydantic (Strict typing)
* **Security:** 
  * OAuth2 Password Bearer with JWT tokens.
  * `passlib` with `bcrypt` for secure password hashing.
  * `python-jose` for secure token signing/validation.

## Module-Wise Folder Structure

The project has been refactored into independent modules following Domain-Driven Design principles:

```text
.
├── core/
│   ├── database.py       # Database configs and ORM initialization
│   └── security.py       # JWT creation and Password Cryptography
├── modules/
│   ├── users/            # Handles authentication, roles, and user data
│   │   └── router.py     # API Endpoints (e.g., /api/users/login)
│   ├── customers/        # Customer profiles and CRM
│   ├── orders/           # Order processing
│   ├── products/         # End product definition (BOM mapping)
│   ├── inventory/        # Material and stock management
│   ├── suppliers/        # Supplier profiles and tracking
│   ├── production/       # Manufacturing and work stages
│   ├── employees/        # Workforce tracking
│   └── reports/          # Data aggregation and analytics wrappers
├── main.py               # Application entrypoint that ties routers together
└── requirements.txt      # Python dependencies
```

## How to Run Locally

1. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Setup Database URL in `core/database.py`:**
   By default, it uses SQLite for easy local dev but can quickly be swapped to MySQL (`mysql+mysqlconnector://...`).
3. **Run the Development Server:**
   ```bash
   uvicorn main:app --reload
   ```
4. **Access the API Documentation:**
   Open your browser and navigate to `http://localhost:8000/docs`. FastAPI automatically generates an interactive Swagger UI for testing the ERP endpoints securely.
