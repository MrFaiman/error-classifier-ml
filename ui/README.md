# Error Classifier UI

React-based web interface for the Error Classification System built with Vite, Material-UI, and TanStack Router/Query.

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Material-UI (MUI)** - Component library
- **TanStack Router** - Type-safe routing
- **TanStack Query** - Server state management
- **Axios** - HTTP client

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the Flask API server:
```bash
cd ../ml
python src/api_server.py
```

3. Start the Vite development server:
```bash
npm run dev
```

The app will open at `http://localhost:3000`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production (outputs to `dist/`)
- `npm run preview` - Preview production build locally

## Features

- **Search Page**: Classify errors using Vector DB, Semantic Search, or Random Forest methods
- **Manage Docs**: CRUD operations for documentation files with file preview
- **Manage Dataset**: Add, edit, and delete training data records
- **Status Page**: View system health and statistics (auto-refreshing every 5 seconds)
- **Feedback System**: Thumbs up/down with correction learning capability

## Architecture

### State Management
- **TanStack Query** for server state (caching, background refetching, optimistic updates)
- **React useState** for local UI state

### Routing
- **TanStack Router** for type-safe, file-based routing
- Routes defined in `src/routes.jsx`

### API Communication
All API calls centralized in `src/services/api.js`:
- Axios instance configured with `/api` base URL
- Proxy configured in `vite.config.js` for development

## API Endpoints

The React app communicates with the Flask API server at `http://localhost:5000`:

**Classification**
- `POST /api/classify` - Classify an error with specified method
- `POST /api/teach-correction` - Teach system a correction

**Documentation**
- `GET /api/docs` - List all documentation files
- `GET /api/doc-content?path=...` - Get file content for preview
- `POST /api/docs` - Create new documentation
- `PUT /api/docs/:id` - Update documentation
- `DELETE /api/docs/:id` - Delete documentation

**Dataset**
- `GET /api/dataset` - Get all dataset records
- `POST /api/dataset` - Add dataset record
- `PUT /api/dataset/:id` - Update dataset record
- `DELETE /api/dataset/:id` - Delete dataset record

**System**
- `POST /api/update-kb` - Update knowledge base
- `GET /api/status` - Get system status

## Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory and can be served with any static file server or containerized with the included Dockerfile.

## Docker Deployment

The UI includes a multi-stage Dockerfile:
1. **Builder stage**: Installs dependencies and builds the app
2. **Production stage**: Serves static files with Nginx

```bash
docker build -t error-classifier-ui .
docker run -p 80:80 error-classifier-ui
```

Or use the docker-compose setup from the project root:
```bash
cd ../docker
docker-compose up -d
```
