# Error Classification System

An ML-based system that automatically classifies error logs and maps them to their corresponding documentation files using Natural Language Processing and Random Forest classification.

## Overview

This project trains a machine learning model to predict which documentation file should be referenced for a given error log. It uses TF-IDF vectorization combined with Random Forest classification to analyze error patterns across different services (logitrack, meteo-il, skyguard) and categorize them into specific error types.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Ensure `errors_dataset.csv` exists with training data
2. (Optional) Create `input_examples.json` with test cases
3. Run the script:
```bash
python main.py
```

The system will:
- Train the model on historical error data (or load from checkpoint)
- Save the trained model to `checkpoints/`
- Classify any errors in `input_examples.json`

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

## Data Format

### Training Data (`errors_dataset.csv`)
```
Service,Error_Category,Raw_Input_Snippet,Root_Cause
logitrack,NEGATIVE_VALUE,"weight: -5kg",Invalid sensor reading
```

### Test Data (`input_examples.json`)
```json
[
  {
    "Service": "meteo-il",
    "Error_Category": "MISSING_FIELD",
    "Raw_Input_Snippet": "temperature field missing"
  }
]
```

## Model Checkpoints

Models are automatically saved to `checkpoints/` with timestamps and as `latest_model.pkl`. Set `FORCE_RETRAIN = False` to reuse the latest checkpoint.
