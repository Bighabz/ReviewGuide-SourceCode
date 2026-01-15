# Backend Scripts

## Link Health Checker

Monitors affiliate link health and updates the database with link status.

### Usage

```bash
# Check current statistics without running health checks
python backend/scripts/check_link_health.py --stats-only

# Run full health check on all affiliate links
python backend/scripts/check_link_health.py

# Customize timeout and concurrency
python backend/scripts/check_link_health.py --timeout 15 --max-concurrent 20
```

### Options

- `--stats-only`: Only show current statistics without checking links
- `--timeout SECONDS`: Request timeout in seconds (default: 10)
- `--max-concurrent N`: Maximum concurrent health checks (default: 10)

### What it does

1. **Stats Only Mode**: Queries the database and shows current link health statistics
2. **Full Check Mode**:
   - Fetches all affiliate links from the database
   - Checks each link by making HEAD requests
   - Updates the `healthy` field in the `affiliate_links` table
   - Reports statistics on healthy vs unhealthy links

### Automated Scheduling

The health checker runs automatically every 6 hours via the background scheduler service.
You can view the scheduler status in the backend logs or through the admin API (if implemented).

### Requirements

- Backend server environment variables must be set (`.env` file in `backend/` directory)
- Database connection must be available
- Network access to check external affiliate links
