# Error Classification System

An ML-based system that automatically classifies error logs and maps them to their corresponding documentation files using Natural Language Processing, featuring three advanced classification approaches.

## Overview

This project provides three methods for matching error logs to documentation:

1. **Vector Database with ChromaDB** (`vector_db_classifier.py`): Persistent vector store with learned feedback capability
2. **Semantic Search Engine** (`semantic_search.py`): Real-time transformer-based embeddings (Sentence-BERT) for similarity matching
3. **Traditional ML Pipeline** (`main.py`): TF-IDF vectorization with Random Forest classification

The system analyzes error patterns across different services (logitrack, meteo-il, skyguard) and categorizes them into specific error types, mapping each to the relevant documentation file.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Main Classification System

1. Ensure `dataset/errors_dataset.csv` exists with training data
2. Create `dataset/input_examples.json` with test cases
3. Run the main script:
```bash
python main.py
```

The system will:
- Train the Random Forest model on historical error data (or load from checkpoint)
- Save the trained model to `checkpoints/`
- Classify errors using Vector DB (default) or Semantic Search based on `USE_VECTOR_DB` flag

To switch between classification methods, edit `main.py`:
```python
USE_VECTOR_DB = True   # Use Vector DB with learned feedback
USE_VECTOR_DB = False  # Use Semantic Search
```

### Standalone Tools

**Semantic Search:**
```bash
python semantic_search.py
```

**Vector DB Classifier:**
```bash
python vector_db_classifier.py
```

**Interactive Feedback Session:**
```bash
python interactive_feedback.py
```
Provides a REPL interface to classify errors and teach the system corrections in real-time.

## Core Functions

### `build_model()`

Creates and returns the complete ML pipeline for error classification.

**Architecture:**

The function constructs a scikit-learn Pipeline with two stages:

1. **TF-IDF Vectorization** (`TfidfVectorizer`):
   - Converts text into numerical features using Term Frequency-Inverse Document Frequency
   - `ngram_range=(1, 2)`: Captures both individual words (unigrams) and word pairs (bigrams)
     - Example: "missing field error" → ["missing", "field", "error", "missing field", "field error"]
   - `analyzer='word'`: Tokenizes at the word level (as opposed to character level)
   - This creates a sparse matrix where each row represents an error log and columns represent TF-IDF scores for each n-gram

2. **Random Forest Classifier** (`RandomForestClassifier`):
   - Ensemble learning method that builds multiple decision trees
   - `n_estimators=100`: Creates 100 decision trees in the forest
   - `random_state=42`: Sets seed for reproducibility
   - Each tree votes on the classification, and the majority vote determines the final prediction
   - Handles high-dimensional TF-IDF features well and provides probability estimates

**Why This Architecture?**

- TF-IDF captures the importance of specific error keywords relative to the entire dataset
- Bigrams help capture multi-word error patterns like "schema validation" or "missing field"
- Random Forest is robust to overfitting and works well with sparse text features
- The pipeline ensures consistent preprocessing during both training and inference

**Returns:** A scikit-learn Pipeline object ready for training with `.fit()` or prediction with `.predict()`

### `classify_error(log_line_dict)`

Performs inference on a single error log entry and returns the predicted documentation path with confidence score.

**Parameters:**
- `log_line_dict` (dict): A dictionary containing error details with keys:
  - `Service`: The service name (e.g., "logitrack", "meteo-il", "skyguard")
  - `Error_Category`: The error type (e.g., "MISSING_FIELD", "SCHEMA_VALIDATION")
  - `Raw_Input_Snippet`: The actual error message or log snippet

**Process:**

1. **Feature Construction:**
   ```python
   input_text = f"{log_line_dict['Service']} {log_line_dict['Error_Category']} {log_line_dict['Raw_Input_Snippet']}"
   ```
   Concatenates service, category, and snippet into a single string that matches the training data format (`combined_features`).

2. **Prediction:**
   ```python
   prediction = model.predict([input_text])[0]
   ```
   - Passes the text through the TF-IDF vectorizer (transforms to numerical features)
   - Random Forest classifier votes on the most likely documentation path
   - Returns the predicted file path (e.g., `dataset\docs\services\meteo-il\MISSING_FIELD.md`)

