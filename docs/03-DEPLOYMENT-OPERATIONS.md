# 3. Deployment and Operations

## Deployment Overview

**Current Setup**: Manual deployments to AWS ECS Fargate
**CI/CD**: Not currently implemented (manual process)
**Region**: ca-central-1 (Canada Central)

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Quick Start
```bash
# 1. Clone repository
git clone <repository-url>
cd ReviewGuide

# 2. Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Setup backend environment
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration

# 4. Setup database
./setup.sh --reset    # Creates database, runs migrations, creates admin user

# 5. Setup frontend
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with API URL

# 6. Start all services
cd ..
./run.sh
```

### Development URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Redis: localhost:6379

### Useful Scripts
```bash
./run.sh          # Start all services (backend, frontend, redis)
./run.sh kill     # Kill all running services
./run.sh clear    # Clear terminal and start services
./setup.sh        # Run database migrations only
./setup.sh --reset # Full database reset with migrations
```

---

## Docker Local Development

```bash
# Start all services
docker-compose up --build

# Start with migrations profile
docker-compose --profile setup up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Clean up volumes (reset data)
docker-compose down -v
```

---

## ECS Deployment Process

### Step 1: Build Docker Images

**Backend:**
```bash
# Navigate to project root
cd /path/to/ReviewGuide

# Build backend image (context is project root)
docker build -t reviewguide-backend -f backend/Dockerfile .

# Tag for ECR
docker tag reviewguide-backend:latest <AWS_ACCOUNT_ID>.dkr.ecr.ca-central-1.amazonaws.com/reviewguide-backend:latest
```

**Frontend:**
```bash
# Navigate to frontend directory
cd frontend

# Build with API URL baked in
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://review-guide-backend-173284151.ca-central-1.elb.amazonaws.com \
  -t reviewguide-frontend .

# Tag for ECR
docker tag reviewguide-frontend:latest <AWS_ACCOUNT_ID>.dkr.ecr.ca-central-1.amazonaws.com/reviewguide-frontend:latest
```

### Step 2: Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.ca-central-1.amazonaws.com

# Push backend
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ca-central-1.amazonaws.com/reviewguide-backend:latest

# Push frontend
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ca-central-1.amazonaws.com/reviewguide-frontend:latest
```

### Step 3: Update ECS Services

```bash
# Force new deployment for backend
aws ecs update-service \
  --cluster reviewguide-cluster \
  --service reviewguide-backend \
  --force-new-deployment \
  --region ca-central-1

# Force new deployment for frontend
aws ecs update-service \
  --cluster reviewguide-cluster \
  --service reviewguide-frontend \
  --force-new-deployment \
  --region ca-central-1
```

### Step 4: Monitor Deployment

```bash
# Watch service deployments
aws ecs describe-services \
  --cluster reviewguide-cluster \
  --services reviewguide-backend reviewguide-frontend \
  --region ca-central-1

# View task logs in CloudWatch
aws logs tail /ecs/reviewguide-backend --follow --region ca-central-1
aws logs tail /ecs/reviewguide-frontend --follow --region ca-central-1
```

---

## Complete Deployment Script

Here's a complete deployment script you can use:

```bash
#!/bin/bash
# deploy.sh - Deploy ReviewGuide to ECS

set -e

AWS_ACCOUNT_ID="<YOUR_AWS_ACCOUNT_ID>"
AWS_REGION="ca-central-1"
ECR_BACKEND="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/reviewguide-backend"
ECR_FRONTEND="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/reviewguide-frontend"
BACKEND_API_URL="https://review-guide-backend-173284151.ca-central-1.elb.amazonaws.com"
ECS_CLUSTER="reviewguide-cluster"

echo "=== Logging into ECR ==="
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "=== Building Backend ==="
docker build -t reviewguide-backend -f backend/Dockerfile .
docker tag reviewguide-backend:latest $ECR_BACKEND:latest
docker push $ECR_BACKEND:latest

echo "=== Building Frontend ==="
cd frontend
docker build --build-arg NEXT_PUBLIC_API_URL=$BACKEND_API_URL -t reviewguide-frontend .
docker tag reviewguide-frontend:latest $ECR_FRONTEND:latest
docker push $ECR_FRONTEND:latest
cd ..

