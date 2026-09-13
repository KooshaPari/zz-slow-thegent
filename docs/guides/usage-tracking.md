# Current Usage Tracking Guide

## Quick Reference: How to Check Resource Utilization

### 1. Upstash Redis Usage

**Via MCP Tool** (atoms-mcp-prod):
```python
# Get Redis metrics
result = await monitoring_tool(operation="get_metrics")
redis_stats = result["data"]["embedding_cache"]  # or token_cache, rate_limiting
```

**What you get**:
- Embedding cache: hits, misses, hit_ratio, api_calls_saved
- Token cache: hits, misses, validations, hit_ratio
- Rate limiting: exceeded_count, status
- Redis status: connected, backend, latency

**Limitations**: No actual request count, storage, or cost data

**Direct Access**:
```python
from atoms_mcp.infrastructure.redis_monitoring import get_redis_metrics

metrics = await get_redis_metrics()
all_stats = await metrics.get_all_metrics()
```

### 2. Database Usage

**Via MCP Tool** (atoms-mcp-prod):
```python
# Get database performance
result = await monitoring_tool(operation="get_performance_profile")
db_stats = result["data"]
```

**What you get**:
- Total queries
- Query breakdown by operation/table
- Slow queries (>1000ms)
- Min/max/avg query times
- Slow query percentage

**Limitations**: No actual query count, storage, or cost data

**Direct Access**:
```python
from atoms_mcp.infrastructure.monitoring import get_performance_monitor

monitor = get_performance_monitor()
stats = monitor.get_stats()
```

### 3. Usage Analytics

**Via MCP Tool** (atoms-mcp-prod):
```python
# Get usage analytics
result = await monitoring_tool(operation="get_usage_analytics")
analytics = result["data"]
```

**What you get**:
- Most used tools (top 10)
- Popular operations (by count, avg time, unique users)
- Search analytics (total searches, avg results)

**Direct Access**:
```python
from atoms_mcp.infrastructure.monitoring import get_usage_analytics

analytics = get_usage_analytics()
report = analytics.get_analytics_report()
```

### 4. Health Check (All Services)

**Via MCP Tool** (atoms-mcp-prod):
```python
# Get comprehensive health
result = await health_check()
```

**What you get**:
- Database: status, latency_ms, responsive
- Authentication: status, service, domain
- Cache: status, size, max_size
- Performance: status, total_queries, slow_queries
- Errors: status, total_errors, unique_errors
- Rate limiter: status, tracked_users

### 5. Sandbox Execution Metrics (agentapi/atomsagent)

**Via REST API**:
```bash
GET /api/v1/monitoring/metrics/{execution_id}
```

**What you get**:
- Execution time (total, sandbox creation, dependency install, execution)
- Status (started, completed, failed)
- Tokens used
- Error messages

**Via MCP Tool**:
```python
metrics = await get_execution_metrics(execution_id)
```

## Current Metrics Available

### ✅ Tracked Metrics

| Metric | Location | Access Method |
|--------|----------|---------------|
| Redis cache hits/misses | `redis_monitoring.py` | `monitoring_tool("get_metrics")` |
| Database query performance | `monitoring.py` | `monitoring_tool("get_performance_profile")` |
| Tool usage counts | `monitoring.py` | `monitoring_tool("get_usage_analytics")` |
| Error tracking | `monitoring.py` | `monitoring_tool("get_error_tracking")` |
| Sandbox execution metrics | `agentapi/monitoring.py` | `/api/v1/monitoring/metrics/{id}` |
| Health status | `health.py` | `health_check()` tool |

### ❌ Missing Metrics

| Metric | Why Missing | Impact |
|--------|-------------|--------|
| Upstash request count | No Upstash API integration | Can't track actual usage |
| Upstash storage usage | No Upstash API integration | Can't track storage costs |
| Upstash costs | No Upstash API integration | Can't track spending |
| Supabase query count | No Supabase Management API | Can't track actual usage |
| Supabase storage | No database size queries | Can't track storage costs |
| Supabase costs | No cost tracking | Can't track spending |
| Vercel function invocations | No Vercel API integration | Can't track serverless costs |
| Per-user/org costs | No cost attribution | Can't implement usage-based billing |

## How to Get Actual Usage (Manual)

### Upstash

1. **Via Upstash Dashboard**:
   - Go to https://console.upstash.com
   - Select your Redis database
   - View "Usage" tab for:
     - Requests per day/hour
     - Storage used
     - Bandwidth
     - Cost breakdown

2. **Via Upstash API** (if API key configured):
   ```bash
   curl -H "Authorization: Bearer $UPSTASH_API_KEY" \
     https://api.upstash.io/v2/usage
   ```

### Supabase

1. **Via Supabase Dashboard**:
   - Go to your project dashboard
   - View "Database" → "Usage" for:
     - Database size
     - Bandwidth
     - Query count (if enabled)
     - Cost breakdown

2. **Via Database Queries**:
   ```sql
   -- Database size
   SELECT pg_size_pretty(pg_database_size('postgres'));
   
   -- Query stats (if pg_stat_statements enabled)
   SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
   ```

### Vercel

1. **Via Vercel Dashboard**:
   - Go to your project
   - View "Analytics" → "Usage" for:
     - Function invocations
     - Execution time
     - Bandwidth
     - Cost breakdown

## Recommendations

### Immediate: Add API Integrations

1. **Upstash Management API**:
   - Add `UPSTASH_API_KEY` environment variable
   - Query usage stats via API
   - Track in monitoring service

2. **Supabase Management API**:
   - Use Supabase Management API
   - Query database stats
   - Track storage and query counts

3. **Vercel API**:
   - Use Vercel API for function metrics
   - Track invocations and execution time

### Short-term: Enhanced Tracking

1. **Add usage tracking service** that aggregates all metrics
2. **Add cost calculation** based on usage
3. **Add per-user/org tracking** for cost attribution

### Long-term: Full Observability

1. **Real-time dashboards** in frontend
2. **Usage alerts** and budget limits
3. **Cost optimization recommendations**

## Example: Get All Available Metrics

```python
# atoms-mcp-prod
from atoms_mcp.server import create_consolidated_server

mcp = create_consolidated_server()

# Get all metrics
metrics = await mcp.call_tool("monitoring_tool", {"operation": "get_metrics"})

# Get performance
performance = await mcp.call_tool("monitoring_tool", {"operation": "get_performance_profile"})

# Get usage analytics
analytics = await mcp.call_tool("monitoring_tool", {"operation": "get_usage_analytics"})

# Get health
health = await mcp.call_tool("health_check", {})
```

## Summary

**Current State**: 
- ✅ Performance monitoring exists
- ✅ Cache hit/miss tracking exists
- ✅ Query performance tracking exists
- ❌ Actual usage/cost tracking missing
- ❌ Service-level aggregation missing

**To get actual usage**: Use service provider dashboards (Upstash, Supabase, Vercel) or implement API integrations.
