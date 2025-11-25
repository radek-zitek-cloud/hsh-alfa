# Deployment Guide

## Overview

This guide covers deploying Home Sweet Home to production environments. The application is containerized with Docker and designed for easy deployment on any server with Docker support.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Production Deployment](#production-deployment)
- [Traefik Integration](#traefik-integration)
- [Security Hardening](#security-hardening)
- [Environment Variables](#environment-variables)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup Strategy](#backup-strategy)
- [Scaling Considerations](#scaling-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum**:
- **CPU**: 1 core
- **RAM**: 1 GB
- **Disk**: 10 GB
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, or similar)

**Recommended**:
- **CPU**: 2 cores
- **RAM**: 2 GB
- **Disk**: 20 GB (for backups and logs)
- **OS**: Ubuntu 22.04 LTS

### Software Requirements

- Docker 24.0+
- Docker Compose 2.0+
- Git
- (Optional) Traefik 2.0+ for reverse proxy
- (Optional) Nginx for additional reverse proxy

### Installation

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Add user to docker group (optional, for non-root usage)
sudo usermod -aG docker $USER
newgrp docker
```

## Deployment Options

### 1. Standalone Docker Compose

Simple deployment without reverse proxy.

**Best for**: Development, testing, local networks

**Setup**:
```bash
cd /opt/home-sweet-home
docker-compose up -d
```

**Access**:
- Frontend: `http://server-ip:8080`
- Backend: `http://server-ip:8000`

---

### 2. Docker Compose with Traefik

Production deployment with automatic HTTPS.

**Best for**: Production, self-hosted with domain name

**Setup**:
- Configure Traefik (see [Traefik Integration](#traefik-integration))
- Deploy with docker-compose
- Traefik handles SSL, routing, and load balancing

**Access**:
- Frontend: `https://home.yourdomain.com`
- Backend: `https://home.yourdomain.com/api`

---

### 3. Kubernetes (Advanced)

Enterprise-grade deployment with orchestration.

**Best for**: Large-scale deployments, high availability

**Setup**: See separate Kubernetes deployment guide (future)

---

## Production Deployment

### Step-by-Step Production Setup

#### 1. Server Preparation

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y git curl wget ufw fail2ban

# Configure firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable

# Install Fail2ban for security
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

#### 2. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/home-sweet-home
sudo chown $USER:$USER /opt/home-sweet-home

# Clone repository
cd /opt/home-sweet-home
git clone https://github.com/your-username/hsh-alfa.git .
```

#### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secure SECRET_KEY
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# Edit environment file
nano .env
```

**Required variables**:
```bash
# Security
SECRET_KEY=your-generated-secret-key-here  # 32+ characters
ENVIRONMENT=production

# Domain
DOMAIN=home.yourdomain.com

# Database (defaults are fine for SQLite)
DATABASE_URL=sqlite+aiosqlite:///data/home.db

# Redis (optional, for caching)
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://home.yourdomain.com/api/auth/google/callback

# Widget API Keys
WEATHER_API_KEY=your-openweathermap-api-key
EXCHANGE_RATE_API_KEY=your-exchange-rate-api-key  # Optional
NEWS_API_KEY=your-news-api-key  # Optional

# CORS (comma-separated origins)
CORS_ORIGINS=https://home.yourdomain.com

# Logging
LOG_LEVEL=INFO
```

#### 4. Create Data Directory

```bash
# Create data directory
mkdir -p data

# Set proper permissions (UID 1000 is the container user)
sudo chown -R 1000:1000 data
chmod 755 data
```

#### 5. Pull and Start Services

```bash
# Pull latest images
docker compose pull

# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

#### 6. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}

# Check frontend (if exposed)
curl http://localhost:8080
```

#### 7. Access Application

Open browser and navigate to:
- **With Traefik**: `https://home.yourdomain.com`
- **Without Traefik**: `http://server-ip:8080`

---

## Traefik Integration

### Prerequisites

Traefik 2.0+ running with Docker provider enabled.

### Traefik Network

Create external network for Traefik:

```bash
docker network create proxy
```

**IMPORTANT**: Always use `proxy` as the network name for consistency.

### Traefik Configuration

Ensure Traefik is configured to:
1. Listen on ports 80 (HTTP) and 443 (HTTPS)
2. Enable Docker provider
3. Have Let's Encrypt configured (for HTTPS)

Example `traefik.yml`:
```yaml
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https

  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: proxy

certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@example.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web
```

### Application Labels

The `docker-compose.yml` includes Traefik labels:

```yaml
services:
  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.home-frontend.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.home-frontend.entrypoints=websecure"
      - "traefik.http.routers.home-frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.home-frontend.loadbalancer.server.port=80"

  backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.home-backend.rule=Host(`${DOMAIN}`) && PathPrefix(`/api`)"
      - "traefik.http.routers.home-backend.entrypoints=websecure"
      - "traefik.http.routers.home-backend.tls.certresolver=letsencrypt"
      - "traefik.http.services.home-backend.loadbalancer.server.port=8000"
```

### DNS Configuration

Point your domain to your server's IP:

```
A     home.yourdomain.com     →     123.456.789.0
```

Or use a CNAME if deploying on a subdomain:

```
CNAME home.yourdomain.com     →     your-server.com
```

### Verify Traefik Integration

```bash
# Check if containers are connected to proxy network
docker network inspect proxy

# Check Traefik logs
docker logs traefik

# Test HTTPS connection
curl https://home.yourdomain.com/health
```

---

## Security Hardening

### 1. SECRET_KEY Security

```bash
# Generate cryptographically secure key
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'

# Never commit .env to version control
echo ".env" >> .gitignore
```

### 2. File Permissions

```bash
# Restrict .env file access
chmod 600 .env

# Database directory permissions
sudo chown -R 1000:1000 data
chmod 755 data
chmod 644 data/home.db
```

### 3. Firewall Configuration

```bash
# Only allow necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 4. SSH Hardening

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config

# Set:
PermitRootLogin no
PasswordAuthentication no  # Use key-based auth only
PubkeyAuthentication yes

# Restart SSH
sudo systemctl restart sshd
```

### 5. Docker Security

```bash
# Run containers as non-root (already configured in Dockerfile)
# Backend runs as UID 1000

# Limit container resources
# Add to docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### 6. HTTPS Enforcement

Traefik automatically redirects HTTP to HTTPS. For standalone deployments:

```nginx
# Add to nginx.conf
server {
    listen 80;
    server_name home.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 7. Security Headers

Add to frontend `nginx.conf`:

```nginx
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 8. Rate Limiting

Backend already includes rate limiting. Verify in logs:

```bash
docker compose logs backend | grep "rate limit"
```

### 9. Regular Updates

```bash
# Update Docker images
docker compose pull
docker compose up -d

# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update application
cd /opt/home-sweet-home
git pull
docker compose up -d --build
```

### 10. Secrets Management

For production, consider using Docker secrets or environment variable vaults:

```yaml
# docker-compose.yml
services:
  backend:
    secrets:
      - secret_key
      - google_client_secret

secrets:
  secret_key:
    file: ./secrets/secret_key.txt
  google_client_secret:
    file: ./secrets/google_client_secret.txt
```

---

## Environment Variables

### Production Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | - | JWT signing key (32+ chars) |
| `ENVIRONMENT` | ❌ | `development` | Environment mode |
| `DOMAIN` | ✅ | - | Your domain name |
| `DATABASE_URL` | ❌ | `sqlite+aiosqlite:///data/home.db` | Database connection URL |
| `REDIS_ENABLED` | ❌ | `false` | Enable Redis caching |
| `REDIS_URL` | ❌ | `redis://redis:6379/0` | Redis connection URL |
| `GOOGLE_CLIENT_ID` | ✅ | - | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ✅ | - | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | ✅ | - | OAuth callback URL |
| `WEATHER_API_KEY` | ❌ | - | OpenWeatherMap API key |
| `EXCHANGE_RATE_API_KEY` | ❌ | - | Exchange rate API key |
| `NEWS_API_KEY` | ❌ | - | News API key |
| `CORS_ORIGINS` | ✅ | - | Allowed CORS origins (comma-separated) |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `BACKEND_PORT` | ❌ | `8000` | Backend port |
| `FRONTEND_PORT` | ❌ | `80` | Frontend port (inside container) |

### Validation

The application validates critical environment variables on startup:

```python
# Enforced by backend/app/config.py
- SECRET_KEY must be 32+ characters
- SECRET_KEY cannot be a placeholder value
- GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET required for auth
```

---

## SSL/TLS Configuration

### Let's Encrypt with Traefik (Recommended)

Traefik handles SSL automatically:

1. **Automatic**: Traefik requests certificates from Let's Encrypt
2. **Renewal**: Certificates auto-renew before expiration
3. **ACME Challenge**: HTTP-01 challenge (requires port 80 open)

**No manual configuration needed** if Traefik is set up correctly.

### Manual SSL Certificate

For standalone deployments without Traefik:

#### 1. Generate Certificate with Certbot

```bash
# Install Certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d home.yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/home.yourdomain.com/
```

#### 2. Configure Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name home.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/home.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/home.yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Your location blocks...
}
```

#### 3. Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job for auto-renewal
sudo crontab -e

# Add:
0 3 * * * certbot renew --quiet --post-hook "docker compose restart nginx"
```

---

## Monitoring and Logging

### Application Logs

#### View Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs frontend

# Follow logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100
```

#### Log Locations

Logs are written to:
- **Backend**: stdout/stderr (captured by Docker)
- **Frontend**: Nginx access/error logs
- **Database**: SQLite doesn't have separate logs

#### Structured Logging

Backend uses JSON structured logging:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "app.api.bookmarks",
  "message": "Bookmark created",
  "user_id": 1,
  "bookmark_id": 42
}
```

### Log Management

#### Logrotate Configuration

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/docker-compose

# Add:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
```

#### Centralized Logging (Optional)

For production, consider:
- **Loki + Grafana**: Log aggregation and visualization
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Papertrail**: Cloud-based log management

Example with Loki:

```yaml
# docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
```

### Monitoring

#### Health Checks

```bash
# Check application health
curl https://home.yourdomain.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### Docker Health Checks

Already configured in `docker-compose.yml`:

```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

#### Monitoring Tools

**Recommended**:
- **Uptime Kuma**: Self-hosted uptime monitoring
- **Prometheus + Grafana**: Metrics and dashboards
- **Netdata**: Real-time performance monitoring

Example Uptime Kuma:

```bash
docker run -d \
  --name uptime-kuma \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:1
```

### Alerts

Set up alerts for:
- **Downtime**: Application not responding
- **High CPU/Memory**: Resource exhaustion
- **Disk Space**: Running out of storage
- **Failed Logins**: Potential security issue
- **Error Rate**: Spike in errors

---

## Backup Strategy

### What to Backup

1. **Database**: `/data/home.db`
2. **Configuration**: `.env` file
3. **User uploads**: (if applicable)

### Automated Backup Script

```bash
#!/bin/bash
# /opt/home-sweet-home/backup.sh

BACKUP_DIR="/opt/backups/home-sweet-home"
APP_DIR="/opt/home-sweet-home"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
cp "$APP_DIR/data/home.db" "$BACKUP_DIR/home_${TIMESTAMP}.db"

# Backup environment (without secrets for security)
grep -v "SECRET\|KEY\|PASSWORD" "$APP_DIR/.env" > "$BACKUP_DIR/env_${TIMESTAMP}.txt"

# Compress backup
tar -czf "$BACKUP_DIR/backup_${TIMESTAMP}.tar.gz" \
    "$BACKUP_DIR/home_${TIMESTAMP}.db" \
    "$BACKUP_DIR/env_${TIMESTAMP}.txt"

# Remove uncompressed files
rm "$BACKUP_DIR/home_${TIMESTAMP}.db" "$BACKUP_DIR/env_${TIMESTAMP}.txt"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: backup_${TIMESTAMP}.tar.gz"
```

### Schedule Backups

```bash
# Make script executable
chmod +x /opt/home-sweet-home/backup.sh

# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/home-sweet-home/backup.sh >> /var/log/hsh-backup.log 2>&1
```

### Offsite Backup

Sync backups to remote storage:

```bash
# Using rsync
rsync -avz /opt/backups/home-sweet-home/ user@remote:/backups/hsh/

# Using rclone (for cloud storage)
rclone sync /opt/backups/home-sweet-home/ remote:hsh-backups/
```

### Restore from Backup

```bash
# Stop application
cd /opt/home-sweet-home
docker compose down

# Extract backup
tar -xzf /opt/backups/home-sweet-home/backup_20250115_020000.tar.gz -C /tmp

# Restore database
cp /tmp/home_20250115_020000.db /opt/home-sweet-home/data/home.db

# Fix permissions
sudo chown 1000:1000 /opt/home-sweet-home/data/home.db

# Start application
docker compose up -d
```

---

## Scaling Considerations

### Vertical Scaling

Increase server resources:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### Horizontal Scaling

For multiple instances:

1. **Database**: Migrate from SQLite to PostgreSQL
2. **Session Storage**: Use Redis for sessions
3. **Load Balancer**: Traefik or Nginx
4. **Container Orchestration**: Docker Swarm or Kubernetes

Example PostgreSQL migration:

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: homedb
      POSTGRES_USER: homeuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data

  backend:
    environment:
      DATABASE_URL: postgresql+asyncpg://homeuser:${DB_PASSWORD}@postgres:5432/homedb
    depends_on:
      - postgres

volumes:
  postgres-data:
```

### Caching

Enable Redis for improved performance:

```bash
# In .env
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0
```

Redis caches:
- Widget data
- API responses
- Session data (future)

### CDN Integration

For static assets:
- Serve frontend assets via CDN (Cloudflare, AWS CloudFront)
- Configure `Cache-Control` headers in Nginx

---

## Troubleshooting

### Common Deployment Issues

#### Container Won't Start

**Check logs**:
```bash
docker compose logs backend
```

**Common causes**:
- Missing environment variables
- Database permission issues
- Port conflicts

#### Database Permission Error

```bash
# Error: attempt to write a readonly database
sudo chown -R 1000:1000 data
chmod 755 data
```

#### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000

# Kill process or change port in docker-compose.yml
```

#### Traefik Not Routing

**Check**:
1. Traefik is running: `docker ps | grep traefik`
2. Proxy network exists: `docker network ls | grep proxy`
3. DNS points to server: `dig home.yourdomain.com`
4. Containers on proxy network: `docker network inspect proxy`

#### SSL Certificate Issues

```bash
# Check Traefik logs
docker logs traefik | grep acme

# Verify port 80 is accessible for ACME challenge
curl http://yourdomain.com/.well-known/acme-challenge/test
```

#### Memory Issues

```bash
# Check container stats
docker stats

# Increase container memory limit
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 1G
```

### Performance Issues

#### Slow Response Times

1. **Enable Redis caching**: Set `REDIS_ENABLED=true`
2. **Check database size**: `du -h data/home.db`
3. **Run VACUUM**: `sqlite3 data/home.db "VACUUM;"`
4. **Optimize queries**: Check slow query logs

#### High CPU Usage

```bash
# Identify process
docker stats

# Check backend logs for errors
docker compose logs backend --tail=100
```

### Maintenance

#### Update Application

```bash
cd /opt/home-sweet-home

# Pull latest code
git pull

# Rebuild containers
docker compose build

# Restart with new images
docker compose up -d

# Verify
docker compose ps
curl https://home.yourdomain.com/health
```

#### Database Maintenance

```bash
# Vacuum database (reclaim space)
docker compose exec backend python -c "
import sqlite3
conn = sqlite3.connect('/data/home.db')
conn.execute('VACUUM;')
conn.close()
"

# Check integrity
docker compose exec backend python -c "
import sqlite3
conn = sqlite3.connect('/data/home.db')
result = conn.execute('PRAGMA integrity_check;').fetchone()
print(result[0])
conn.close()
"
```

---

## Production Checklist

Before going live:

- [ ] Generated secure `SECRET_KEY` (32+ characters)
- [ ] Configured Google OAuth credentials
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Configured `CORS_ORIGINS` for your domain
- [ ] Database directory permissions set (UID 1000)
- [ ] SSL/TLS configured (via Traefik or manually)
- [ ] Firewall configured (UFW or iptables)
- [ ] SSH hardened (key-based auth only)
- [ ] Fail2ban installed and configured
- [ ] Automated backups scheduled
- [ ] Monitoring/alerting set up
- [ ] Health check endpoint verified
- [ ] DNS records configured
- [ ] Log rotation configured
- [ ] Docker resource limits set
- [ ] Security headers configured in Nginx
- [ ] Rate limiting verified
- [ ] Tested restore from backup
- [ ] Documentation reviewed and updated

---

## Support

For deployment issues:

1. Check logs: `docker compose logs`
2. Review this documentation
3. Check [Troubleshooting](#troubleshooting) section
4. Open an issue on GitHub with:
   - Deployment method (Traefik / standalone)
   - Error messages from logs
   - Docker compose configuration (sanitized)
   - Steps to reproduce
