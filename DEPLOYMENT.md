# Transmission Middleware - Deployment Guide

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### 1. Clone Repository
```bash
git clone https://github.com/ChrisCryptoBot/Transmission-Middleware.git
cd Transmission-Middleware
```

### 2. Configure API Keys
Edit `config/user_default_user/kraken_config.yaml`:
```yaml
broker:
  type: "kraken"
  api_key: "YOUR_KRAKEN_API_KEY"
  private_key: "YOUR_KRAKEN_PRIVATE_KEY"
  sandbox: true  # Set to false for live trading
```

### 3. Start Services
```bash
docker-compose up -d
```

This starts:
- **API** on `http://localhost:8000`
- **Web Dashboard** on `http://localhost:80`

### 4. Access Dashboard
Open browser: `http://localhost`

Default API key will be printed in API logs:
```bash
docker logs transmission-api | grep "Default API key"
```

### 5. Submit First Signal
1. Navigate to Dashboard
2. Paste API key
3. Fill manual signal form:
   - Symbol: `BTC/USD:USD`
   - Direction: LONG
   - Entry: 45000
   - Stop: 44500
   - Target: 46000
4. Submit!

---

## Docker Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# API only
docker logs -f transmission-api

# Web only
docker logs -f transmission-web
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Clean Up (Remove Volumes)
```bash
docker-compose down -v
```

---

## Manual Deployment (Without Docker)

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm 9+

### Backend Setup

1. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Broker**
Edit `config/user_default_user/kraken_config.yaml`

3. **Start API Server**
```bash
python startup/run_api.py
```

API runs on `http://localhost:8000`

### Frontend Setup

1. **Install Node Dependencies**
```bash
cd web
npm install
```

2. **Start Development Server**
```bash
npm run dev
```

Frontend runs on `http://localhost:5173`

3. **Build for Production**
```bash
npm run build
npm run preview
```

---

## Production Deployment

### Recommended: Railway.app

1. **Create Railway Project**
```bash
railway init
```

2. **Deploy API**
```bash
railway up
```

3. **Set Environment Variables**
```bash
railway variables set DATABASE_URL=postgresql://...
railway variables set KRAKEN_API_KEY=your_key
railway variables set KRAKEN_PRIVATE_KEY=your_private_key
```

4. **Deploy Frontend to Vercel**
```bash
cd web
vercel deploy --prod
```

### Alternative: AWS/GCP/Azure

Use Docker Compose on cloud VM:
```bash
# On cloud VM
git clone repo
cd Transmission-Middleware
docker-compose up -d
```

Configure firewall:
- Port 80 (Web)
- Port 8000 (API)
- Port 443 (HTTPS via reverse proxy)

---

## Environment Variables

### API (Backend)
```bash
DATABASE_URL=sqlite:////app/data/transmission.db  # Or PostgreSQL
LOG_LEVEL=INFO
KRAKEN_API_KEY=your_key
KRAKEN_PRIVATE_KEY=your_private_key
KRAKEN_SANDBOX=true  # false for live trading
```

### Web (Frontend)
```bash
VITE_API_URL=http://localhost:8000  # Or production API URL
```

---

## Health Checks

### API Health
```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "database": "connected",
  "orchestrator": "ready"
}
```

### Web Health
```bash
curl http://localhost/
```

Should return HTML.

---

## Monitoring

### Docker Stats
```bash
docker stats transmission-api transmission-web
```

### API Logs
```bash
docker logs -f transmission-api | grep ERROR
```

### Database Size
```bash
du -sh data/transmission.db
```

---

## Troubleshooting

### API Won't Start
1. Check logs: `docker logs transmission-api`
2. Verify database permissions: `ls -la data/`
3. Test broker connection: Check Kraken API keys

### Web Can't Connect to API
1. Check API health: `curl http://localhost:8000/health`
2. Verify nginx config: `docker exec transmission-web cat /etc/nginx/conf.d/default.conf`
3. Check network: `docker network inspect transmission-network`

### Database Locked
```bash
docker-compose down
rm data/transmission.db-shm data/transmission.db-wal
docker-compose up -d
```

### Out of Memory
```bash
docker-compose down
docker system prune -a
docker-compose up -d
```

---

## Backup & Restore

### Backup Database
```bash
docker exec transmission-api sqlite3 /app/data/transmission.db ".backup /app/data/backup.db"
docker cp transmission-api:/app/data/backup.db ./backup_$(date +%Y%m%d).db
```

### Restore Database
```bash
docker cp backup_20240101.db transmission-api:/app/data/transmission.db
docker-compose restart api
```

---

## Scaling

### Horizontal Scaling (Multiple API Instances)
```bash
docker-compose up -d --scale api=3
```

Add load balancer (nginx/traefik) in front.

### Vertical Scaling (More Resources)
Edit `docker-compose.yml`:
```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
```

---

## Security

### Production Checklist
- [ ] Change default API keys
- [ ] Enable HTTPS (Let's Encrypt)
- [ ] Set `KRAKEN_SANDBOX=false` only when ready
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Regular backups
- [ ] Monitor logs for anomalies

### HTTPS Setup with Caddy
```bash
# Install Caddy
docker run -d -p 443:443 -p 80:80 \
  --name caddy \
  -v caddy_data:/data \
  -v $(pwd)/Caddyfile:/etc/caddy/Caddyfile \
  caddy:latest
```

Caddyfile:
```
your-domain.com {
    reverse_proxy web:80
}

api.your-domain.com {
    reverse_proxy api:8000
}
```

---

## Support

- **Issues**: https://github.com/ChrisCryptoBot/Transmission-Middleware/issues
- **Docs**: https://docs.claude.com/transmission
- **Community**: Discord (link in README)

Happy trading! 🚀
