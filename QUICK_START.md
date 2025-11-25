# Quick Start Guide - Custom ML Implementation

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- UV package manager
- Node.js 18+

### Installation

```bash
# Clone repository
git clone <repo-url>
cd error-classifier-ml

# Backend setup
cd ml
uv sync
cd ..

# Frontend setup
cd ui
npm install
cd ..
```

## 🎯 Running the System

### Start Backend (API Server)
```bash
cd ml
python src/api_server.py
```
API runs at: http://localhost:3100

### Start Frontend (React UI)
```bash
cd ui
npm run dev
```
UI runs at: http://localhost:3000

### Test Custom ML Implementations
```bash
cd ml
python src/main.py
```

## 🔍 Available Search Methods

### 1. Custom TF-IDF (Default)
- **Best for**: Fast keyword matching
- **Algorithm**: TF-IDF + Cosine Similarity
- **Speed**: Fast (< 40ms)
- **Memory**: Low

### 2. Enhanced Custom
- **Best for**: Accurate matching with typo tolerance
- **Algorithms**: TF-IDF + K-Means + Edit Distance + Chunking
- **Speed**: Moderate (< 100ms)
- **Memory**: Medium

## 📡 API Endpoints

### Classify Error
```bash
POST http://localhost:3100/api/classify
Content-Type: application/json

{
  "error_message": "ValueError: list index out of range",
  "method": "CUSTOM_TFIDF"
}
```

**Valid methods:**
- `CUSTOM_TFIDF` - Custom TF-IDF + Cosine Similarity
- `ENHANCED_CUSTOM` - All custom ML algorithms

### Multi-Search
```bash
POST http://localhost:3100/api/classify
Content-Type: application/json

{
  "error_message": "ValueError: list index out of range",
  "multi_search": true
}
```

### Teach Correction
```bash
POST http://localhost:3100/api/teach-correction
Content-Type: application/json

{
  "error_text": "ValueError: list index out of range",
  "correct_doc_path": "data/services/logitrack/NEGATIVE_VALUE.md",
  "engine": "CUSTOM_TFIDF"
}
```

### Get Status
```bash
GET http://localhost:3100/api/status
```

### Compare Engines
```bash
GET http://localhost:3100/api/search-engines-comparison
```

## 📚 Custom ML Modules

### Import Custom Implementations
```python
from custom_ml import (
    TfidfVectorizer,      # Custom TF-IDF
    SimilaritySearch,     # Custom similarity metrics
    KMeans,               # Custom K-Means clustering
    EditDistance,         # Custom Levenshtein distance
    FuzzyMatcher,         # Custom fuzzy matching
    TextChunker,          # Custom text chunking
    TextPreprocessor,     # Custom text preprocessing
    ENGLISH_STOP_WORDS    # English stop words list
)
```

### Use Custom TF-IDF
```python
from custom_ml import TfidfVectorizer

# Initialize
vectorizer = TfidfVectorizer(
    max_features=5000,
    lowercase=True,
    stop_words=ENGLISH_STOP_WORDS,
    ngram_range=(1, 2)
)

# Fit and transform
documents = ["error message 1", "error message 2"]
tfidf_matrix = vectorizer.fit_transform(documents)

# Get feature names
features = vectorizer.get_feature_names()
```

### Use K-Means Clustering
```python
from custom_ml import KMeans
import numpy as np

# Initialize
kmeans = KMeans(n_clusters=5, max_iters=100, random_state=42)

# Fit
data = np.random.rand(100, 10)
kmeans.fit(data)

# Predict
labels = kmeans.predict(data)
```

### Use Edit Distance
```python
from custom_ml import EditDistance, FuzzyMatcher

# Calculate distance
distance = EditDistance.levenshtein("hello", "hallo")  # Returns 1

# Fuzzy matching
matcher = FuzzyMatcher(["hello", "world", "python"])
matches = matcher.find_matches("helo", max_distance=2, max_matches=3)
```

### Use Custom Search Engines
```python
from search_engines import CustomTfidfSearchEngine, EnhancedCustomSearchEngine

# Custom TF-IDF Search
custom_tfidf = CustomTfidfSearchEngine(docs_root_dir="data/services")
doc_path, confidence = custom_tfidf.find_relevant_doc("error message")

# Enhanced Custom Search
enhanced = EnhancedCustomSearchEngine(docs_root_dir="data/services")
doc_path, confidence = enhanced.find_relevant_doc("error message")

# Teach correction
custom_tfidf.teach_correction(
    error_text="error message",
    correct_doc_path="data/services/service/ERROR.md"
)
```

