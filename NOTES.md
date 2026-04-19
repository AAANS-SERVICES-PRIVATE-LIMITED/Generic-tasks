# FastAPI Email API - Concepts Guide

## Project Structure

```
email_api/
├── main.py              # App entry point
├── routers/             # API endpoint handlers
├── models/              # Data models (Pydantic + SQLAlchemy)
├── services/            # Business logic
├── database.py          # Database connection management
├── init_db.py           # Table initialization
├── requirements.txt     # Dependencies
└── .env                 # Configuration
```

---

## 1. FastAPI Core Concepts

### What is FastAPI?
FastAPI is a modern Python web framework for building APIs. It provides:
- Automatic API documentation (Swagger UI at `/docs`)
- Data validation with Pydantic
- Async/await support for high performance
- Type hints for better IDE support

### Routers
Routers group related endpoints together. Each router has:
- **Prefix**: URL path segment (e.g., `/send`, `/templates`)
- **Tags**: Groups endpoints in documentation
- **Endpoints**: Specific URL + HTTP method combinations

Why use routers? Organization and maintainability - separate concerns into logical groups.

### Dependency Injection
FastAPI uses `Depends()` to inject dependencies like database sessions. This:
- Eliminates manual session management
- Ensures cleanup (sessions always closed)
- Makes code testable and reusable

---

## 2. Database Integration

### Why PostgreSQL?
PostgreSQL is a robust relational database that provides:
- Persistent storage (survives server restarts)
- ACID compliance (reliable transactions)
- Complex queries and relationships
- Production-ready scalability

### SQLAlchemy ORM
SQLAlchemy is an Object-Relational Mapper that:
- Maps Python classes to database tables
- Generates SQL queries automatically
- Provides a Pythonic database interface
- Supports multiple database backends

### Pydantic vs SQLAlchemy Models

| Purpose | Model Type | Used For |
|---------|------------|---------|
| API validation | Pydantic (schemas.py) | Request/response validation |
| Database mapping | SQLAlchemy (db_models.py) | Table structure and queries |

Why two types? They serve different purposes - Pydantic ensures valid API data, SQLAlchemy manages database persistence.

### Database Connection Management
The `database.py` file manages connections via:
- **Engine**: Connection pool to PostgreSQL
- **SessionLocal**: Factory for creating sessions
- **get_db()**: Dependency injection helper

This pattern ensures sessions are properly opened and closed automatically.

---

## 3. Pydantic Models

### What are Pydantic Models?
Pydantic models define the shape of data for API requests and responses. They:
- Validate incoming data automatically
- Convert types (e.g., string to int)
- Provide documentation examples
- Enable IDE autocomplete

### Current Models
- **Recipient**: Email recipient with optional name/company
- **SendRequest**: Email sending request with recipients list
- **ManualSendRequest**: Single email send with template selection (form data)
- **TemplateCreate**: Template creation with validation

### Field Options
- **Required fields**: No default value
- **Optional fields**: `Optional[str] = None`
- **Examples**: `Field(..., example="value")` for docs

---

## 4. Services Layer

### What is the Services Layer?
The services layer contains business logic separate from HTTP handling. It:
- Handles core operations (email sending)
- No HTTP/FastAPI dependencies
- Reusable across different contexts
- Easier to test in isolation

### EmailService
The EmailService handles:
- SMTP connection management
- HTML to text conversion
- Error handling and logging
- Async email sending

Why separate? Business logic shouldn't know about HTTP - it's a separation of concerns.

---

## 5. API Endpoints

### Send Endpoints

#### Manual Entry (POST /api/send)
Sends email to single recipient with form data input.
- **Fields**: email, name (optional), company (optional), subject, html_body (optional), template_name (optional)
- **Template options**: Provide html_body directly OR select saved template by name
- **Why form data?** Handles HTML content without JSON parsing issues

#### CSV Upload (POST /api/send/csv)
Sends emails to multiple recipients from CSV file.
- **CSV format**: email,name,company (email required, others optional)
- **Template options**: Provide html_body directly OR select saved template by name
- **Skips header row** automatically
- **Validates emails** before sending

#### XLSX Upload (POST /api/send/xlsx)
Sends emails to multiple recipients from Excel file.
- **Excel format**: email,name,company (email required, others optional)
- **Template options**: Provide html_body directly OR select saved template by name
- **Parses with pandas** for robust Excel handling
- **Validates emails** before sending

**Why file uploads?** Bulk sending without manual entry, handles large recipient lists efficiently.

### Template Endpoints

#### List Templates (GET /api/templates)
Retrieves all saved templates from database.

#### Create Template - Paste (POST /api/templates)
Creates template by pasting HTML directly in form field.
- **Uses form data** to handle HTML content without JSON issues
- **Fields**: name, html_body

#### Create Template - Upload (POST /api/templates/upload)
Creates template by uploading HTML file.
- **File upload** for large HTML files
- **No JSON parsing issues**
- **Fields**: file, name

#### Update Template (PUT /api/templates/{id})
Updates existing template fields.

#### Delete Template (DELETE /api/templates/{id})
Removes template from database.

**Why two create options?** Flexibility - paste for small templates, upload for large files. Both avoid JSON parsing issues with HTML.

### Database Logging
All send endpoints log each email attempt to the EmailLog table:
- **Fields**: to_email, name, company, subject, html_body, status, error_message, sent_at
- **Status tracking**: sent or failed
- **Error logging**: Captures SMTP errors for debugging
- **History**: Complete audit trail of all email sends

### Database Operations in Endpoints
Each endpoint uses:
1. `db: Session = Depends(get_db)` - Get session
2. `db.query(Model)` - Query database
3. `db.add()` - Add new record
4. `db.commit()` - Save changes
5. `db.refresh()` - Reload from database

---

## 6. Architecture Summary

### Data Flow
1. **Request** → FastAPI validates with Pydantic
2. **Router** → Gets database session via dependency injection
3. **Service** → Executes business logic
4. **Database** → Persists data via SQLAlchemy
5. **Response** → Returns JSON to client

### Layer Responsibilities

| Layer | Responsibility |
|-------|---------------|
| Models | Data shapes and validation |
| Routers | HTTP request/response handling |
| Services | Business logic |
| Database | Data persistence |

### Key Design Principles
- **Separation of concerns**: Each layer has a single responsibility
- **Dependency injection**: Automatic resource management
- **Type safety**: Pydantic and type hints catch errors early
- **Persistence**: Database for reliable data storage
