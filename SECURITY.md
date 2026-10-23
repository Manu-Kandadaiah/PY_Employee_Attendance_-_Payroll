# Security Policy

Do not open public issues containing credentials, employee personal information, payroll data or exploitable security details.

For a real deployment:

- Rotate the demo credentials and all secrets immediately.
- Store secrets outside source control.
- Apply least-privilege database grants.
- Encrypt transport with HTTPS and restrict database network access.
- Consider application-layer encryption or tokenization for bank and statutory identifiers.
- Review role assignments and audit logs regularly.
- Keep dependencies patched and run automated vulnerability scanning.
- Define retention, backup, privacy and incident-response procedures.

This educational project provides foundational controls but must undergo organization-specific threat modelling, penetration testing and compliance review before processing real employee or payroll data.
