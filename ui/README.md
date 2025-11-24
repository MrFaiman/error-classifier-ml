# Error Classifier UI

React-based web interface for the Error Classification System.

## Setup

1. Install dependencies:
```bash
cd ui
npm install
```

2. Start the Flask API server (from parent directory):
```bash
cd ..
python api_server.py
```

3. Start the React development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Features

- **Search Page**: Classify errors using Vector DB, Semantic Search, or Random Forest
- **Manage Docs**: Add, edit, and delete documentation files
- **Manage Dataset**: Add, edit, and delete training data records
- **Status Page**: View system health and statistics

## API Endpoints

The React app communicates with the Flask API server at `http://localhost:5000`:

- `POST /api/classify` - Classify an error
- `GET /api/docs` - Get all documentation files
- `POST /api/docs` - Create new documentation
- `PUT /api/docs/:id` - Update documentation
- `DELETE /api/docs/:id` - Delete documentation
- `GET /api/dataset` - Get all dataset records
- `POST /api/dataset` - Add dataset record
- `PUT /api/dataset/:id` - Update dataset record
- `DELETE /api/dataset/:id` - Delete dataset record
- `POST /api/update-kb` - Update knowledge base
- `GET /api/status` - Get system status

## Build for Production

```bash
npm run build
```

The production build will be in the `build/` directory.
