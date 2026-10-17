# Payment API Troubleshooting Runbook

## Service

payment-api

## Purpose

The Payment API handles payment creation, payment lookup,
transaction validation, and payment status operations.

## High Latency Investigation

When Payment API latency increases:

1. Check API P95 and P99 latency.
2. Check error rate.
3. Check CPU and memory utilization.
4. Check database latency.
5. Search application logs for slow database queries.
6. Check recent deployments.
7. Compare the timing of the deployment with the beginning
   of the latency increase.

## Database Latency

If database latency increases while CPU and memory remain
normal, investigate database queries before investigating
application resource exhaustion.

Pay particular attention to:

- Slow queries
- Missing indexes
- Changed query execution plans
- Increased result sets
- Connection pool exhaustion

## Recent Deployment

If latency begins shortly after a deployment:

1. Identify queries changed by the deployment.
2. Compare query execution plans with the previous version.
3. Check whether indexes are being used.
4. Consider rolling back the deployment if customer
   impact is significant.

## Recommended Evidence

A strong root-cause hypothesis should correlate:

- API latency
- Database latency
- Application logs
- Deployment timing
- Query changes