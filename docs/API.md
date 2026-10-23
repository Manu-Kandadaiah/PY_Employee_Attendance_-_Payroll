# REST API Notes

The API is session authenticated through Flask-Login. Browser clients must first authenticate at `/auth/login`.

## CSRF

POST requests require an `X-CSRFToken` header. A logged-in page exposes the token in:

```html
<meta name="csrf-token" content="...">
```

Example:

```javascript
fetch('/api/v1/attendance/check-in', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
  },
  body: JSON.stringify({})
});
```

## Response pattern

Successful list responses use `{ "data": [...] }`. Validation/conflict responses use `{ "error": "..." }` with an appropriate HTTP status.

## Authorization

- Employee attendance is restricted to the current employee profile.
- Employee payroll details are restricted to the owner, HR or Admin.
- Employee directory API is restricted to HR or Admin.
