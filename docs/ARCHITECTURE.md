# Architecture and Extension Guide

## Request lifecycle

1. Blueprint controller receives a request.
2. Flask-Login authenticates the session.
3. `roles_required` enforces module access.
4. WTForms validates web input.
5. Service classes/functions execute attendance or payroll rules.
6. SQLAlchemy persists the transaction.
7. Audit and notification records are created in the same transaction.
8. Jinja renders HTML or the API returns JSON.

## Recommended extensions

- **Biometric device:** write an adapter that creates or updates `Attendance` using source `biometric`.
- **Mobile application:** add token authentication while retaining the service layer.
- **Email/SMS:** replace in-app-only notification calls with queued delivery through Celery/RQ.
- **Tax engine:** introduce fiscal-year tax declarations, slabs and statutory components.
- **Multi-company:** add `organization_id` to tenant-owned tables and enforce tenant scopes.
- **Approvals:** generalize manager/HR approval into configurable workflow steps.
- **Documents:** add encrypted object storage for employee and leave documents.
