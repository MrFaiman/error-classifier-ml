# NLP-Based Error Explanation Feature

## Overview

The error classifier now includes an **NLP-powered explanation system** that generates human-readable explanations for classified errors. This feature uses transformer models (T5, FLAN-T5, or BART) to analyze the error message and documentation, then produces clear, actionable explanations.

## Features

### 🤖 Intelligent Explanations
- **Transformer Models**: Uses state-of-the-art NLP models (T5-small by default)
- **Context-Aware**: Combines error message, documentation content, and classification metadata
- **Multiple Formats**: Supports both simple explanations and detailed context

### 📝 Documentation Analysis
- **Automatic Extraction**: Parses markdown documentation for key sections
- **Key Information**: Extracts title, description, root cause, and solution
- **Smart Summarization**: Condenses complex documentation into actionable insights

### ⚡ Performance Optimizations
- **Caching**: Built-in cache for repeated queries
- **Lightweight Models**: Uses T5-small for fast inference
- **Rule-Based Fallback**: Works even without model availability

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Classification Request                  │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│         Hybrid Search Engine (TF-IDF + BM25)        │
│         Returns: doc_path, confidence               │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              NLP Error Explainer                     │
│  1. Reads documentation file                        │
│  2. Extracts key sections (Description, Cause, etc.)│
│  3. Builds prompt with error + context              │
│  4. Generates explanation using T5 model            │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              API Response                            │
│  - doc_path                                         │
│  - confidence                                       │
│  - explanation (NEW!)                               │
└─────────────────────────────────────────────────────┘
```

## API Integration

### Single Classification with Explanation

**Request:**
```bash
curl -X POST http://localhost:3100/api/classify \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "Quantity cannot be negative: -5",
    "method": "HYBRID_CUSTOM",
    "multi_search": false
  }'
```

**Response:**
```json
{
  "doc_path": "/path/to/data/services/logitrack/NEGATIVE_VALUE.md",
  "confidence": 87.5,
  "source": "HYBRID_CUSTOM (TF-IDF + BM25)",
  "explanation": "This error occurs when a numeric field contains a negative value where only positive values are expected. The system validates that fields like quantities, prices, or measurements must be positive. Ensure all numeric inputs are positive numbers greater than 0."
}
```

### Multi-Search with Explanations

**Request:**
```bash
curl -X POST http://localhost:3100/api/classify \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "sensor value out of bounds",
    "multi_search": true
  }'
```

**Response:**
```json
{
  "multi_search": true,
  "doc_path": "/path/to/data/services/skyguard/GEO_OUT_OF_BOUNDS.md",
  "confidence": 92.3,
  "explanation": "This error is classified as 'GEO_OUT_OF_BOUNDS' in the skyguard service. Sensor readings must fall within valid geographical boundaries. Verify that latitude and longitude values are within acceptable ranges.",
  "all_results": [
    {
      "method": "HYBRID_CUSTOM",
      "doc_path": "/path/to/data/services/skyguard/GEO_OUT_OF_BOUNDS.md",
      "confidence": 92.3,
      "explanation": "..."
    }
  ]
}
```

## Configuration

### Model Selection

The NLP explainer supports multiple transformer models:

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `t5-small` | ~242MB | Fast | Good | **Default** - Production use |
| `google/flan-t5-base` | ~990MB | Medium | Better | Higher quality explanations |
| `facebook/bart-large-cnn` | ~1.6GB | Slow | Best | Maximum quality |

### Changing the Model

In `src/api/services.py`:

```python
def _initialize_explainer(self):
    """Initialize NLP explainer for error explanations"""
    # Use a different model
    self.nlp_explainer = get_explainer(model_name="google/flan-t5-base")
```

### Environment Variables

Add to `.env`:

```bash
# NLP Model Configuration
NLP_MODEL_NAME=t5-small
NLP_CACHE_ENABLED=true

# GPU Support (optional)
CUDA_VISIBLE_DEVICES=0  # Use GPU 0
```

## Usage Examples

### Python API

```python
from algorithms import get_explainer

# Initialize explainer
explainer = get_explainer(model_name="t5-small")

# Generate simple explanation
explanation = explainer.explain_error(
    error_message="Invalid coordinate: -999",
    doc_path="/path/to/doc.md",
    confidence=85.0,
    metadata={'service': 'meteo-il', 'category': 'GEO_OUT_OF_BOUNDS'}
)

print(explanation)
# Output: "This error is classified as 'GEO_OUT_OF_BOUNDS' in the meteo-il service. 
#          Geographic coordinates must be within valid ranges..."

# Generate detailed explanation with context
detailed = explainer.explain_with_context(
    error_message="Invalid coordinate: -999",
    doc_path="/path/to/doc.md",
    confidence=85.0,
    metadata={'service': 'meteo-il', 'category': 'GEO_OUT_OF_BOUNDS'},
    include_raw_doc=True
)

