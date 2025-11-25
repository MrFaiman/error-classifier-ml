# Error Classification System

A full-stack ML-based system that automatically classifies error logs and maps them to their corresponding documentation files using Natural Language Processing. Features three advanced classification methods with feedback learning, automatic GPU acceleration, a Flask REST API, and a modern React web interface.

## Architecture

- **Backend**: Python 3.13+ with UV package manager, Flask API with three search engines
- **Frontend**: React + Vite + Material-UI + TanStack Router/Query
- **Database**: ChromaDB for persistent vector storage + FAISS for in-memory search
- **Deployment**: Docker + Docker Compose for easy deployment
- **GPU Acceleration**: Automatic detection of Apple Silicon (MPS), NVIDIA CUDA, or CPU fallback

## Quick Start

### Using Docker (Recommended)

```bash
cd docker
docker-compose up -d --build
```

Access the application:
- **Frontend**: http://localhost
- **API**: http://localhost:5000/api/status

See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

### Local Development

#### Backend Setup
```bash
cd ml
pip install -r requirements.txt
python src/api_server.py
```

Backend runs at http://localhost:5000

#### Frontend Setup
```bash
cd ui
npm install
npm run dev
```

Frontend runs at http://localhost:3000

## Classification Methods

The system provides three methods for matching error logs to documentation:

1. **Vector Database (ChromaDB)**: Persistent vector store with dual collections (official docs + learned feedback)
2. **Semantic Search (LangChain + FAISS)**: Document chunking with in-memory FAISS vector search for fast semantic similarity
3. **Hybrid Search (BM25 + Semantic)**: Combines keyword-based BM25 with semantic embeddings using weighted score fusion

All three engines support feedback learning - the system improves accuracy over time as users correct misclassifications.

## Web Interface

The React UI provides:
- **Search Page**: Classify errors with any of the three methods
- **Manage Docs**: CRUD operations for documentation files
- **Manage Dataset**: Edit training data records
- **Status Page**: System health and metrics (auto-refreshing)
- **Feedback System**: Thumbs up/down with correction learning

## REST API

All endpoints available at `/api`:

**Classification**
- `POST /api/classify` - Classify error with specified method
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
- `GET /api/status` - System health with correction counts by engine
- `GET /api/search-engines-comparison` - Detailed comparison of all three search engines
- `POST /api/update-kb` - Rebuild vector DB

## CLI Usage

### Main Classification System

```bash
cd ml
uv run python src/main.py
```

The system will:
- Initialize all three search engines (Vector DB, Semantic Search, Hybrid Search)
- Automatically detect and use GPU acceleration (Apple Silicon MPS, NVIDIA CUDA, or CPU)
- Classify errors from `data/input_examples.json` using all methods
- Display results with confidence scores and processing times

### Standalone Tools

**Semantic Search:**
```bash
uv run python src/search_engines/semantic_search.py
```

**Hybrid Search:**
```bash
uv run python src/search_engines/hybrid_search.py
```

**Vector DB Classifier:**
```bash
uv run python src/search_engines/vector_db_classifier.py
```

**Interactive Feedback Session:**
```bash
uv run python src/interactive_feedback.py
```
Provides a REPL interface to classify errors and teach the system corrections in real-time.

## Core Components

### GPU Acceleration

The system automatically detects and uses the best available hardware acceleration:

```python
from device_utils import get_best_device, get_device_info

# Automatically detects: 'mps' (Apple Silicon), 'cuda' (NVIDIA), or 'cpu'
device = get_best_device()

# Get detailed device information
info = get_device_info()
# {'device': 'mps', 'platform': 'Darwin', 'machine': 'arm64', ...}
```

**Supported Hardware:**
- Apple Silicon (M1, M2, M3, M4, M5+) via Metal Performance Shaders (MPS)
- NVIDIA GPUs via CUDA
- CPU fallback for systems without GPU

All embedding models automatically use the detected device for optimal performance.

### Feedback Learning System

All three search engines support continuous learning from user corrections:

**Vector DB:** Uses separate ChromaDB collection for learned feedback
```python
vector_kb.teach_system(error_text, correct_doc_path)
```

**Semantic Search:** Uses FAISS feedback store with merge capability
```python
semantic_engine.teach_correction(error_message, correct_service, correct_category)
```

**Hybrid Search:** Uses FAISS feedback store checked before main search
```python
hybrid_engine.teach_correction(error_message, correct_service, correct_category)
```

Learned corrections are checked first (with strict thresholds) before falling back to main search, ensuring the system improves accuracy over time.

