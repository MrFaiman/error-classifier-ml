# Docker Deployment Guide

This directory contains Docker configuration for running the error classifier ML system.

## Architecture

The system consists of three services:
- **Redis**: Cache layer for classification results
- **Backend**: Python Flask API (port 3100)
- **Frontend**: React UI served by Nginx (port 80)

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- MongoDB running on host machine (optional, for feedback loop)

## Quick Start

From this directory:

```bash
docker-compose up -d
```

Access the application:
- Frontend: http://localhost
- Backend API: http://localhost:3100/api

## Services Overview

### Redis
- **Image**: redis:7-alpine
- **Port**: 6379
- **Purpose**: Caches classification results to improve performance
- **Persistence**: Volume-mounted data directory

### Backend
- **Build**: ../core/Dockerfile
- **Port**: 3100
- **Language**: Python 3.13
- **Dependencies**: Managed by uv + pyproject.toml
- **Volumes**:
  - `../data:/app/data` - Documentation and dataset
  - `../core/models:/app/models` - ML models and ChromaDB

### Frontend
- **Build**: ../ui/Dockerfile
- **Port**: 80
- **Framework**: React with Vite
- **Server**: Nginx
- **Proxies**: API requests to backend:3100

## Environment Variables

### Backend Configuration
Set in `docker-compose.yml` or create a `.env` file:

```bash
# Redis
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_ENABLED=true
REDIS_CACHE_TTL=3600

# MongoDB (optional, for feedback loop)
MONGODB_CONNECTION_STRING=mongodb://host.docker.internal:27017/

# Flask
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

## Data Volumes

The following host directories are mounted:
- `../data` → Backend data directory (documentation, datasets)
- `../core/models` → ML models and ChromaDB storage

Ensure these directories exist and have proper permissions before starting.

## Common Operations

### Start all services
```bash
docker-compose up -d
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f redis
```

### Stop services
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Check service health
```bash
docker-compose ps
```

### Access service shells
```bash
# Backend
docker-compose exec backend bash

# Redis CLI
docker-compose exec redis redis-cli
```

## Troubleshooting

### Backend fails to start
1. Check logs: `docker-compose logs backend`
2. Verify data volumes exist: `ls -la ../data ../core/models`
3. Ensure MongoDB is accessible if using feedback loop
4. Check Python dependencies in `../core/pyproject.toml`

### Frontend can't reach backend
1. Verify backend is running: `curl http://localhost:3100/api/status`
2. Check nginx config in `../ui/nginx.conf`
3. Verify backend service name in docker-compose network

### Redis connection issues
1. Check Redis health: `docker-compose exec redis redis-cli ping`
2. Verify REDIS_URL in backend environment
3. Check Redis logs: `docker-compose logs redis`

### Port conflicts
If ports 80 or 3100 are already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "8080:80"  # Frontend on port 8080
  - "3200:3100"  # Backend on port 3200
```

## Development Mode

For development with hot-reload:

1. **Backend**: Run outside Docker with `uv run python src/server.py`
2. **Frontend**: Run outside Docker with `npm run dev`
3. **Redis only**: `docker-compose up -d redis`

This allows faster iteration without rebuilding containers.

## Production Considerations

### Security
- [ ] Use Docker secrets for sensitive credentials
- [ ] Set up proper firewall rules
- [ ] Use HTTPS with SSL certificates
- [ ] Restrict Redis port exposure
- [ ] Set up MongoDB authentication

### Performance
- [ ] Adjust Redis memory limits
- [ ] Configure backend worker processes
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Use production-grade reverse proxy (Traefik, Caddy)

### Scaling
- [ ] Use orchestration (Kubernetes, Docker Swarm)
- [ ] Configure multiple backend replicas
- [ ] Set up load balancing
- [ ] Use managed Redis (AWS ElastiCache, etc.)

## Network

All services communicate on the `error-classifier-network` bridge network.

Service DNS names within the network:
- `redis` - Redis service
- `backend` - Backend API service
- `frontend` - Frontend service

## Health Checks

All services include health checks:
- **Redis**: `redis-cli ping`
- **Backend**: `GET /api/status` (30s interval)
- **Frontend**: HTTP check on port 80 (30s interval)

Use `docker-compose ps` to view health status.
