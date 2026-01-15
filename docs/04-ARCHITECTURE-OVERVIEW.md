# 4. Architecture Overview

## AWS Services Used

| Service | Purpose | Resource Name/ID |
|---------|---------|------------------|
| **ECS Fargate** | Container orchestration | `reviewguide-cluster` |
| **ECR** | Container registry | `reviewguide-backend`, `reviewguide-frontend` |
| **RDS PostgreSQL** | Primary database | `review-guide-postgres` |
| **MemoryDB for Redis** | Cache and sessions | `review-guide-redis` |
| **Application Load Balancer** | HTTP/HTTPS routing | Backend & Frontend ALBs |
| **CloudWatch** | Logging and monitoring | `/ecs/reviewguide-*` |
| **Secrets Manager** | Secure credentials | `reviewguide/production` |
| **VPC** | Network isolation | Default or custom VPC |
| **Security Groups** | Network access control | Per-service SGs |

---

## Architecture Diagram

```
                                    INTERNET
                                        │
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
        ┌───────────────────────┐           ┌───────────────────────┐
        │   Application Load    │           │   Application Load    │
        │   Balancer (Frontend) │           │   Balancer (Backend)  │
        │   Port 80/443         │           │   Port 80/443         │
        └───────────────────────┘           └───────────────────────┘
                    │                                       │
                    ▼                                       ▼
        ┌───────────────────────┐           ┌───────────────────────┐
        │    ECS Service        │           │    ECS Service        │
        │    (Frontend)         │           │    (Backend)          │
        │    Next.js            │ ────────► │    FastAPI            │
        │    Port 3000          │   API     │    Port 8000          │
        └───────────────────────┘  Calls    └───────────────────────┘
                                                    │
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
        │   RDS PostgreSQL  │           │   MemoryDB Redis  │           │   External APIs   │
        │   (Database)      │           │   (Cache/Sessions)│           │   (LLM, Search)   │
        │   Port 5432       │           │   Port 6379       │           │                   │
        └───────────────────┘           └───────────────────┘           └───────────────────┘
```

---

## ECS Configuration

### Cluster
- **Name**: `reviewguide-cluster`
- **Type**: Fargate (serverless)
- **Region**: ca-central-1

### Backend Service
- **Service Name**: `reviewguide-backend`
- **Container Port**: 8000
- **CPU**: 256-1024 (configurable)
- **Memory**: 512-2048 MB (configurable)
- **Desired Count**: 1 (adjust for scaling)

### Frontend Service
- **Service Name**: `reviewguide-frontend`
- **Container Port**: 3000
- **CPU**: 256-512
- **Memory**: 512-1024 MB
- **Desired Count**: 1

### Task Definition Structure

**Backend Task Definition:**
```json
{
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account>.dkr.ecr.ca-central-1.amazonaws.com/reviewguide-backend:latest",
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "environment": [
        {"name": "ENV", "value": "production"},
        {"name": "DEBUG", "value": "false"},
        {"name": "APP_PORT", "value": "8000"},
        {"name": "REDIS_URL", "value": "redis://..."},
        {"name": "LOG_LEVEL", "value": "WARNING"}
      ],
      "secrets": [
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/reviewguide-backend",
          "awslogs-region": "ca-central-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

## ECR Repositories

| Repository | Purpose |
|------------|---------|
| `reviewguide-backend` | Backend FastAPI container images |
| `reviewguide-frontend` | Frontend Next.js container images |

### Image Tagging Strategy
- `latest` - Most recent deployment
- `v1.0.0` - Versioned releases (if implemented)
- Consider adding git commit SHA tags for traceability

---

## RDS PostgreSQL Configuration

- **Instance Identifier**: `review-guide-postgres`
- **Engine**: PostgreSQL 15
- **Endpoint**: `review-guide-postgres.c72wquegyskv.ca-central-1.rds.amazonaws.com`
- **Port**: 5432
- **Database Name**: `postgres`

### Connection String Format
```
postgresql+asyncpg://username:password@endpoint:5432/dbname
```

### Security
- Within private subnet (if VPC configured)
- Security group allows inbound from ECS tasks only
- Credentials stored in Secrets Manager

---

## MemoryDB/ElastiCache Redis

- **Cluster Endpoint**: `clustercfg.review-guide-redis.a7w3fb.memorydb.ca-central-1.amazonaws.com`
- **Port**: 6379
- **Engine**: Redis 7

### Connection String Format
```
redis://endpoint:6379/0
```

### Usage
- Session storage
- Search result caching
- Chat history caching
- Rate limiting state

### Security
- Within private subnet
- Security group allows inbound from ECS tasks only

---

## Application Load Balancers

### Backend ALB
- **DNS**: `review-guide-backend-173284151.ca-central-1.elb.amazonaws.com`
- **Listeners**: HTTP (80), HTTPS (443) if configured
- **Target Group**: Backend ECS service on port 8000
- **Health Check**: `GET /health`

### Frontend ALB
- **DNS**: `review-guide-frontend-2141173391.ca-central-1.elb.amazonaws.com`
- **Listeners**: HTTP (80), HTTPS (443) if configured
- **Target Group**: Frontend ECS service on port 3000
- **Health Check**: `GET /`

---

## CloudWatch Configuration

### Log Groups
| Log Group | Service |
|-----------|---------|
| `/ecs/reviewguide-backend` | Backend container logs |
| `/ecs/reviewguide-frontend` | Frontend container logs |

### Retention
- Default: 30 days (adjust as needed)

### Log Insights Queries

**Find errors:**
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50
```

**API request latency:**
```
fields @timestamp, @message
| filter @message like /request completed/
| parse @message "* ms" as latency
| stats avg(latency), max(latency), min(latency) by bin(5m)
```

---

## Security Groups

### Backend Security Group
- **Inbound**:
  - Port 8000 from ALB security group
- **Outbound**:
  - All traffic (for external API calls)

### Frontend Security Group
- **Inbound**:
  - Port 3000 from ALB security group
- **Outbound**:
  - Port 8000 to Backend ALB (API calls)

### RDS Security Group
- **Inbound**:
  - Port 5432 from Backend security group

### Redis Security Group
- **Inbound**:
  - Port 6379 from Backend security group

---

## S3 Usage

Currently, **S3 is not actively used** in the application. Future uses might include:
- Static asset storage
- File uploads
- Backup storage

---

## VPC Configuration

The services run within a VPC with:
- Public subnets (for ALBs)
- Private subnets (for ECS tasks, RDS, Redis)
- NAT Gateway (for outbound internet from private subnets)

---

## Data Flow

### Request Flow
1. User browser sends request to Frontend ALB
2. ALB routes to Frontend ECS task
3. Frontend makes API call to Backend ALB
4. ALB routes to Backend ECS task
5. Backend queries PostgreSQL/Redis as needed
6. Backend calls external APIs (OpenAI, etc.)
7. Response flows back through the chain

### Chat Streaming Flow
1. Frontend opens SSE connection to `/v1/chat/stream`
2. Backend processes through LangGraph workflow
3. Tokens streamed back via SSE
4. Frontend renders incrementally

---

## Scaling Considerations

### Horizontal Scaling
- ECS services can scale to multiple tasks
- ALB automatically distributes traffic
- Redis handles session sharing between tasks

### Current Limitations
- Single RDS instance (can upgrade to Multi-AZ)
- Consider read replicas for heavy read loads

### Recommended Scaling Points
- Backend: 2+ tasks for high availability
- Frontend: 2+ tasks for high availability
- Enable ECS Service Auto Scaling based on CPU/memory