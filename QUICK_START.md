# Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Node.js 18+
- MongoDB (optional, for feedback storage)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd error-classifier-ml

# Backend setup
cd core
pip install -r requirements.txt
cd ..

# Frontend setup
cd ui
npm install
cd ..
```

## 🎯 Running the System

### Start Backend (API Server)
```bash
cd core
python src/server.py
```
API runs at: http://localhost:3100

### Start Frontend (React UI)
```bash
cd ui
npm run dev
```
UI runs at: http://localhost:3000

## 🔍 Using the Search Engine

The system uses a **Hybrid Custom Search Engine** that combines:
- **TF-IDF**: Term frequency-inverse document frequency
- **BM25**: Probabilistic ranking algorithm
- **Feedback Learning**: Adapts based on user corrections

## 📡 API Endpoints

### Classify Error
```bash
POST http://localhost:3100/api/classify
Content-Type: application/json

{
  "error_message": "negative value detected in sensor"
}
```

### Teach Correction
```bash
POST http://localhost:3100/api/teach-correction
Content-Type: application/json

{
  "error_text": "sensor glitch",
  "correct_doc_path": "data/services/logitrack/SENSOR_ERROR.md"
}
```

### Get Status
```bash
GET http://localhost:3100/api/status
```

## 💡 Example Usage

### Python API Usage
```python
from search_engines import HybridCustomSearchEngine

# Initialize engine
engine = HybridCustomSearchEngine(
    docs_root_dir="data/services",
    tfidf_weight=0.4,
    bm25_weight=0.6
)

# Search for a document
doc_path, confidence = engine.find_relevant_doc(
    "negative value error"
)
print(f"Match: {doc_path} ({confidence:.1f}%)")

# Teach a correction
engine.teach_correction(
    "sensor glitch",
    "data/services/logitrack/SENSOR_ERROR.md"
)
```

### cURL Examples
```bash
# Classify an error
curl -X POST http://localhost:3100/api/classify \
  -H "Content-Type: application/json" \
  -d '{"error_message":"negative value detected"}'

# Teach correction
curl -X POST http://localhost:3100/api/teach-correction \
  -H "Content-Type: application/json" \
  -d '{
    "error_text":"sensor malfunction",
    "correct_doc_path":"data/services/logitrack/SENSOR_ERROR.md"
  }'
```

## 🐛 Troubleshooting

### Issue: Import Errors
```bash
# Reinstall dependencies
cd core
pip install -r requirements.txt
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

### Issue: MongoDB Connection
```bash
# Start MongoDB locally
mongod --dbpath /path/to/data

# Or use Docker
docker run -d -p 27017:27017 mongo
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
cd core && python src/server.py
```

## 🚢 Deployment

### Docker
```bash
cd docker
docker-compose up -d --build
```

Access:
- Frontend: http://localhost
- API: http://localhost:3100

## 💡 Tips

1. **Feedback Learning**: Use thumbs up/down to improve accuracy over time
2. **Confidence Scores**: Higher scores indicate better matches
3. **Documentation**: Keep error docs well-structured for better matching

---

For more details, see the main README.md
