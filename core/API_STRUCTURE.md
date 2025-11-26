# Core API Structure

## Overview

Restructured API following MVC (Model-View-Controller) pattern for better organization and maintainability.

## Directory Structure

```
core/
├── src/
│   ├── api/                          # API Package
│   │   ├── __init__.py               # App factory
│   │   ├── services.py               # Search engine service
│   │   ├── controllers/              # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── classify_controller.py    # Classification logic
│   │   │   ├── docs_controller.py        # Documentation CRUD
│   │   │   ├── dataset_controller.py     # Dataset CRUD
│   │   │   └── status_controller.py      # Status & health
│   │   ├── routes/                   # HTTP endpoints
│   │   │   ├── __init__.py
│   │   │   ├── classify_routes.py        # /api/classify, /api/teach-correction
│   │   │   ├── docs_routes.py            # /api/docs/*
│   │   │   ├── dataset_routes.py         # /api/dataset/*
│   │   │   └── status_routes.py          # /api/status, /api/search-engines-comparison
│   │   └── middleware/               # Future middleware (auth, logging, etc.)
│   ├── custom_ml/                    # Custom ML implementations
│   ├── search_engines/               # Search engine implementations
│   ├── server.py                     # Main entry point
│   ├── constants.py                  # Configuration constants
│   └── (legacy api_server.py - deprecated)
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

## Architecture

### Layer Separation

1. **Routes Layer** (`api/routes/`)
   - HTTP request/response handling
   - Input validation
   - Blueprint registration
   - Minimal business logic

2. **Controllers Layer** (`api/controllers/`)
   - Business logic
   - Data transformation
   - Orchestration between services
   - Error handling

3. **Services Layer** (`api/services.py`)
   - Search engine initialization
   - Shared service instances
   - Resource management

4. **Models Layer** (`custom_ml/`, `search_engines/`)
   - ML algorithms
   - Search implementations
   - Data processing

### Request Flow

```
HTTP Request
    ↓
Routes (Flask Blueprint)
    ↓
Controller (Business Logic)
    ↓
Service (Search Engines)
    ↓
Custom ML / Search Engine
    ↓
Controller (Format Response)
    ↓
Routes (HTTP Response)
```

## API Endpoints

### Classification
- `POST /api/classify` - Classify an error
- `POST /api/teach-correction` - Teach a correction to the system

### Documentation
- `GET /api/docs` - Get all documentation files
- `GET /api/doc-content?path=...` - Get specific document content
- `POST /api/docs` - Create new documentation
- `PUT /api/docs/<id>` - Update documentation
- `DELETE /api/docs/<id>` - Delete documentation

### Dataset
- `GET /api/dataset` - Get all dataset records
- `POST /api/dataset` - Add new record
- `PUT /api/dataset/<id>` - Update record
- `DELETE /api/dataset/<id>` - Delete record

### Status
- `GET /api/status` - System health and statistics
- `GET /api/search-engines-comparison` - Compare search engines

## Running the Server

### Development
```bash
cd core
python src/server.py
```

### Docker
```bash
cd docker
docker-compose up --build
```

### Environment Variables
- `API_PORT` - API server port (default: 3100)
- `FLASK_ENV` - Flask environment (development/production)
- `PYTHONPATH` - Should include `/app/src` for imports

## Benefits of New Structure

### 1. **Separation of Concerns**
- Routes handle HTTP only
- Controllers contain business logic
- Services manage resources
- Clean boundaries between layers

### 2. **Testability**
- Easy to unit test controllers independently
- Mock services for testing
- Test routes without full server

### 3. **Maintainability**
- Find code quickly by responsibility
- Change one layer without affecting others
- Clear dependencies

### 4. **Scalability**
- Easy to add new endpoints
- Simple to add middleware
- Can split into microservices later

### 5. **Reusability**
- Controllers can be used by multiple routes
- Services shared across application
- No duplicate code

## Migration Notes

### From Old `api_server.py`

**Old (Monolithic)**:
```python
@app.route('/api/classify', methods=['POST'])
def classify_error():
    # 50+ lines of code here
    # Mixing HTTP, business logic, and ML calls
```

**New (Separated)**:
```python
# routes/classify_routes.py
@bp.route('/classify', methods=['POST'])
def classify_error():
    result = classify_controller.classify_single(...)
    return jsonify(result)

# controllers/classify_controller.py
def classify_single(error_message, method):
    engine = search_service.get_engine(method)
    return engine.find_relevant_doc(error_message)
```

### Key Changes
1. **Renamed**: `ml/` → `core/`
2. **New entry point**: `server.py` (replaces `api_server.py`)
3. **Blueprints**: Routes organized by feature
4. **Controllers**: Business logic extracted
5. **Services**: Shared engine management

## Adding New Features

### 1. Add New Route
```python
# routes/my_routes.py
from flask import Blueprint
bp = Blueprint('my_feature', __name__, url_prefix='/api')

@bp.route('/my-endpoint', methods=['POST'])
def my_endpoint():
    result = my_controller.do_something()
    return jsonify(result)
```

### 2. Register Blueprint
```python
# api/__init__.py
from .routes import my_routes
app.register_blueprint(my_routes.bp)
```

### 3. Add Controller
```python
# controllers/my_controller.py
def do_something():
    # Business logic here
    return result
```

## Testing

### Test Controllers
```python
from api.controllers import classify_controller

def test_classify_single():
    doc, conf, source, err = classify_controller.classify_single(
        "test error", "CUSTOM_TFIDF"
    )
    assert doc is not None
    assert conf > 0
```

### Test Routes
```python
from api import create_app

def test_classify_endpoint():
    app = create_app()
    client = app.test_client()
    
    response = client.post('/api/classify', json={
        'error_message': 'test error',
        'method': 'CUSTOM_TFIDF'
    })
    
    assert response.status_code == 200
```

## Future Enhancements

### Middleware
- Authentication/Authorization
- Request logging
- Rate limiting
- CORS configuration
- Error tracking

### Additional Layers
- **Repository Layer**: Database abstraction
- **Service Layer**: More granular services
- **DTO Layer**: Data transfer objects
- **Validation Layer**: Input validation schemas

### Monitoring
- Add health check endpoints
- Performance metrics
- Error reporting
- Request tracing

## Summary

The restructured API provides:
- ✅ Clear separation of concerns
- ✅ Better organization and maintainability
- ✅ Easier testing and debugging
- ✅ Scalable architecture
- ✅ Professional MVC pattern
- ✅ Ready for future enhancements

**All functionality preserved** - Just better organized!
