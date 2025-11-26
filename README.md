# Error Classification System

A full-stack ML-based system that automatically classifies error logs and maps them to their corresponding documentation files. The system uses custom TF-IDF and BM25 algorithms combined with adaptive feedback learning to improve accuracy over time.

## Architecture

- **Backend**: Python 3.13+ with Flask API and MVC architecture
- **Frontend**: React + Vite + Material-UI + TanStack Router/Query
- **Search Engine**: Hybrid Custom Search (TF-IDF + BM25 + Feedback Learning)
- **Database**: MongoDB for feedback storage and learning
- **Deployment**: Docker + Docker Compose for easy deployment

## Quick Start

### Using Docker (Recommended)

```bash
cd docker
docker-compose up -d --build
```

Access the application:
- **Frontend**: http://localhost
- **API**: http://localhost:3100/api/status

### Local Development

#### Backend Setup
```bash
cd core
pip install -r requirements.txt
python src/server.py
```

Backend runs at http://localhost:3100

#### Frontend Setup
```bash
cd ui
npm install
npm run dev
```

Frontend runs at http://localhost:3000

## How It Works

The system uses a **Hybrid Custom Search Engine** that combines:
- **TF-IDF**: Term frequency-inverse document frequency for content matching
- **BM25**: Probabilistic ranking algorithm for keyword relevance
- **Adaptive Feedback Learning**: Improves accuracy over time based on user corrections

The hybrid approach balances semantic understanding with keyword precision, while the feedback loop continuously learns from user input to boost confidence for known patterns.

## Web Interface

The React UI provides:
- **Search Page**: Classify errors using the Hybrid Custom search engine
- **Manage Docs**: CRUD operations for documentation files
- **Manage Dataset**: Edit training data records
- **Status Page**: System health and metrics (auto-refreshing)
- **Feedback System**: Thumbs up/down for continuous learning

## REST API

All endpoints available at `/api`:

**Classification**
- `POST /api/classify` - Classify error message
- `POST /api/teach-correction` - Teach system a correction

**Documentation**
- `GET /api/docs` - List all documentation files
- `GET /api/doc-content?path=...` - Get file content
- `POST /api/docs` - Create new doc
- `PUT /api/docs/:id` - Update doc
- `DELETE /api/docs/:id` - Delete doc

**Dataset**
- `GET /api/dataset` - List all records
- `POST /api/dataset` - Add record
- `PUT /api/dataset/:id` - Update record
- `DELETE /api/dataset/:id` - Delete record

**System**
- `GET /api/status` - System health with feedback statistics
- `GET /api/search-engines-comparison` - Detailed engine information

## CLI Usage

```bash
cd core
python src/server.py
```

The API server will:
- Initialize the Hybrid Custom search engine
- Load documentation and dataset
- Start Flask server on port 3100
- Enable feedback learning system

## Core Components

### Hybrid Custom Search Engine

Combines TF-IDF and BM25 algorithms for optimal search accuracy:

**Initialization:**
```python
from search_engines import HybridCustomSearchEngine

engine = HybridCustomSearchEngine(
    docs_root_dir="data/services",
    tfidf_weight=0.4,  # Weight for TF-IDF scores
    bm25_weight=0.6     # Weight for BM25 scores
)
```

**How It Works:**
1. **Dual Indexing**: Creates both TF-IDF and BM25 indexes for all documentation
2. **Hybrid Search**: Performs both searches in parallel and combines scores
3. **Feedback Learning**: Checks learned patterns first for known queries
4. **Score Fusion**: Normalizes and combines scores with configurable weights

**Example:**
```python
doc_path, confidence = engine.find_relevant_doc(
    "negative value detected in sensor"
)
# Returns: ("data/services/logitrack/NEGATIVE_VALUE.md", 87.5)

# Teach a correction
engine.teach_correction(
    "sensor glitch detected",
    "data/services/logitrack/SENSOR_ERROR.md"
)
```

### Adaptive Feedback Learning

The system continuously improves through user feedback:

- **Pattern Recognition**: Learns which documents work best for specific query patterns
- **Confidence Adjustment**: Boosts confidence for historically correct predictions
- **Fast Lookups**: Returns high-confidence results instantly for known patterns
- **Persistent Storage**: Saves learning to MongoDB for long-term improvement

**Mathematical Foundation:**
```
Success Rate (EMA) = α × is_correct + (1 - α) × previous_rate
Adjusted Confidence = base_confidence + (success_rate - 0.5) × boost_factor
```

## Data Format

### Training Data (`data/dataset/errors_dataset.csv`)
```csv
Service,Error_Category,Raw_Input_Snippet,Root_Cause
logitrack,NEGATIVE_VALUE,"weight: -5kg",Invalid sensor reading
meteo-il,MISSING_FIELD,"temperature field missing",Required field not provided
```

### Documentation Files (`data/services/`)
```
data/services/
├── logitrack/
│   ├── NEGATIVE_VALUE.md
│   └── SECURITY_ALERT.md
├── meteo-il/
│   ├── GEO_OUT_OF_BOUNDS.md
│   └── MISSING_FIELD.md
└── skyguard/
    ├── REGEX_MISMATCH.md
    └── SCHEMA_VALIDATION.md
```

## Configuration

### Environment Variables

Create `core/.env` file:

```bash
# API Configuration
API_PORT=3100

# MongoDB Configuration
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE=error_classifier
```

### File Paths

All file paths are automatically detected in `core/src/constants.py`:

```python
# Base directories (auto-detected from file location)
BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
CORE_DIR = dirname(dirname(abspath(__file__)))
DATA_DIR = join(BASE_DIR, 'data')

# Data paths
DOCS_ROOT_DIR = join(DATA_DIR, 'services')
DATASET_PATH = join(DATA_DIR, 'dataset', 'errors_dataset.csv')

# API configuration
API_PORT = int(getenv('API_PORT', 3100))

# MongoDB configuration
MONGODB_CONNECTION_STRING = getenv('MONGODB_CONNECTION_STRING', 'mongodb://localhost:27017/')
MONGODB_DATABASE = getenv('MONGODB_DATABASE', 'error_classifier')
```

No manual path configuration needed! Works in Docker and local environments.