echo "=== Updating ECS Services ==="
aws ecs update-service --cluster $ECS_CLUSTER --service reviewguide-backend --force-new-deployment --region $AWS_REGION
aws ecs update-service --cluster $ECS_CLUSTER --service reviewguide-frontend --force-new-deployment --region $AWS_REGION

echo "=== Deployment initiated! ==="
echo "Monitor with: aws ecs describe-services --cluster $ECS_CLUSTER --services reviewguide-backend reviewguide-frontend --region $AWS_REGION"
```

---

## Database Migrations in Production

### Option 1: Automatic (in Dockerfile)
The backend Dockerfile runs migrations automatically on startup:
```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### Option 2: Manual via ECS Exec
```bash
# Enable ECS Exec on service if not already enabled
aws ecs update-service \
  --cluster reviewguide-cluster \
  --service reviewguide-backend \
  --enable-execute-command \
  --region ca-central-1

# Get task ID
TASK_ID=$(aws ecs list-tasks --cluster reviewguide-cluster --service-name reviewguide-backend --query 'taskArns[0]' --output text --region ca-central-1)

# Execute migration
aws ecs execute-command \
  --cluster reviewguide-cluster \
  --task $TASK_ID \
  --container backend \
  --interactive \
  --command "alembic upgrade head" \
  --region ca-central-1
```

### Option 3: One-time Migration Task
Use docker-compose migration profile or run a one-off ECS task with the migration command.

---

## Background Workers / Scheduled Jobs

### Current Background Tasks

The backend includes a background scheduler (APScheduler) that runs:

1. **Link Health Checker** - Every 6 hours
   - Checks affiliate link health
   - Updates database with link status
   - Configured via: `ENABLE_LINK_HEALTH_CHECKER`, `LINK_HEALTH_CHECK_INTERVAL_HOURS`

### No External Workers
All background tasks run within the main backend process. There are no separate worker containers or external schedulers (like Celery) currently in use.

---

## Health Checks

### Backend Health Endpoint
```bash
curl https://review-guide-backend-173284151.ca-central-1.elb.amazonaws.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### Frontend Health
The frontend health check is a simple HTTP request to the root path.

### ECS Health Check Configuration
Both services have health checks configured in their Dockerfiles and ECS task definitions.

---

## Logging and Monitoring

### CloudWatch Logs
- Backend logs: `/ecs/reviewguide-backend`
- Frontend logs: `/ecs/reviewguide-frontend`

### Log Format
Backend logs are in JSON format for easy parsing:
```bash
LOG_FORMAT=json
LOG_LEVEL=WARNING
```

### Langfuse Tracing
LLM calls and traces are sent to Langfuse for observability:
- Dashboard: https://cloud.langfuse.com
- Credentials in environment variables

### Viewing Logs
```bash
# CloudWatch CLI
aws logs tail /ecs/reviewguide-backend --follow --region ca-central-1

# Or use CloudWatch Console
# https://ca-central-1.console.aws.amazon.com/cloudwatch/home?region=ca-central-1#logsV2:log-groups
```

---

## Rollback Procedure

### Quick Rollback
```bash
# List recent image tags
aws ecr describe-images \
  --repository-name reviewguide-backend \
  --query 'imageDetails[*].imageTags' \
  --region ca-central-1

# Update task definition to use previous image tag
# Then force new deployment
aws ecs update-service \
  --cluster reviewguide-cluster \
  --service reviewguide-backend \
  --force-new-deployment \
  --region ca-central-1
```

### Database Rollback
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

---

## Scaling

### Manual Scaling
```bash
# Scale backend to 2 tasks
aws ecs update-service \
  --cluster reviewguide-cluster \
  --service reviewguide-backend \
  --desired-count 2 \
  --region ca-central-1
```

### Auto Scaling (if configured)
Check ECS Service Auto Scaling settings in AWS Console for target tracking policies.

---

## Troubleshooting

### Common Issues

1. **Task keeps failing to start**
   - Check CloudWatch logs for error messages
   - Verify environment variables in task definition
   - Check database/Redis connectivity

2. **Database connection errors**
   - Verify RDS security group allows ECS tasks
   - Check DATABASE_URL is correct
   - Verify RDS is running

3. **Redis connection errors**
   - Verify MemoryDB security group settings
   - Check REDIS_URL is correct
   - Verify Redis cluster is running

4. **Frontend can't reach backend**
   - Verify NEXT_PUBLIC_API_URL is correct
   - Check ALB health checks
   - Verify CORS_ORIGINS includes frontend URL