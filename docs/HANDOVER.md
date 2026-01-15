# ReviewGuide.ai - Complete Project Handover

## Table of Contents

1. [Source Code Overview](./01-SOURCE-CODE-OVERVIEW.md)
2. [Environment and Configuration](./02-ENVIRONMENT-CONFIGURATION.md)
3. [Deployment and Operations](./03-DEPLOYMENT-OPERATIONS.md)
4. [Architecture Overview](./04-ARCHITECTURE-OVERVIEW.md)
5. [External Services and IAM Close-Out](./05-EXTERNAL-SERVICES-IAM.md)

---

## Quick Start Summary

### Repository Structure
```
ReviewGuide/
├── backend/                 # FastAPI Python backend
├── frontend/                # Next.js React frontend
├── docs/                    # Documentation
├── docker-compose.yml       # Local Docker development
├── run.sh                   # Local development startup script
├── setup.sh                 # Database setup script
└── requirements.txt         # Root Python dependencies
```

### Key Technologies
- **Backend**: Python 3.11, FastAPI, LangGraph, SQLAlchemy, Alembic
- **Frontend**: Next.js 14, React, TypeScript, TailwindCSS
- **Database**: PostgreSQL 15 (AWS RDS)
- **Cache**: Redis 7 (AWS MemoryDB/ElastiCache)
- **AI/LLM**: OpenAI GPT-4o, Perplexity, Anthropic Claude
- **Deployment**: AWS ECS Fargate, ECR, Application Load Balancer

### Current Production URLs
- **Frontend**: `https://review-guide-frontend-2141173391.ca-central-1.elb.amazonaws.com`
- **Backend API**: `https://review-guide-backend-173284151.ca-central-1.elb.amazonaws.com`

### AWS Region
All infrastructure is deployed in **ca-central-1** (Canada Central).

---

## Access Requirements for Handover

### GitHub Repository
- Repository contains all source code
- Ensure the new developer has repository access

### AWS Console Access
- ECS clusters and services
- ECR repositories
- RDS database instance
- MemoryDB/ElastiCache Redis cluster
- Secrets Manager
- CloudWatch Logs
- Application Load Balancers

### Third-Party Service Accounts
See [External Services documentation](./05-EXTERNAL-SERVICES-IAM.md) for complete list.

---

## Contact Information

For questions about this handover, please contact the original developer.

---

**Last Updated**: January 2025