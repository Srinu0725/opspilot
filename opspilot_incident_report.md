# Production Incident Report

## Incident Summary
- Affected service: payment-api
- Incident type: High API latency and intermittent server errors
- Suspected start: After a recent deployment
- Status: Under investigation

## Symptoms
- API P95 and P99 response latency increased.
- Database queries became slower.
- Intermittent HTTP 500 errors occurred.
- The issue may be associated with a recent deployment.

## Investigation Checklist
1. Check API P95 and P99 latency.
2. Check error rates and application logs.
3. Check CPU and memory utilization.
4. Check database latency and connection-pool metrics.
5. Search logs for slow payment_lookup queries.
6. Review recent deployment records.
7. Compare current and previous query execution plans.

## Important Note
These are user-reported observations and have not been independently verified.