## 🎨 Frontend Usage

### Search Component
```jsx
import SearchInput from '../components/SearchInput';

<SearchInput
    errorInput={errorInput}
    onErrorInputChange={setErrorInput}
    method={method}
    onMethodChange={setMethod}
    multiSearch={multiSearch}
    onMultiSearchChange={setMultiSearch}
    onSearch={handleSearch}
    isSearching={isSearching}
/>
```

### Available Methods in UI
- "Custom TF-IDF (No Blackbox)"
- "Enhanced Custom (All ML Algorithms)"

## 🧪 Testing

### Test Individual Components
```bash
# Test TF-IDF
python -c "from custom_ml import TfidfVectorizer; print('TF-IDF OK')"

# Test K-Means
python -c "from custom_ml import KMeans; print('K-Means OK')"

# Test Edit Distance
python -c "from custom_ml import EditDistance; print('Edit Distance OK')"

# Test Search Engines
python -c "from search_engines import CustomTfidfSearchEngine; print('Search OK')"
```

### Run All Tests
```bash
cd ml
python src/main.py
```

## 🐛 Troubleshooting

### Issue: Import Errors
```bash
# Clear cache
find ml/src -type d -name "__pycache__" -exec rm -rf {} +

# Reinstall dependencies
cd ml
uv sync
```

### Issue: API Not Starting
```bash
# Check if port 3100 is available
lsof -i :3100

# Kill process if needed
kill -9 $(lsof -t -i:3100)
```

### Issue: UI Not Loading
```bash
# Clear node modules and reinstall
cd ui
rm -rf node_modules package-lock.json
npm install
```

## 📊 Performance Tips

### For Faster Search
- Use `CUSTOM_TFIDF` for quick results
- Reduce `max_features` in TfidfVectorizer
- Disable multi-search for single queries

### For Better Accuracy
- Use `ENHANCED_CUSTOM` for complex queries
- Enable multi-search for consensus
- Teach corrections for common errors

### For Lower Memory
- Reduce `max_features` in TF-IDF
- Reduce `n_clusters` in K-Means
- Use smaller `chunk_size` in text processing

## 🎓 Learning Resources

### Understand TF-IDF
- Read: `ml/src/custom_ml/tfidf.py`
- Formula: TF(t,d) × IDF(t)
- Documentation: `CUSTOM_ML_IMPLEMENTATIONS.md`

### Understand K-Means
- Read: `ml/src/custom_ml/kmeans.py`
- Algorithm: k-means++ initialization
- Minimize: Σ ||x - μ_k||²

### Understand Edit Distance
- Read: `ml/src/custom_ml/edit_distance.py`
- Algorithm: Dynamic Programming
- Use case: Typo tolerance

## 🔗 Useful Commands

```bash
# Update dependencies
cd ml && uv sync

# Format code
cd ml && black src/

# Check errors
cd ml && pylance src/

# Build for production
cd ui && npm run build

# Run production server
cd ui && npm run preview
```

## 📝 Adding New Documentation

```bash
# Add a new error documentation file
cat > data/services/myservice/NEW_ERROR.md << EOF
# New Error Category

## Overview
Description of the error

## Root Cause
Why it happens

## Solution
How to fix it
EOF

# Restart API to re-index
cd ml && python src/api_server.py
```

## 🚢 Deployment

### Docker (Coming Soon)
```bash
cd docker
docker-compose up -d --build
```

### Manual Deployment
1. Copy project to server
2. Install dependencies
3. Configure ports
4. Start backend and frontend
5. Set up reverse proxy (nginx)

## 💡 Tips

1. **Multi-Search**: Enable for higher confidence through consensus
2. **Feedback Learning**: Teach corrections to improve over time
3. **Custom Implementation**: All ML is transparent - check the code!
4. **Performance**: Custom TF-IDF is faster than Enhanced Custom
5. **Accuracy**: Enhanced Custom handles typos better

## 🆘 Need Help?

- Check `REFACTORING_SUMMARY.md` for architecture details
- Check `CUSTOM_ML_IMPLEMENTATIONS.md` for algorithm details
- Check `SYSTEM_WORKFLOW.md` for system flow diagrams
- Check source code - everything is documented!

---

**Remember**: No blackbox libraries. Just pure, custom ML! 🎯
