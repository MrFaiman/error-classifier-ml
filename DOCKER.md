# Docker Deployment Guide

## Quick Start

Build and run all services:
```bash
docker-compose up -d
```

Access the application:
- Frontend: http://localhost
- Backend API: http://localhost:5000/api/status

## Architecture

- **Backend**: Python Flask API with ML models (port 5000)
- **Frontend**: React + Vite with Nginx (port 80)
- **Network**: Custom bridge network for inter-service communication
- **Volume**: Persistent ChromaDB storage

## Commands

### Build and Start
```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop and Clean
```bash
# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes ChromaDB data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Development

#### Backend Only
```bash
docker-compose up backend
```

#### Frontend Only (requires backend running)
```bash
docker-compose up frontend
```

#### Rebuild Single Service
```bash
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

## Health Checks

Both services include health checks:
- Backend: Checks `/api/status` endpoint
- Frontend: Checks nginx is responding

View health status:
```bash
docker-compose ps
```

## Environment Variables

Backend (optional):
- `PYTHONUNBUFFERED=1`: Enable Python logging
- `FLASK_ENV=production`: Set Flask environment

## Volumes

- `./dataset`: Documentation and dataset files (mounted to backend)
- `./checkpoints`: ML model checkpoints (mounted to backend)
- `chroma_data`: ChromaDB persistent storage (Docker volume)

## Troubleshooting

### Backend not starting
```bash
docker-compose logs backend
```
Check for missing dependencies or file paths

### Frontend 502 Bad Gateway
Ensure backend is healthy:
```bash
docker-compose ps
curl http://localhost:5000/api/status
```

### Clear all data and restart
```bash
docker-compose down -v
docker-compose up -d --build
```

## Production Considerations

1. **Security**: 
   - Change default ports
   - Add SSL/TLS with reverse proxy (Traefik, Caddy)
   - Set proper CORS origins

2. **Scaling**:
   - Use `docker-compose up --scale backend=3` for multiple backend instances
   - Add load balancer (nginx, HAProxy)

3. **Monitoring**:
   - Add Prometheus + Grafana
   - Integrate logging (ELK stack)

4. **Backup**:
   - Backup `chroma_data` volume regularly
   - Backup `./dataset` and `./checkpoints` directories
