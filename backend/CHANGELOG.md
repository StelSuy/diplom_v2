# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-01-24

### 🔧 Fixed

#### Critical Bugs
- **Fixed duplicate `get_db()` function** in `app/api/deps.py` and `app/db/session.py`
- **Fixed `terminal_id` type** in Event model (changed from String to Integer with ForeignKey)
- **Fixed schedule cell saving** in `upsert_cell()` - now properly validates and saves data
- **Fixed README.md encoding** - restored Cyrillic text from corrupted state

#### Schedule Issues
- **Improved schedule cell validation logic**:
  - Clear separation of cases: delete, explicit time, code parsing
  - Added time range validation (start must be before end)
  - Fixed return value when deleting cells (no longer returns unsaved object)
- **Added detailed error messages** for schedule operations
- **Fixed time format parsing** for both "H-H" and "HH:MM" formats

### ✨ Added

#### Dependencies
- `cryptography==41.0.7` - For NFC signature verification
- `reportlab==4.0.7` - For PDF generation
- `pymysql==1.1.0` - MySQL driver
- `alembic==1.13.1` - Database migrations
- `python-multipart==0.0.6` - For file uploads

#### Features
- **CORS Middleware** - Cross-origin requests support
- **Global exception handler** - Centralized error handling
- **Structured logging** - Better debugging and monitoring
- **Request logging middleware** - Debug mode request tracking
- **Health check improvements** - Database status verification

#### Database
- **Alembic integration** for database migrations:
  - `alembic.ini` configuration
  - `alembic/env.py` with auto-import of all models
  - Initial migration script `001_initial_schema.py`
- **Improved database initialization** script with better error handling

#### Documentation
- **QUICKSTART.md** - 5-minute setup guide
- **API_DOCS.md** - Complete API reference with examples
- **FAQ.md** - Frequently asked questions and solutions
- **.env.example** - Environment variables template
- **Makefile** - Command automation for common tasks

#### Utilities
- **health_check.py** - System health diagnostics:
  - Database connection check
  - Tables existence verification
  - Indexes validation
  - Data integrity checks
- **Improved init_db.py** - Better logging and error messages

### 🎨 Improved

#### Code Quality
- **Better error handling** in all CRUD operations
- **Consistent logging** across all modules
- **Type hints** improvements
- **Validation** enhancements for all inputs

#### API
- **Better HTTP status codes** (400 for validation, 500 for server errors)
- **Detailed error messages** in API responses
- **Improved schedule endpoints** with comprehensive logging

#### Configuration
- **Centralized logging setup** in `app/core/logging.py`
- **Environment variable validation** in config
- **Better defaults** for all settings

### 📝 Changed

#### Breaking Changes
None - all changes are backward compatible

#### Internal Changes
- Removed duplicate code in session management
- Cleaned up imports and unused code
- Standardized error handling patterns

### 🔒 Security

- **Added .env.example** to prevent accidental secret commits
- **Improved token validation** in auth middleware
- **Better password hashing** configuration

---

## [1.0.0] - 2024-12-01

### Initial Release

- Basic employee management
- NFC event tracking
- Schedule management
- Work time statistics
- Terminal integration
- Admin authentication
- PDF report generation

---

## Future Plans

### [1.2.0] - Planned
- [ ] Unit tests with pytest
- [ ] Integration tests
- [ ] Docker and docker-compose
- [ ] Rate limiting middleware
- [ ] Prometheus metrics
- [ ] Background tasks with Celery
- [ ] WebSocket support for real-time updates
- [ ] Advanced reporting features

### [1.3.0] - Planned
- [ ] Multi-tenancy support
- [ ] Role-based access control (RBAC)
- [ ] Audit logging
- [ ] Data export/import
- [ ] Advanced schedule templates
- [ ] Notifications system

---

## Version Format

We use [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in backward compatible manner
- **PATCH** version for backward compatible bug fixes

---

## Types of Changes

- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security improvements
