# 5. External Services and IAM Close-Out

## External Services Summary

### LLM / AI Services

| Service | Account Owner | Purpose | Status |
|---------|---------------|---------|--------|
| **OpenAI** | Client | GPT-4o models, web search, moderation | Active |
| **Anthropic Claude** | Client | Alternative LLM (configured but may not be active) | Configured |
| **Perplexity** | Client | AI-powered web search | Active |

**Notes:**
- OpenAI API key is the primary LLM provider
- Perplexity used for product/service search enhancement
- API keys should be rotated and ownership transferred to client

---

### Affiliate / E-commerce APIs

| Service | Account Owner | Purpose | Status |
|---------|---------------|---------|--------|
| **eBay Partner Network** | Developer | Product affiliate links | Active |
| **Amazon Associates** | Client (if any) | Product affiliate links | Configured but disabled |

**eBay Partner Network:**
- App ID: `MikeJahs-test-PRD-e8135f6e7-33e60d50`
- **Action Required**: Transfer eBay developer account to client OR client creates new eBay partner account

**Amazon Associates:**
- Currently disabled (`AMAZON_API_ENABLED=false`)
- Associate tag: `reviewguideai-20`
- **Action Required**: Client should create their own Amazon Associates account

---

### Travel APIs

| Service | Account Owner | Purpose | Status |
|---------|---------------|---------|--------|
| **Amadeus** | Developer/Client | Hotel and flight search | Active |
| **Booking.com (RapidAPI)** | N/A | Hotel search | Configured |
| **Skyscanner (RapidAPI)** | N/A | Flight search | Configured |

**Amadeus:**
- Primary travel provider currently in use
- **Action Required**: Verify account ownership and transfer if needed

**RapidAPI Services:**
- Booking.com and Skyscanner require RapidAPI subscription
- **Action Required**: Client should create RapidAPI account and subscribe to required APIs

---

### Utility Services

| Service | Account Owner | Purpose | Status |
|---------|---------------|---------|--------|
| **IPInfo** | Developer/Client | IP geolocation for user location | Active |
| **Langfuse** | Developer/Client | LLM observability and tracing | Active |

**IPInfo:**
- Token: `5353a4cedf4678`
- Free tier may be sufficient
- **Action Required**: Verify account ownership

**Langfuse:**
- Cloud-hosted at https://cloud.langfuse.com
- Used for tracing LLM calls
- **Action Required**: Transfer account or client creates new account

---

## Services Running Outside Client AWS Account

### Confirmation of External Services

| External Service | Runs In | Notes |
|------------------|---------|-------|
| OpenAI API | OpenAI Cloud | API calls only |
| Anthropic API | Anthropic Cloud | API calls only |
| Perplexity API | Perplexity Cloud | API calls only |
| eBay API | eBay Cloud | API calls only |
| Amadeus API | Amadeus Cloud | API calls only |
| Langfuse | Langfuse Cloud | Tracing data stored externally |
| IPInfo | IPInfo Cloud | API calls only |

**All core infrastructure (ECS, RDS, Redis, ALB) runs within the client's AWS account.**

No databases, servers, or persistent storage runs outside the client's AWS account.

---

## Developer Account Access to Transfer

### Accounts That May Need Transfer

1. **eBay Partner Network**
   - Current: Developer account
   - Action: Client creates new account OR developer transfers access

2. **Langfuse**
   - Current: May be developer account
   - Action: Export data, transfer project, or client creates new account

3. **IPInfo**
   - Current: May be developer account
   - Action: Client creates new account if needed

### Client-Owned Accounts (Verify)

1. **OpenAI** - Verify API key ownership
2. **Perplexity** - Verify API key ownership
3. **Amadeus** - Verify API key ownership
4. **Anthropic** - Verify API key ownership (if using)

---

## IAM Close-Out Checklist

### Work Confirmation

- [x] All development work was performed within client's AWS account
- [x] No resources created in developer's personal AWS account
- [x] All infrastructure runs in ca-central-1 region
- [x] ECR repositories contain all container images
- [x] RDS database contains all application data
- [x] Secrets Manager contains production credentials

### IAM Permissions to Review/Remove

After handover is complete, the client should:

1. **Remove Developer IAM User/Role**
   - Remove any IAM users created for the developer
   - Remove any assumed role permissions

2. **Review IAM Policies**
   - Check for any overly permissive policies
   - Ensure least-privilege principle

3. **Rotate Credentials**
   - Rotate AWS access keys
   - Rotate database passwords
   - Rotate API keys stored in Secrets Manager

4. **Enable CloudTrail** (if not already)
   - Monitor for unauthorized access
   - Review past activity

### Security Recommendations Post-Handover

1. **Enable MFA** on all AWS IAM users
2. **Enable AWS CloudTrail** for audit logging
3. **Enable AWS GuardDuty** for threat detection
4. **Review Security Groups** for any overly permissive rules
5. **Set up AWS Budgets** for cost monitoring
6. **Enable RDS automated backups** if not already enabled

---

## API Keys Rotation Checklist

After handover, rotate these API keys:

| Service | Key Location | Action |
|---------|--------------|--------|
| OpenAI | AWS Secrets Manager / .env | Rotate in OpenAI dashboard |
| Perplexity | AWS Secrets Manager / .env | Rotate in Perplexity dashboard |
| Anthropic | AWS Secrets Manager / .env | Rotate in Anthropic console |
| eBay | AWS Secrets Manager / .env | Rotate in eBay Developer Portal |
| Amadeus | AWS Secrets Manager / .env | Rotate in Amadeus portal |
| IPInfo | AWS Secrets Manager / .env | Rotate in IPInfo dashboard |
| Langfuse | AWS Secrets Manager / .env | Rotate in Langfuse settings |
| SECRET_KEY | AWS Secrets Manager / .env | Generate new: `openssl rand -hex 32` |
| ADMIN_PASSWORD | AWS Secrets Manager / .env | Change to new secure password |
| Database Password | AWS Secrets Manager / RDS | Rotate via RDS console |

---

## Handover Completion Checklist

### Developer Confirmation

- [ ] All source code delivered (GitHub/ZIP)
- [ ] All documentation provided
- [ ] All environment variables documented
- [ ] All AWS resources documented
- [ ] All external service accounts identified
- [ ] Database schema migrations up to date
- [ ] No pending work or unfinished features (unless documented)

### Client Action Items

- [ ] Verify repository access
- [ ] Verify AWS console access to all resources
- [ ] Verify ability to deploy updates
- [ ] Transfer/create external service accounts
- [ ] Remove developer IAM permissions
- [ ] Rotate all credentials
- [ ] Test application functionality

---

## Final Notes

### Support Period
If any questions arise during the transition, please document them and reach out within the agreed support window.

### Known Issues / Technical Debt
Refer to `REMAINING_TASKS.md` in the repository root for any documented technical debt or pending improvements.

### Emergency Contacts
For critical production issues during transition:
- Check CloudWatch logs first
- Verify all services are running in ECS console
- Check RDS and Redis connectivity

---

**Handover Complete**

Once all checklist items are verified, the developer will confirm completion and the client can remove developer access permissions.