## Semantic Search Engine

### `DocumentationSearchEngine` Class

Provides transformer-based semantic similarity matching with document chunking using LangChain and FAISS.

**Initialization:**
```python
search_engine = DocumentationSearchEngine(
    docs_root_dir=DOCS_ROOT_DIR,
    chunk_size=500,      # Characters per chunk
    chunk_overlap=50     # Overlap between chunks
)
```

**Parameters:**
- `docs_root_dir` (str): Root directory containing documentation markdown files
- `model_name` (str, optional): Sentence-transformers model (default: from environment or constants)
- `chunk_size` (int): Characters per chunk (default: 500)
- `chunk_overlap` (int): Overlap between chunks (default: 50)

**How It Works:**

1. **Indexing Phase** (`_index_documents()`):
   - Scans all `.md` files in the documentation directory
   - Splits documents into chunks using RecursiveCharacterTextSplitter
   - Adds context (filename, service) to each chunk
   - Creates FAISS vectorstore with all chunk embeddings

2. **Search Phase** (`find_relevant_doc()`):
   - Checks feedback store first (learned corrections)
   - Falls back to main FAISS vectorstore
   - Computes similarity between query and all chunks
   - Returns the best matching document with confidence score

**Advantages:**
- Document chunking improves accuracy for long documentation
- FAISS provides very fast similarity search (< 30ms typical)
- In-memory operation with no persistence overhead
- Feedback learning via separate FAISS store
- GPU acceleration support

**Example:**
```python
search_engine = DocumentationSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
doc_path, confidence = search_engine.find_relevant_doc(
    "GPS coordinates out of range: lat=95.0"
)
# doc_path: "data/services/meteo-il/GEO_OUT_OF_BOUNDS.md"
# confidence: 87.34

# Teach a correction
search_engine.teach_correction(
    "lat value 95 is invalid",
    "meteo-il",
    "GEO_OUT_OF_BOUNDS"
)
```

## Vector Database Classifier

### `VectorKnowledgeBase` Class

Provides persistent vector storage with ChromaDB and dynamic learning capabilities through user feedback.

**Initialization:**
```python
from vector_db_classifier import VectorKnowledgeBase, initialize_vector_db

# Initialize and populate from dataset
kb = initialize_vector_db()

# Or create instance directly
kb = VectorKnowledgeBase(db_path="./chroma_db")
kb.populate_initial_knowledge(DATASET_PATH)
```

**Key Features:**

1. **Dual Collection Architecture:**
   - `official_docs`: Static knowledge base from training data
   - `learned_feedback`: Dynamic corrections from user feedback

2. **Smart Search Priority:**
   - First checks learned feedback (high confidence threshold: distance < 0.4)
   - Falls back to official knowledge base
   - Returns source information for transparency

3. **Continuous Learning:**
   ```python
   # System learns from corrections
   kb.teach_system(
       error_text="DELETE FROM users WHERE admin=true",
       correct_doc_path="data/services/logitrack/SQL_INJECTION.md"
   )
   # Next search will prioritize this learned knowledge
   ```

**Methods:**

- `populate_initial_knowledge(csv_path)`: Loads training data into vector DB (one-time operation)
- `search(error_query)`: Returns best matching doc with source and confidence
- `teach_system(error_text, correct_doc_path)`: Adds user correction to learned feedback

**Advantages:**
- **Persistent Storage**: Data persists across sessions (ChromaDB on disk)
- **Learning Capability**: Improves over time with user corrections
- **No Retraining**: Updates happen instantly without model retraining
- **Semantic Understanding**: Uses same embeddings as semantic search
- **Transparent Sources**: Distinguishes between official knowledge and learned corrections

**Example:**
```python
kb = initialize_vector_db()

# First search
result = kb.search("DROP TABLE users")
print(result)
# {'source': 'OFFICIAL_KNOWLEDGE', 'doc_path': '...', 'confidence': 'Normal'}

# Teach correction
kb.teach_system("DROP TABLE users", "data/services/logitrack/SECURITY_ALERT.md")

# Second search - now uses learned knowledge
result = kb.search("DROP TABLE users")
print(result)
# {'source': 'LEARNED_MEMORY (Feedback)', 'doc_path': '...', 'confidence': 'High'}
```

## Hybrid Search Engine

### `HybridSearchEngine` Class

Combines BM25 keyword-based search with semantic embeddings using weighted score fusion.

