# Deployment Guide - Long-Running Sessions

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- OR Python 3.11+ with pip

### Option 1: Docker Deployment (Recommended)

```bash
# 1. Build the image
docker compose build

# 2. Start the service
docker compose up -d

# 3. Verify it's running
curl http://localhost:4041/health

# 4. Check logs
docker compose logs -f terminal-engine
```

### Option 2: Direct Python Deployment

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
uvicorn main:app --host 0.0.0.0 --port 4041 \
  --ws-ping-interval 30 \
  --ws-ping-timeout 300 \
  --timeout-keep-alive 300

# 3. Verify it's running
curl http://localhost:4041/health
```

---

## 📋 Pre-Deployment Checklist

### Configuration Verification
```bash
# Run verification script
python verify_config.py

# Expected output: ✅ ALL CONFIGURATION CHECKS PASSED!
```

### Files to Review
- [ ] `gunicorn_conf.py` - timeout=7200, keepalive=300
- [ ] `uvicorn_worker.py` - ws_ping_interval=30, ws_ping_timeout=300
- [ ] `main.py` - HEARTBEAT_INTERVAL_SECONDS=30, session TTL=7200
- [ ] `nginx-terminal.conf` - proxy timeouts=7200
- [ ] `session_manager.py` - idle_ttl_seconds=7200

### Environment Variables
```bash
# Optional: Set in docker-compose.yml or .env
LOG_LEVEL=WARNING          # Logging level
WEB_CONCURRENCY=4          # Number of workers
```

---

## 🔧 Deployment Steps

### Step 1: Backup Current Version (if upgrading)

```bash
# Backup configuration files
cp gunicorn_conf.py gunicorn_conf.py.backup
cp main.py main.py.backup
cp uvicorn_worker.py uvicorn_worker.py.backup
cp nginx-terminal.conf nginx-terminal.conf.backup
```

### Step 2: Deploy New Version

```bash
# Pull latest code
git pull origin main

# Or copy updated files
# - gunicorn_conf.py
# - main.py
# - uvicorn_worker.py
# - nginx-terminal.conf
# - session_manager.py
```

### Step 3: Verify Configuration

```bash
# Run verification
python verify_config.py

# Check for syntax errors
python -m py_compile main.py
python -m py_compile gunicorn_conf.py
python -m py_compile uvicorn_worker.py
python -m py_compile session_manager.py
```

### Step 4: Build & Deploy

#### Docker Deployment
```bash
# Stop current service
docker compose down

# Build new image
docker compose build

# Start service
docker compose up -d

# Verify startup
docker compose logs -f terminal-engine
```

#### Direct Deployment
```bash
# Stop current process
pkill -f uvicorn

# Start new process
uvicorn main:app --host 0.0.0.0 --port 4041 \
  --ws-ping-interval 30 \
  --ws-ping-timeout 300 \
  --timeout-keep-alive 300 &

# Or use gunicorn
gunicorn -c gunicorn_conf.py main:app &
```

### Step 5: Verify Deployment

```bash
# Check health endpoint
curl http://localhost:4041/health
# Expected: {"status":"ok","active_sessions":0}

# Test WebSocket connection
wscat -c ws://localhost:4041/terminal

# You should receive init message:
# {"type":"init","data":{"session_id":"...","prompt":"user@server:~$ "}}
```

### Step 6: Monitor

```bash
# Watch logs
docker compose logs -f terminal-engine

# Or for direct deployment
tail -f uvicorn.out.log

# Monitor active sessions
watch -n 5 'curl -s http://localhost:4041/health | jq'
```

---

## 🧪 Post-Deployment Testing

### Test 1: Basic Connection
```bash
# Connect with wscat
wscat -c ws://localhost:4041/terminal

# Send command
{"type":"command","data":"pwd"}

# Expected response
{"type":"response","data":{"output":"/home/user","prompt":"user@server:~$ "}}
```

### Test 2: Heartbeat Mechanism
```bash
# Connect and wait for ping
wscat -c ws://localhost:4041/terminal

# Server will send (after 30s):
{"type":"ping"}

# Respond with:
{"type":"pong"}

# Connection should stay alive
```

### Test 3: Long Session (Optional)
```bash
# Run long session test
python test_long_session.py

# Or manually keep connection alive for 10+ minutes
# Respond to pings and verify no disconnection
```

### Test 4: New Features
```bash
# Test grep -c
{"type":"command","data":"echo 'ERROR 1' > test.log"}
{"type":"command","data":"echo 'ERROR 2' >> test.log"}
{"type":"command","data":"grep -c 'ERROR' test.log"}
# Expected: 2

# Test nano
{"type":"command","data":"nano config.txt"}
# Expected: {"type":"nano","data":{...}}

# Test sudo
{"type":"command","data":"sudo mkdir admin"}
# Expected: success with [sudo] indicator
```

---

## 🔄 Rollback Procedure

If issues occur, rollback to previous version:

```bash
# Stop current service
docker compose down
# Or: pkill -f uvicorn

# Restore backup files
cp gunicorn_conf.py.backup gunicorn_conf.py
cp main.py.backup main.py
cp uvicorn_worker.py.backup uvicorn_worker.py
cp nginx-terminal.conf.backup nginx-terminal.conf

# Restart service
docker compose up -d
# Or: uvicorn main:app --host 0.0.0.0 --port 4041 &

