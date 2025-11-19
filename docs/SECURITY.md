# Security Guidance

- Use dedicated service accounts with least privilege; grant access only to required Todo API and Vertex AI resources.
- Enforce VPC Service Controls around Vertex endpoints and the Todo service.
- Configure CMEK for storage and logging backends; avoid storing sensitive data in prompts.
- Enable Gemini content filters and safety settings to block abuse.
- Store secrets in Secret Manager and load into the environment at runtime; never commit credentials.
- Validate and sanitize all user-provided strings before calling tools to mitigate prompt injection.
