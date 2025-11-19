# Operations Runbook

## Monitoring Checklist
- Cloud Logging: watch `todo_tool` and `agent` logs for elevated error rates.
- Cloud Monitoring: dashboard for latency, success rate, and rate-limit denials.
- Alerts: trigger on sustained 5xx errors from Todo API or retry exhaustion.

## Failure Scenarios
- **Todo API down**: retries will back off; escalate if outage exceeds 5 minutes. Fallback to user-friendly apology.
- **Rate limit exceeded**: token bucket blocks excess calls; advise user to slow down.
- **Prompt injection attempts**: sanitizer blocks dangerous directives; log and prompt user to rephrase.

## Mitigations
- Tune backoff parameters in `TodoServiceTool` to balance latency and protection.
- Enable circuit breakers or cached reads for `list_todos` during outages.
- Keep dependencies pinned and rotate credentials via Secret Manager.
