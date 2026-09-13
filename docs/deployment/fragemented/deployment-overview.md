# CRUN Deployment Guide

**Deploy CRUN to production environments with confidence**

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Deployment Options](#deployment-options)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Local Deployment](#local-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Container Deployment (Docker)](#container-deployment-docker)
7. [Verification & Validation](#verification--validation)
8. [Rollback Procedures](#rollback-procedures)
9. [Scaling Considerations](#scaling-considerations)

---

## Deployment Overview

CRUN can be deployed in multiple ways depending on your infrastructure and use case:

| Deployment Type | Use Case                         | Complexity  | Scalability      |
| --------------- | -------------------------------- | ----------- | ---------------- |
| **Local**       | Development, testing             | Low         | Single machine   |
| **Server**      | Production on dedicated hardware | Medium      | Up to 100 agents |
| **Docker**      | Container orchestration          | High        | Multi-container  |
| **Kubernetes**  | Enterprise scale                 | High        | 1000+ agents     |
| **Cloud**       | AWS/GCP/Azure                    | Medium-High | Auto-scaling     |

---

## Deployment Options

### 1. Local Deployment

- **Best for:** Development, proof-of-concept
- **Requirements:** Single machine with Python 3.11+
- **Setup time:** 15 minutes
- **Scalability:** Limited to single machine resources

### 2. Server Deployment

- **Best for:** Production on dedicated hardware
- **Requirements:** Ubuntu/Debian server, systemd
- **Setup time:** 30 minutes
- **Scalability:** Up to 100 agents with proper resources

### 3. Docker Deployment

- **Best for:** Cloud platforms, CI/CD pipelines
- **Requirements:** Docker/Docker Compose
- **Setup time:** 20 minutes
- **Scalability:** Unlimited (horizontal scaling)

### 4. Kubernetes Deployment

- **Best for:** Enterprise, high availability
- **Requirements:** Kubernetes cluster
- **Setup time:** 1-2 hours
- **Scalability:** Unlimited (auto-scaling)

---

## Pre-Deployment Checklist

Before deploying CRUN, ensure:

- [ ] Python 3.11+ installed and tested
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -e ".[all]"`)
- [ ] `.env` file configured with production settings
- [ ] API keys configured (OpenAI, Anthropic, etc.)
- [ ] Database prepared (PostgreSQL for production)
- [ ] Redis/NATS configured (if using distributed mode)
- [ ] Sufficient disk space available (2GB minimum)
- [ ] Sufficient RAM available (8GB recommended)
- [ ] Firewall rules configured (ports: 8000, 8001, etc.)
- [ ] SSL/TLS certificates obtained (for HTTPS)
- [ ] Backup strategy defined
- [ ] Monitoring/alerting configured
- [ ] Log aggregation setup

---

## Local Deployment

### Step 1: Install CRUN

```bash
cd /path/to/crun
python3 -m venv venv
source venv/bin/activate
pip install -e ".[all]"
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

**Key settings for local deployment:**

```env
CRUN_ENVIRONMENT=development
CRUN_DEBUG=false
CRUN_LOG_LEVEL=INFO
CRUN_WORKSPACE_ROOT=/path/to/workspace
CRUN_WORKSPACE_LOG_DIR=/path/to/logs
CRUN_AGENTS_MAX_WORKERS=4
```

### Step 3: Test Installation

```bash
# Test CLI
crun --help

# Test GUI
crun gui

# Test TUI
crun tui
```

### Step 4: Create Projects

```bash
# Generate first plan
crun ai-plan generate-massive project_spec.txt -o plan.md

# Monitor execution
crun ai-plan monitor plan.md --workers 8
```

---

## Cloud Deployment

### AWS Deployment

#### Step 1: Launch EC2 Instance

```bash
# Launch Ubuntu 22.04 LTS t3.xlarge instance
# Configure security group to allow:
#   - Port 22 (SSH)
#   - Port 8000 (CRUN API)
#   - Port 8001 (WebSocket)
```

#### Step 2: SSH into Instance

```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

#### Step 3: Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip git

# Clone or upload CRUN
git clone <repository> crun
cd crun
```

#### Step 4: Setup and Deploy

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[all]"

# Configure environment
cp .env.example .env
nano .env  # Set your API keys and settings

# Start CRUN service
nohup crun gui --host 0.0.0.0 --port 8000 &
```

#### Step 5: Setup Systemd Service

Create `/etc/systemd/system/crun.service`:

```ini
[Unit]
Description=CRUN Multi-Agent Orchestration
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/crun
Environment="PATH=/home/ubuntu/crun/venv/bin"
ExecStart=/home/ubuntu/crun/venv/bin/python -m crun.cli.main gui --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable crun
sudo systemctl start crun
sudo systemctl status crun
```

### GCP Deployment

Similar steps for Google Cloud Platform:

1. Create Compute Engine VM (Ubuntu 22.04)
2. Install dependencies
3. Deploy CRUN
4. Configure Cloud Load Balancer for HA
5. Setup Cloud Logging/Monitoring

### Azure Deployment

Similar steps for Microsoft Azure:

1. Create Virtual Machine
2. Install dependencies
3. Deploy CRUN
4. Use Azure App Service or Container Instances
5. Configure Azure Monitor

---

## Container Deployment (Docker)

### Step 1: Create Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Install CRUN
RUN pip install --no-cache-dir -e ".[all]"

# Expose ports
EXPOSE 8000 8001

# Default command
CMD ["crun", "gui", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Create Docker Compose

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  crun:
    build: .
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - CRUN_ENVIRONMENT=production
      - CRUN_DEBUG=false
      - CRUN_DB_HOST=postgres
      - CRUN_REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/.crun/logs
      - ./cache:/app/.crun/cache
    restart: always

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=crun
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=crun
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Step 3: Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f crun

# Stop services
docker-compose down
```

### Step 4: Verify Container

```bash
# Check services running
docker-compose ps

# Access CRUN
curl http://localhost:8000/health

# View logs
docker-compose logs crun
```

---

## Verification & Validation

### Health Checks

#### 1. CLI Test

```bash
crun --version
crun --help
```

#### 2. API Test

```bash
# If running with API
curl -X GET http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "3.0.0"}
```

#### 3. Planning Test

```bash
# Generate a test plan
echo "Build a test app" | crun ai-plan generate-massive - -o test_plan.md

# Verify plan created
ls -la test_plan.md
```

#### 4. Database Test

```bash
# Test PostgreSQL connection (if configured)
psql -h localhost -U crun -d crun -c "SELECT 1;"
```

#### 5. Agent Test

```bash
# Test plan execution
crun ai-plan monitor test_plan.md --workers 1
```

### Smoke Tests

```bash
#!/bin/bash
# smoke_test.sh

echo "Testing CRUN deployment..."

# Test 1: Version
crun --version || { echo "Version check failed"; exit 1; }

# Test 2: Help
crun --help > /dev/null || { echo "Help check failed"; exit 1; }

# Test 3: Planner command group
crun ai-plan --help > /dev/null || { echo "Planner help check failed"; exit 1; }

# Test 4: Create test plan
echo "Test" | crun ai-plan generate-massive - -o test_plan.md || { echo "Plan generation failed"; exit 1; }

# Test 5: Cleanup
rm test_plan.md

echo "All smoke tests passed!"
```

Run tests:

```bash
bash smoke_test.sh
```

---

## Rollback Procedures

### Scenario 1: Rollback Docker Container

```bash
# View deployment history
docker-compose ps
docker images

# Rollback to previous image
docker-compose down
docker-compose up -d  # Uses previous image if available
```

### Scenario 2: Rollback Systemd Service

```bash
# Stop current version
sudo systemctl stop crun

# Restore from backup
cd /home/ubuntu/crun
git checkout HEAD~1  # Go to previous commit

# Restart with previous version
sudo systemctl start crun
sudo systemctl status crun
```

### Scenario 3: Database Rollback

```bash
# If using PostgreSQL, restore from backup
pg_restore -h localhost -U crun -d crun /path/to/backup.sql

# Verify restoration
psql -h localhost -U crun -d crun -c "SELECT COUNT(*) FROM plans;"
```

### Scenario 4: File-Based Rollback

```bash
# Backup before deployment
tar -czf crun_backup_$(date +%Y%m%d_%H%M%S).tar.gz /path/to/crun

# Restore from backup
tar -xzf crun_backup_20260220_100000.tar.gz -C /
```

---

## Scaling Considerations

### Horizontal Scaling (Multiple Machines)

For scaling to multiple machines:

1. **Use NATS for messaging:** Configure NATS cluster for agent coordination
2. **Use PostgreSQL:** Central database for state
3. **Use Redis:** Distributed caching
4. **Load Balancer:** Route requests across instances

**Example NATS configuration:**

```yaml
# nats.conf
cluster {
  name: "crun-cluster"
  listen: 0.0.0.0:4222
  routes: [
    "nats://nats1:6222",
    "nats://nats2:6222",
    "nats://nats3:6222"
  ]
}
```

### Vertical Scaling (Single Machine)

For scaling on a single machine:

1. **Increase resources:** RAM, CPU, disk space
2. **Adjust worker pools:** `CRUN_AGENTS_MAX_WORKERS`
3. **Database optimization:** Index frequently queried columns
4. **Cache optimization:** Redis memory allocation

**Configuration for high-load:**

```env
CRUN_AGENTS_MAX_WORKERS=100
CRUN_AGENTS_EXECUTION_TIMEOUT=600
CRUN_RESOURCES_TARGET_FD_LIMIT=65536
CRUN_PLANNING_RESOURCE_ALLOCATION_STRATEGY=aggressive
```

### Performance Tuning

```bash
# Monitor performance
watch -n 1 'ps aux | grep crun'

# Check resource usage
top -p $(pgrep -f "crun")

# Check file descriptors
lsof -p $(pgrep -f "crun") | wc -l

# Check database connections
psql -h localhost -U crun -d crun -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Troubleshooting Deployments

### Issue: Service Won't Start

```bash
# Check logs
systemctl status crun -l

# Check error
journalctl -u crun -n 50

# Verify binary exists
which crun
```

### Issue: Out of Memory

```bash
# Check memory usage
free -h

# Reduce worker count
CRUN_AGENTS_MAX_WORKERS=5

# Enable memory profiling
python -m memory_profiler crun
```

### Issue: Database Connection Failed

```bash
# Test connection
psql -h localhost -U crun -d crun

# Check credentials in .env
grep CRUN_DB .env

# Verify PostgreSQL running
systemctl status postgresql
```

---

## Monitoring in Production

### Key Metrics to Monitor

- **CPU Usage:** Should stay below 80%
- **Memory Usage:** Should not exceed 85% of available
- **Disk Space:** Maintain at least 10% free
- **Agent Count:** Track active agents
- **Task Success Rate:** Monitor for anomalies
- **API Response Time:** Should be < 1 second
- **Database Size:** Monitor growth rate

### Example Monitoring Setup

```bash
# Using Prometheus + Grafana
# 1. Install Prometheus
# 2. Configure scrape targets
# 3. Install Grafana
# 4. Create dashboards
# 5. Set up alerting
```

---

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-20
