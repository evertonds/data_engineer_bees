# Monitoring & Alerting Strategy

## Overview

This document outlines the comprehensive monitoring and alerting strategy for the BEES Breweries Data Pipeline. The strategy follows observability best practices and addresses data quality issues, pipeline failures, infrastructure problems, and business metrics.

## Table of Contents

1. [Observability Pillars](#observability-pillars)
2. [Alerting Channels & Severity Levels](#alerting-channels--severity-levels)
3. [Key Metrics & SLAs](#key-metrics--slas)
4. [Dashboard Design](#dashboard-design)
5. [Data Quality Monitoring](#data-quality-monitoring)
6. [Pipeline Health Monitoring](#pipeline-health-monitoring)
7. [Infrastructure Monitoring](#infrastructure-monitoring)
8. [Incident Response & Runbooks](#incident-response--runbooks)
9. [Implementation Guide](#implementation-guide)
10. [Cost Optimization](#cost-optimization)

---

## Observability Pillars

### 1. Metrics
**What:** Quantitative measurements of system behavior over time.

**Implementation:**
- **Airflow Metrics:** Task duration, success/failure rates, queue times
- **Data Quality Metrics:** Validation pass rates, null percentages, schema violations
- **Business Metrics:** Record counts, freshness, completeness
- **Infrastructure Metrics:** CPU, memory, disk I/O, network

**Tools:**
- Prometheus (metrics collection)
- StatsD (custom metrics)
- Airflow StatsD integration

### 2. Logs
**What:** Timestamped records of discrete events.

**Implementation:**
- **Structured Logging:** JSON format with consistent fields
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Correlation IDs:** Track requests across pipeline stages
- **Sensitive Data:** Masking PII and credentials

**Tools:**
- CloudWatch Logs (AWS)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Fluentd/Fluent Bit (log aggregation)

### 3. Traces
**What:** End-to-end journey of requests through the system.

**Implementation:**
- **DAG Execution Traces:** Bronze → Silver → Gold flow
- **API Request Traces:** Open Brewery DB API calls
- **Database Query Traces:** PostgreSQL operations

**Tools:**
- Jaeger or AWS X-Ray
- OpenTelemetry for instrumentation

---

## Alerting Channels & Severity Levels

### Alerting Channels

| Channel | Use Case | Response Time |
|---------|----------|---------------|
| **PagerDuty** | Critical alerts requiring immediate action | < 5 minutes |
| **Slack** | Non-critical alerts, warnings, daily summaries | < 30 minutes |
| **Email** | Digest reports, weekly summaries | < 24 hours |
| **Datadog/Grafana** | Real-time dashboard, on-call monitoring | Real-time |

### Severity Levels

#### P0 - Critical (PagerDuty + Slack)
- Pipeline completely down
- Data corruption detected
- Zero records processed for > 2 hours
- Database connection failures
- **Action:** Wake up on-call engineer, immediate investigation

#### P1 - High (Slack + Email)
- Single layer failure (Bronze/Silver/Gold)
- Data quality below critical threshold (< 70%)
- API rate limit exceeded
- Disk space > 85%
- **Action:** Fix within 4 hours, during business hours

#### P2 - Medium (Slack)
- Data quality warning (70-85%)
- Task retries (< 3 attempts)
- Slow query performance (> 2x baseline)
- **Action:** Investigate within 24 hours

#### P3 - Low (Email digest)
- Schema drift detected
- Non-critical validation warnings
- Performance degradation (< 2x baseline)
- **Action:** Review in next sprint

---

## Key Metrics & SLAs

### Pipeline SLAs

| Metric | Target | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| **Pipeline Completion** | < 30 minutes | > 45 minutes | > 60 minutes |
| **Data Freshness** | < 24 hours | > 36 hours | > 48 hours |
| **Success Rate** | > 99% | < 99% | < 95% |
| **Data Quality Score** | > 95% | < 90% | < 70% |

### Data Quality Metrics

```python
# Example metrics to track
data_quality_metrics = {
    "completeness": {
        "null_percentage": "< 5%",
        "empty_string_percentage": "< 2%",
        "missing_mandatory_fields": "0"
    },
    "accuracy": {
        "schema_conformance": "> 99%",
        "data_type_violations": "< 0.1%",
        "coordinate_validity": "> 90%"
    },
    "consistency": {
        "duplicate_records": "< 0.5%",
        "referential_integrity": "> 99%"
    },
    "timeliness": {
        "ingestion_lag": "< 1 hour",
        "processing_lag": "< 30 minutes"
    }
}
```

### Business Metrics

- **Record Volume:** Expected range per run (8,000 - 10,000 breweries)
- **Coverage:** Countries represented (> 10 countries)
- **Growth Rate:** Month-over-month change (-5% to +20%)
- **Brewery Types:** Distribution across 14 types

---

## Dashboard Design

### 1. Executive Dashboard (Grafana/Datadog)

**Purpose:** High-level overview for stakeholders.

**Panels:**
- Pipeline health status (last 7 days)
- Data quality trend (last 30 days)
- Record volume over time
- Success rate gauge
- Cost per run (AWS)

### 2. Engineering Dashboard

**Purpose:** Detailed metrics for data engineers.

**Panels:**
- Task duration breakdown (Bronze/Silver/Gold)
- Error rate by layer
- Retry attempts histogram
- Great Expectations validation results
- Database query performance
- API response times

### 3. Data Quality Dashboard

**Purpose:** Monitor data quality across layers.

**Panels:**
- Validation suite results (Bronze/Silver/Gold)
- Null percentage by column
- Schema drift alerts
- Data profiling statistics
- Anomaly detection (record count, distributions)

### 4. Infrastructure Dashboard

**Purpose:** Monitor resource utilization.

**Panels:**
- CPU/Memory usage (Airflow, Postgres)
- Disk I/O and space
- Network throughput
- Container health (Docker)
- Database connection pool

---

## Data Quality Monitoring

### Great Expectations Integration

**Current Implementation:**
- 3 validation suites (Bronze/Silver/Gold)
- 16 total expectations
- Checkpoint execution per layer

**Enhanced Monitoring:**

```python
# Pseudo-code for enhanced GE monitoring
def monitor_data_quality(validation_result):
    metrics = {
        "suite_name": validation_result.suite_name,
        "success": validation_result.success,
        "success_percent": validation_result.success_percent,
        "evaluated_expectations": validation_result.statistics["evaluated_expectations"],
        "successful_expectations": validation_result.statistics["successful_expectations"],
        "failed_expectations": validation_result.statistics["failed_expectations"]
    }

    # Send to monitoring backend
    send_metric("ge.validation.success_rate", metrics["success_percent"])

    # Alert on failure
    if not validation_result.success:
        alert(
            severity="P1" if metrics["success_percent"] < 70 else "P2",
            message=f"Data quality check failed: {metrics['suite_name']}",
            details=metrics
        )

    # Track trends
    store_trend("data_quality_history", metrics)
```

### Anomaly Detection

**Statistical Methods:**
- Z-score for outlier detection (record counts)
- Moving average for trend analysis
- Seasonal decomposition for patterns

**Example Anomalies to Detect:**
- Sudden drop in record count (> 20%)
- Spike in null values (> 2x baseline)
- New brewery types not seen before
- Geographic distribution shifts

---

## Pipeline Health Monitoring

### Airflow Monitoring

**Native Airflow Metrics:**
```python
# Metrics exported to StatsD/Prometheus
airflow_metrics = {
    "dag_run.duration": "Histogram",
    "dag_run.schedule_delay": "Gauge",
    "task_instance.duration": "Histogram",
    "task_instance.failures": "Counter",
    "task_instance.successes": "Counter",
    "executor.open_slots": "Gauge",
    "executor.queued_tasks": "Gauge"
}
```

**Custom DAG Monitoring:**

```python
# Add to brewery_pipeline.py
def monitor_dag_execution():
    """Send custom metrics to monitoring backend."""
    from datetime import datetime
    import statsd

    statsd_client = statsd.StatsClient('localhost', 8125)

    # Track execution
    start_time = datetime.now()
    statsd_client.incr('brewery_pipeline.runs')

    try:
        # Pipeline logic...
        pass
    except Exception as e:
        statsd_client.incr('brewery_pipeline.errors')
        raise
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        statsd_client.timing('brewery_pipeline.duration', duration)
```

### Task-Level Monitoring

**Metrics per Task:**
- Extract: API response time, records fetched, rate limit status
- Bronze: Write duration, file size, storage usage
- Silver: Transformation duration, PySpark memory, partitions created
- Gold: dbt run time, aggregation accuracy, table size

**Alerting Rules:**
```yaml
# Example alerting rules (Prometheus format)
groups:
  - name: brewery_pipeline
    rules:
      - alert: PipelineFailure
        expr: airflow_dag_run_status{dag_id="brewery_pipeline",state="failed"} > 0
        for: 5m
        annotations:
          summary: "Brewery pipeline failed"
          severity: "P0"

      - alert: SlowPipeline
        expr: airflow_dag_run_duration_seconds{dag_id="brewery_pipeline"} > 3600
        for: 10m
        annotations:
          summary: "Pipeline running slower than expected"
          severity: "P2"

      - alert: DataQualityDegraded
        expr: ge_validation_success_rate < 0.85
        for: 15m
        annotations:
          summary: "Data quality below threshold"
          severity: "P1"
```

---

## Infrastructure Monitoring

### Docker Container Monitoring

**Metrics to Track:**
```bash
# Container health checks
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Example metrics
- CPU usage per container (< 80% sustained)
- Memory usage (< 90% of limit)
- Network I/O
- Container restarts (< 3 per day)
```

**Alerting:**
- Container down for > 2 minutes → P0
- High memory usage (> 90%) → P1
- Frequent restarts (> 3/hour) → P1

### PostgreSQL Monitoring

**Key Metrics:**
```sql
-- Connection pool utilization
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';

-- Slow queries (> 5 seconds)
SELECT query, query_start, now() - query_start as duration
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds';

-- Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname IN ('breweries_bronze', 'breweries_silver', 'breweries_gold')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Database locks
SELECT pid, locktype, relation::regclass, mode, granted
FROM pg_locks
WHERE NOT granted;
```

**Alerts:**
- Active connections > 80% of max → P1
- Query duration > 30 seconds → P2
- Disk space > 85% → P0
- Deadlocks detected → P1

### AWS Infrastructure (MWAA Production)

**CloudWatch Metrics:**
- MWAA environment health
- Worker CPU/Memory utilization
- Scheduler latency
- Database connection pool
- S3 request rates and errors
- RDS performance insights

---

## Incident Response & Runbooks

### Runbook Template

```markdown
# Incident: [Short Description]

## Symptoms
- What users/systems are seeing
- Error messages
- Affected components

## Triage
1. Check [Dashboard Name] for [specific metric]
2. Review logs in [location]
3. Verify [upstream/downstream] dependencies

## Resolution Steps
1. [Step 1 with exact commands]
2. [Step 2 with exact commands]
3. [Step 3 with exact commands]

## Prevention
- Changes needed to prevent recurrence
- Monitoring improvements
- Code/config updates

## Post-Mortem
- Root cause analysis
- Timeline of events
- Action items
```

### Common Incidents

#### 1. Pipeline Failure - API Unavailable

**Symptoms:**
- Extract task fails with connection timeout
- "Unable to reach Open Brewery DB API" error

**Triage:**
```bash
# Check API health
curl -I https://api.openbrewerydb.org/v1/breweries

# Check Airflow logs
docker exec -it airflow-webserver airflow tasks logs brewery_pipeline extract_breweries 2024-01-26
```

**Resolution:**
1. Verify API is up (check status page)
2. If API is down, wait and retry
3. If persistent, check network/firewall rules
4. Manually trigger DAG after API recovers

**Prevention:**
- Implement exponential backoff (already in place)
- Add API health check before extraction
- Set up external monitoring for API availability

#### 2. Data Quality Failure - High Null Rate

**Symptoms:**
- Great Expectations validation fails
- "Silver validation" task fails
- Alert: "Data quality below threshold"

**Triage:**
```bash
# Check validation results
docker exec -it airflow-webserver cat /opt/airflow/data/ge_results/silver_validation_*.json

# Query database for null analysis
docker exec -it postgres psql -U airflow -d breweries -c "
SELECT
    count(*) as total,
    count(*) - count(city) as null_cities,
    count(*) - count(country) as null_countries
FROM breweries_silver.tb_breweries
WHERE ingestion_date = CURRENT_DATE;
"
```

**Resolution:**
1. Identify which fields have unexpected nulls
2. Check Bronze layer for data availability
3. Review API response for changes
4. Adjust Silver processor if API schema changed
5. Update Great Expectations suite if change is expected

**Prevention:**
- Monitor API schema changes
- Add schema validation in Bronze layer
- Alert on schema drift before processing

#### 3. Pipeline Slow - Performance Degradation

**Symptoms:**
- Pipeline takes > 60 minutes (normally 30 minutes)
- Alert: "Pipeline running slower than expected"

**Triage:**
```bash
# Check task durations in Airflow UI
# Look at Gantt chart for bottlenecks

# Check Spark job performance
docker logs airflow-webserver | grep "PySpark"

# Check database performance
docker exec -it postgres psql -U airflow -d breweries -c "
SELECT query, calls, mean_exec_time, max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"
```

**Resolution:**
1. Identify slow task (Bronze/Silver/Gold)
2. For Silver: Check Spark memory configuration
3. For Gold: Review dbt query optimization
4. Check database indexes
5. Consider partitioning strategy

**Prevention:**
- Baseline performance metrics
- Set up performance regression tests
- Optimize Spark configurations
- Add database indexes for common queries

#### 4. Storage Full - Disk Space Exhausted

**Symptoms:**
- Tasks fail with "No space left on device"
- Alert: "Disk space > 95%"

**Triage:**
```bash
# Check disk usage
docker exec airflow-webserver df -h

# Find large files
docker exec airflow-webserver du -sh /opt/airflow/data/* | sort -hr | head -20

# Check log sizes
docker exec airflow-webserver du -sh /opt/airflow/logs
```

**Resolution:**
1. Clean old data files (Bronze layer retention)
2. Rotate/compress logs
3. Clean Great Expectations data docs
4. Remove old DAG run artifacts

**Prevention:**
- Implement data retention policy (30 days Bronze)
- Set up log rotation
- Monitor disk usage proactively
- Automate cleanup jobs

---

## Implementation Guide

### Phase 1: Basic Monitoring (Week 1)

**Goals:** Get visibility into pipeline execution.

**Tasks:**
1. Enable Airflow StatsD metrics
2. Set up Prometheus + Grafana
3. Create basic dashboard (pipeline success/failure)
4. Configure Slack webhook for critical alerts

**Config Changes:**
```python
# airflow.cfg
[metrics]
statsd_on = True
statsd_host = localhost
statsd_port = 8125
statsd_prefix = airflow
```

### Phase 2: Data Quality Monitoring (Week 2)

**Goals:** Track data quality trends.

**Tasks:**
1. Export Great Expectations results to metrics backend
2. Create data quality dashboard
3. Set up alerting rules for validation failures
4. Implement anomaly detection for record counts

### Phase 3: Advanced Observability (Week 3-4)

**Goals:** Full observability stack.

**Tasks:**
1. Implement distributed tracing (OpenTelemetry)
2. Set up log aggregation (ELK or CloudWatch)
3. Create comprehensive runbooks
4. Conduct incident response drill

### Phase 4: Production Hardening (Week 5-6)

**Goals:** Production-ready monitoring.

**Tasks:**
1. Set up PagerDuty integration
2. Configure on-call rotation
3. Create SLO dashboards
4. Implement cost monitoring

---

## Cost Optimization

### Monitoring Cost Considerations

**Metrics Storage:**
- Prometheus: Local storage (free, limited retention)
- CloudWatch: $0.30 per custom metric/month
- Datadog: $15-23 per host/month

**Recommendations:**
- Use Prometheus for development/local
- Use CloudWatch for AWS production (native integration)
- Sample high-cardinality metrics (reduce cost)
- Set appropriate retention periods (30-90 days)

**Log Storage:**
- CloudWatch Logs: $0.50/GB ingested, $0.03/GB stored
- S3: $0.023/GB stored (archive logs here)

**Recommendations:**
- Use structured logging (easier to query, less storage)
- Set log retention policies (7 days hot, 90 days cold)
- Archive to S3 for long-term retention
- Use log sampling for high-volume non-critical logs

### Sample Monitoring Budget (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| CloudWatch Metrics | 50 custom metrics | $15 |
| CloudWatch Logs | 10 GB ingested | $5 |
| Datadog (optional) | 2 hosts | $46 |
| PagerDuty | 1 user | $21 |
| **Total (Basic)** | - | **$41/month** |
| **Total (Full Stack)** | - | **$87/month** |

---

## Appendix

### Useful Commands

```bash
# Airflow task logs
docker exec -it airflow-webserver airflow tasks logs <dag_id> <task_id> <execution_date>

# Trigger DAG manually
docker exec -it airflow-webserver airflow dags trigger brewery_pipeline

# Check DAG status
docker exec -it airflow-webserver airflow dags list-runs -d brewery_pipeline

# Database queries
docker exec -it postgres psql -U airflow -d breweries

# Container metrics
docker stats

# Great Expectations validation
docker exec -it airflow-webserver great_expectations checkpoint run bronze_checkpoint
```

### References

- [Airflow Metrics Documentation](https://airflow.apache.org/docs/apache-airflow/stable/logging-monitoring/metrics.html)
- [Great Expectations Monitoring](https://docs.greatexpectations.io/docs/guides/validation/checkpoints/how_to_configure_validation_result_actions)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Google SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)

---

**Last Updated:** 2024-01-26
**Owner:** Data Engineering Team
**Review Cycle:** Quarterly