print(detailed['explanation'])
print(f"Root Cause: {detailed['key_points']['root_cause']}")
print(f"Solution: {detailed['key_points']['solution']}")

# Batch processing
classifications = [
    {'error_message': 'Error 1', 'doc_path': '/path/1.md', 'confidence': 80.0},
    {'error_message': 'Error 2', 'doc_path': '/path/2.md', 'confidence': 75.0}
]

explanations = explainer.batch_explain(classifications)
```

### Cache Management

```python
# Get cache statistics
stats = explainer.get_cache_stats()
print(f"Cache size: {stats['cache_size']}")
print(f"Cache enabled: {stats['cache_enabled']}")

# Clear cache
explainer.clear_cache()
```

## Performance

### Benchmarks (T5-small on CPU)

- **First explanation**: ~2-3 seconds (model loading)
- **Cached explanations**: <10ms
- **Subsequent explanations**: ~200-500ms
- **Batch processing (10 items)**: ~3-5 seconds

### Memory Usage

- **T5-small**: ~300MB RAM
- **FLAN-T5-base**: ~1.2GB RAM
- **BART-large**: ~2GB RAM

### GPU Acceleration

With CUDA-enabled GPU:
- **T5-small**: ~50-100ms per explanation
- **FLAN-T5-base**: ~100-200ms per explanation

## Testing

### Run NLP Explainer Tests

```bash
cd core
uv run pytest tests/test_nlp_explainer.py -v
```

### Test Coverage

The test suite covers:
- ✅ Model initialization (including fallback)
- ✅ Documentation parsing and key extraction
- ✅ Simple explanation generation
- ✅ Detailed explanation with context
- ✅ Batch processing
- ✅ Caching mechanism
- ✅ Low confidence warnings
- ✅ Missing documentation handling
- ✅ Multiple services and categories
- ✅ Rule-based fallback mode

### Manual Testing

```bash
# Test the explainer directly
cd core/src
python -m algorithms.nlp_explainer
```

## Troubleshooting

### Model Download Issues

If model download fails:

```python
# Pre-download model
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
```

### Out of Memory

If you encounter OOM errors:

1. Use a smaller model: `t5-small` instead of `flan-t5-base`
2. Reduce max_length in pipeline initialization
3. Disable caching temporarily

### Slow Performance

To improve speed:

1. Enable GPU if available (add `CUDA_VISIBLE_DEVICES=0` to .env)
2. Use model quantization (8-bit inference)
3. Reduce max_length parameter
4. Enable caching for repeated queries

### Rule-Based Fallback

If the model fails to load, the system automatically falls back to rule-based explanations that extract and format information directly from documentation files.

## Future Enhancements

### Planned Features

1. **Fine-tuned Models**: Train domain-specific models on error classification data
2. **Multi-language Support**: Generate explanations in multiple languages
3. **Confidence-Based Verbosity**: More detailed explanations for low-confidence predictions
4. **Interactive Explanations**: Ask follow-up questions about errors
5. **Explanation History**: Track and analyze explanation quality over time

### Contributing

To improve the NLP explainer:

1. Add more test cases in `tests/test_nlp_explainer.py`
2. Experiment with different models and prompts
3. Improve documentation parsing logic
4. Add support for more explanation formats

## Dependencies

The NLP explainer requires:

```toml
dependencies = [
    "transformers>=4.30.0",  # Hugging Face transformers
    "torch>=2.0.0",          # PyTorch backend
    "sentencepiece>=0.1.99", # Tokenization for T5
]
```

Install with:

```bash
cd core
uv sync
```

## Security Considerations

- **Model Source**: Models are downloaded from Hugging Face (trusted source)
- **Input Sanitization**: Error messages are truncated to prevent injection
- **Output Filtering**: Explanations are validated for appropriate content
- **No Data Leakage**: Models run locally, no data sent to external APIs

## License

This feature is part of the error-classifier-ml project and follows the same license.

---

## Quick Reference

### Initialize Explainer
```python
from algorithms import get_explainer
explainer = get_explainer(model_name="t5-small")
```

### Generate Explanation
```python
explanation = explainer.explain_error(
    error_message="Your error here",
    doc_path="/path/to/doc.md",
    confidence=85.0,
    metadata={'service': 'service_name', 'category': 'ERROR_TYPE'}
)
```

### API Endpoint
```
POST /api/classify
Body: {"error_message": "...", "method": "HYBRID_CUSTOM"}
Response: {"doc_path": "...", "confidence": 85.0, "explanation": "..."}
```

---

For more information, see the main [README.md](../README.md) and [API_STRUCTURE.md](API_STRUCTURE.md).
