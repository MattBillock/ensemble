

## Error Recovery
## Error Handling Guidelines

- **BadRequestError**: Log error details, attempt recovery, escalate if unrecoverable
- **NotFoundError**: Log error details, attempt recovery, escalate if unrecoverable
- **CircuitBreakerOpenError**: Log error details, attempt recovery, escalate if unrecoverable
- **RateLimitError**: Log error details, attempt recovery, escalate if unrecoverable
- **General**: Always log errors with context, never silently fail

## Model Preference
sonnet

(Rest of the file remains unchanged)