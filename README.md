# Error Classification System

An ML-based system that automatically classifies error logs and maps them to their corresponding documentation files using Natural Language Processing, featuring both traditional ML (Random Forest) and semantic search approaches.

## Overview

This project provides two methods for matching error logs to documentation:

1. **Traditional ML Pipeline** (`main.py`): Uses TF-IDF vectorization with Random Forest classification
2. **Semantic Search Engine** (`semantic_search.py`): Uses transformer-based embeddings (Sentence-BERT) for similarity matching

The system analyzes error patterns across different services (logitrack, meteo-il, skyguard) and categorizes them into specific error types, mapping each to the relevant documentation file.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Ensure `dataset/errors_dataset.csv` exists with training data
2. Create `dataset/input_examples.json` with test cases
3. Run the main script:
```bash
python main.py
```

The system will:
- Train the Random Forest model on historical error data (or load from checkpoint)
- Save the trained model to `checkpoints/`
- Use semantic search to classify errors in `dataset/input_examples.json`

### Standalone Semantic Search

You can also run the semantic search engine independently:
```bash
python semantic_search.py
```

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
   - Returns the predicted file path (e.g., `docs\services\meteo-il\MISSING_FIELD.md`)

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
# doc_path: "docs\services\meteo-il\MISSING_FIELD.md"
# conf: 92.45
```

## Semantic Search Engine

### `DocumentationSearchEngine` Class

Provides transformer-based semantic similarity matching between error logs and documentation files.

**Initialization:**
```python
search_engine = DocumentationSearchEngine(docs_root_dir='docs', model_name='all-MiniLM-L6-v2')
```

**Parameters:**
- `docs_root_dir` (str): Root directory containing documentation markdown files
- `model_name` (str): Sentence-transformers model name (default: 'all-MiniLM-L6-v2')

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
search_engine = DocumentationSearchEngine(docs_root_dir='docs')
doc_path, similarity = search_engine.find_relevant_doc(
    "GPS coordinates out of range: lat=95.0"
)
# doc_path: "docs\services\meteo-il\GEO_OUT_OF_BOUNDS.md"
# similarity: 87.34
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
DOCS_ROOT_DIR = 'docs'
DATASET_PATH = 'dataset\\errors_dataset.csv'
INPUT_EXAMPLES_PATH = 'dataset\\input_examples.json'
```

## Model Checkpoints

Models are automatically saved to `checkpoints/` with timestamps and as `latest_model.pkl`. Set `FORCE_RETRAIN = False` to reuse the latest checkpoint.