3. **Confidence Calculation:**
   ```python
   probs = model.predict_proba([input_text])
   confidence = np.max(probs) * 100
   ```
   - `predict_proba()` returns probability estimates for all possible classes
   - Takes the maximum probability (the predicted class's confidence)
   - Converts to percentage (0-100 scale)
   - Higher confidence (>80%) indicates strong certainty, lower values suggest ambiguity

**Returns:**
- `prediction` (str): Path to the predicted documentation file
- `confidence` (float): Confidence percentage (0-100)

**Example:**
```python
error = {
    "Service": "meteo-il",
    "Error_Category": "MISSING_FIELD",
    "Raw_Input_Snippet": "Required field 'temperature' not found in payload"
}
doc_path, conf = classify_error(error)
# doc_path: "dataset\\docs\\services\\meteo-il\\MISSING_FIELD.md"
# conf: 92.45
```

## Semantic Search Engine

### `DocumentationSearchEngine` Class

Provides transformer-based semantic similarity matching between error logs and documentation files.

**Initialization:**
```python
search_engine = DocumentationSearchEngine(docs_root_dir='dataset\\docs')
# Uses default model from constants.py (all-MiniLM-L6-v2)

# Or specify custom model
search_engine = DocumentationSearchEngine(docs_root_dir='dataset\\docs', model_name='custom-model')
```

**Parameters:**
- `docs_root_dir` (str): Root directory containing documentation markdown files
- `model_name` (str, optional): Sentence-transformers model name (default: from `constants.EMBEDDING_MODEL`)

**How It Works:**

1. **Indexing Phase** (`_index_documents()`):
   - Scans all `.md` files in the documentation directory
   - Reads file content and creates combined text (filename + content)
   - Generates embeddings using Sentence-BERT model
   - Stores embeddings as tensors for fast similarity computation

2. **Search Phase** (`find_relevant_doc()`):
   - Encodes the error snippet into an embedding vector
   - Computes cosine similarity between query and all document embeddings
   - Returns the most similar document with confidence score

**Advantages over Traditional ML:**
- No training data required - works immediately with existing docs
- Understands semantic meaning, not just keyword matching
- Adapts automatically when documentation is added/updated
- Better handles paraphrasing and synonyms

**Example:**
```python
search_engine = DocumentationSearchEngine(docs_root_dir='dataset\\docs')
doc_path, similarity = search_engine.find_relevant_doc(
    "GPS coordinates out of range: lat=95.0"
)
# doc_path: "dataset\\docs\\services\\meteo-il\\GEO_OUT_OF_BOUNDS.md"
# similarity: 87.34
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
       correct_doc_path="dataset/docs/services/logitrack/SQL_INJECTION.md"
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
kb.teach_system("DROP TABLE users", "dataset/docs/services/logitrack/SECURITY_ALERT.md")

# Second search - now uses learned knowledge
result = kb.search("DROP TABLE users")
print(result)
# {'source': 'LEARNED_MEMORY (Feedback)', 'doc_path': '...', 'confidence': 'High'}
```

## Data Format

### Training Data (`dataset/errors_dataset.csv`)
```
Service,Error_Category,Raw_Input_Snippet,Root_Cause
logitrack,NEGATIVE_VALUE,"weight: -5kg",Invalid sensor reading
```

### Test Data (`dataset/input_examples.json`)
```json
[
  {
    "Service": "meteo-il",
    "Error_Category": "MISSING_FIELD",
    "Raw_Input_Snippet": "temperature field missing"
  }
]
```

## Configuration

All file paths are centralized in `constants.py`:
```python
CHECKPOINT_DIR = 'checkpoints'
DOCS_ROOT_DIR = 'dataset\\docs'
DATASET_PATH = 'dataset\\errors_dataset.csv'
INPUT_EXAMPLES_PATH = 'dataset\\input_examples.json'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Sentence-transformers model for embeddings
```

## Storage and Persistence

### Model Checkpoints (Traditional ML)
Models are automatically saved to `checkpoints/` with timestamps and as `latest_model.pkl`. Set `FORCE_RETRAIN = False` to reuse the latest checkpoint.

### Vector Database (ChromaDB)
Vector embeddings and learned feedback are persisted in `chroma_db/` directory:
- Survives across sessions
- No need to re-index on restart
- Learned corrections are permanent
- Can be version controlled or backed up

## Project Structure

```
errors_classification/
├── main.py                    # Main classifier with method selection
├── vector_db_classifier.py    # ChromaDB vector store implementation
├── semantic_search.py         # Real-time semantic search
├── interactive_feedback.py    # Interactive REPL for learning
├── constants.py               # Centralized configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation
├── dataset/
│   ├── errors_dataset.csv     # Training data
│   ├── input_examples.json    # Test cases
│   └── docs/
│       └── services/          # Documentation files
├── checkpoints/               # Trained ML models
└── chroma_db/                 # Vector database storage
```