# Verify rollback
curl http://localhost:4041/health
```

---

## 🌐 Nginx Configuration

If deploying behind Nginx, update your nginx config:

```nginx
location /terminal {
    proxy_pass http://localhost:4041;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Long-running session support (120 minutes)
    proxy_read_timeout 7200;
    proxy_send_timeout 7200;
    proxy_connect_timeout 300;
    
    # Disable buffering for WebSocket
    proxy_buffering off;
}
```

Then reload Nginx:
```bash
sudo nginx -t
sudo nginx -s reload
```

---

## 📊 Monitoring & Alerts

### Key Metrics to Monitor

1. **Active Sessions**
   ```bash
   curl http://localhost:4041/health | jq '.active_sessions'
   ```

2. **Connection Duration**
   - Track how long sessions stay connected
   - Alert if average duration < expected

3. **Heartbeat Success Rate**
   - Monitor ping/pong exchanges
   - Alert on timeout increases

4. **Memory Usage**
   ```bash
   docker stats terminal-engine
   ```

5. **CPU Usage**
   ```bash
   docker stats terminal-engine
   ```

### Recommended Alerts

- Active sessions > 1000 (capacity warning)
- Memory usage > 80% (resource warning)
- CPU usage > 80% (performance warning)
- Heartbeat timeout rate > 5% (connection issue)
- Average session duration < 60 minutes (unexpected disconnects)

---

## 🔍 Troubleshooting

### Issue: Service Won't Start

**Check logs:**
```bash
docker compose logs terminal-engine
```

**Common causes:**
- Port 4041 already in use
- Configuration syntax error
- Missing dependencies

**Solution:**
```bash
# Check port
lsof -i :4041

# Verify config
python -m py_compile main.py

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: WebSocket Connection Fails

**Check:**
1. Service is running: `curl http://localhost:4041/health`
2. Firewall allows port 4041
3. WebSocket upgrade headers present

**Solution:**
```bash
# Test with wscat
wscat -c ws://localhost:4041/terminal

# Check nginx config if behind proxy
sudo nginx -t
```

### Issue: Session Disconnects Before 120 Minutes

**Check:**
1. Client responding to pings
2. Nginx timeout settings
3. Load balancer timeout settings

**Solution:**
```bash
# Verify configuration
python verify_config.py

# Check nginx timeouts
grep timeout /etc/nginx/sites-enabled/default

# Update if needed
proxy_read_timeout 7200;
proxy_send_timeout 7200;
```

### Issue: High Memory Usage

**Check:**
```bash
# View active sessions
curl http://localhost:4041/health

# Check Docker stats
docker stats terminal-engine
```

**Solution:**
- Reduce session TTL if too many idle sessions
- Increase cleanup frequency
- Add session limits per user

---

## 🔒 Security Considerations

### Production Checklist

- [ ] Use WSS (secure WebSocket) in production
- [ ] Implement authentication/authorization
- [ ] Add rate limiting
- [ ] Set up firewall rules
- [ ] Enable HTTPS for health endpoint
- [ ] Implement session token validation
- [ ] Add IP whitelisting if needed
- [ ] Monitor for suspicious activity
- [ ] Regular security updates
- [ ] Backup session data if needed

### Recommended Settings

```python
# Add to main.py for production
from fastapi import WebSocket, HTTPException
from fastapi.security import HTTPBearer

# Implement authentication
security = HTTPBearer()

@app.websocket("/terminal")
async def terminal(websocket: WebSocket, token: str = None):
    # Validate token
    if not validate_token(token):
        await websocket.close(code=1008, reason="Unauthorized")
        return
    # ... rest of code
```

---

## 📈 Scaling

### Horizontal Scaling

For multiple instances:

1. **Use Redis for session storage**
   ```python
   # Replace in-memory sessions with Redis
   import redis
   redis_client = redis.Redis(host='redis', port=6379)
   ```

2. **Configure sticky sessions**
   ```nginx
   upstream terminal_backend {
       ip_hash;  # Sticky sessions
       server terminal-1:4041;
       server terminal-2:4041;
   }
   ```

3. **Update docker-compose.yml**
   ```yaml
   services:
     terminal-engine:
       deploy:
         replicas: 3
   ```

### Vertical Scaling

Increase resources:
```yaml
services:
  terminal-engine:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Configuration verified
- [ ] Tests passing
- [ ] Documentation reviewed
- [ ] Backup created
- [ ] Team notified

### Deployment
- [ ] Service stopped
- [ ] Files updated
- [ ] Configuration verified
- [ ] Service started
- [ ] Health check passed

### Post-Deployment
- [ ] WebSocket connection tested
- [ ] Heartbeat mechanism verified
- [ ] Long session tested (optional)
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Team notified
- [ ] Documentation updated

---

## 📞 Support

### Getting Help

1. Check logs: `docker compose logs -f`
2. Review documentation: `LONG_RUNNING_SESSIONS.md`
3. Run verification: `python verify_config.py`
4. Test configuration: `python test_long_session.py`

### Common Commands

```bash
# Restart service
docker compose restart terminal-engine

# View logs
docker compose logs -f terminal-engine

# Check health
curl http://localhost:4041/health

# Connect to terminal
wscat -c ws://localhost:4041/terminal

# Monitor sessions
watch -n 5 'curl -s http://localhost:4041/health | jq'
```

---

**Deployment Status**: ✅ Ready  
**Last Updated**: May 4, 2026  
**Version**: 2.0