**Initialization:**
```python
hybrid_engine = HybridSearchEngine(
    docs_root_dir=DOCS_ROOT_DIR,
    semantic_weight=0.5,  # Weight for semantic similarity
    bm25_weight=0.5       # Weight for BM25 keyword scores
)
```

**Parameters:**
- `docs_root_dir` (str): Root directory containing documentation
- `semantic_weight` (float): Weight for semantic similarity (0-1)
- `bm25_weight` (float): Weight for BM25 keyword scores (0-1)
- `chunk_size` (int): Characters per chunk (default: 500)
- `chunk_overlap` (int): Overlap between chunks (default: 50)

**How It Works:**

1. **Dual Indexing:**
   - Creates FAISS vectorstore for semantic search
   - Creates BM25 index for keyword search
   - Both indexes use the same chunked documents

2. **Hybrid Search Process:**
   - Checks feedback store first (learned corrections)
   - Performs semantic search (FAISS) - returns top 10
   - Performs BM25 keyword search - returns top 10
   - Normalizes both score sets to 0-1 range
   - Combines scores: `combined = semantic_weight * semantic + bm25_weight * bm25`
   - Returns document with highest combined score

**Advantages:**
- Best of both worlds: semantic understanding + exact keyword matching
- Excellent for technical terms and acronyms
- Handles both natural language and code snippets well
- Feedback learning via FAISS feedback store
- GPU acceleration for semantic component

**Example:**
```python
hybrid_engine = HybridSearchEngine(
    docs_root_dir=DOCS_ROOT_DIR,
    semantic_weight=0.5,
    bm25_weight=0.5
)

doc_path, confidence = hybrid_engine.find_relevant_doc(
    "DROP TABLE users -- SQL injection attempt"
)
# doc_path: "data/services/logitrack/SECURITY_ALERT.md"
# confidence: 92.15

# Get top 3 chunks with score breakdown
chunks = hybrid_engine.find_relevant_chunks(error_text, top_k=3)
for chunk in chunks:
    print(f"Combined: {chunk['score']:.2f}%")
    print(f"Semantic: {chunk['semantic_score']:.2f}%")
    print(f"BM25: {chunk['bm25_score']:.2f}")
```

## Data Format

### Training Data (`data/dataset/errors_dataset.csv`)
```csv
Service,Error_Category,Raw_Input_Snippet,Root_Cause
logitrack,NEGATIVE_VALUE,"weight: -5kg",Invalid sensor reading
meteo-il,MISSING_FIELD,"temperature field missing",Required field not provided
```

### Test Data (`data/input_examples.json`)
```json
[
  {
    "Service": "meteo-il",
    "Error_Category": "MISSING_FIELD",
    "Raw_Input_Snippet": "temperature field missing"
  }
]
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

Create `ml/.env` file (see `ml/.env.example`):

```bash
# API Configuration
API_PORT=5000

# Model Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### File Paths

All file paths are automatically detected in `ml/src/constants.py`:

```python
# Base directories (auto-detected from file location)
BASE_DIR = dirname(dirname(dirname(abspath(__file__))))
ML_DIR = dirname(dirname(abspath(__file__)))  # ml/ directory
MODELS_DIR = join(ML_DIR, 'models')  # ml/models/
DATA_DIR = join(BASE_DIR, 'data')    # project/data/

# Model paths
CHROMA_DB_DIR = join(MODELS_DIR, 'chroma_db')  # ml/models/chroma_db/

# Data paths
DOCS_ROOT_DIR = join(DATA_DIR, 'services')
DATASET_PATH = join(DATA_DIR, 'dataset', 'errors_dataset.csv')

# Model configuration (from .env or defaults)
API_PORT = int(getenv('API_PORT', 5000))
EMBEDDING_MODEL = getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')

# Document chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
```

No manual path configuration needed! Works in Docker and local environments.

## Storage and Persistence

### Vector Database (ChromaDB)
Vector embeddings and learned feedback are persisted in `ml/models/chroma_db/`:
- Survives across sessions
- No need to re-index on restart
- Learned corrections are permanent
- Two collections: `official_docs` and `learned_feedback`
- Can be version controlled or backed up

### In-Memory Stores (FAISS)
Semantic Search and Hybrid Search use FAISS in-memory vectorstores:
- Fast initialization and search (< 30ms typical)
- Feedback corrections stored in separate FAISS stores
- Re-indexed on restart (fast operation)
- Lower memory footprint than ChromaDB for small corpora

### Package Management (UV)
Dependencies managed with UV (Rust-based package manager):
- Defined in `ml/pyproject.toml`
- Lock file for reproducible builds
- Much faster than pip
- Python 3.13+ required
