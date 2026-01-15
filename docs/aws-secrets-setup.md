# AWS Secrets Manager Setup for ECS

## Secrets to Store

Create a secret in AWS Secrets Manager with the following JSON structure:

```json
{
  "SECRET_KEY": "your-64-char-random-key",
  "ADMIN_PASSWORD": "your-strong-admin-password",
  "DATABASE_URL": "postgresql+asyncpg://user:pass@rds-endpoint:5432/reviewguide_db",
  "OPENAI_API_KEY": "sk-...",
  "ANTHROPIC_API_KEY": "sk-ant-...",
  "PERPLEXITY_API_KEY": "pplx-...",
  "EBAY_APP_ID": "...",
  "EBAY_CERT_ID": "...",
  "EBAY_CAMPAIGN_ID": "...",
  "AMAZON_ACCESS_KEY": "...",
  "AMAZON_SECRET_KEY": "...",
  "BOOKING_API_KEY": "...",
  "SKYSCANNER_API_KEY": "...",
  "AMADEUS_API_KEY": "...",
  "AMADEUS_API_SECRET": "...",
  "IPINFO_TOKEN": "...",
  "LANGFUSE_PUBLIC_KEY": "pk-lf-...",
  "LANGFUSE_SECRET_KEY": "sk-lf-..."
}
```

## Create Secret via AWS CLI

```bash
aws secretsmanager create-secret \
  --name reviewguide/production \
  --description "ReviewGuide production secrets" \
  --secret-string file://secrets.json \
  --region us-east-1
```

## ECS Task Definition - Referencing Secrets

In your task definition JSON, reference secrets like this:

```json
{
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/reviewguide-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        { "name": "ENV", "value": "production" },
        { "name": "DEBUG", "value": "false" },
        { "name": "APP_PORT", "value": "8000" },
        { "name": "REDIS_URL", "value": "redis://your-elasticache:6379" },
        { "name": "LOG_LEVEL", "value": "WARNING" },
        { "name": "LOG_FORMAT", "value": "json" }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:reviewguide/production:SECRET_KEY::"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:reviewguide/production:DATABASE_URL::"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:reviewguide/production:OPENAI_API_KEY::"
        },
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:reviewguide/production:ANTHROPIC_API_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/reviewguide-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "executionRoleArn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole"
}
```

## IAM Policy for Task Execution Role

Attach this policy to your ECS task execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789:secret:reviewguide/*"
      ]
    }
  ]
}
```

## Generate Secret Key

```bash
# Generate a secure 64-character secret key
openssl rand -hex 32
```