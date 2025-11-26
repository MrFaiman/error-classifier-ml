# Feedback Loop System - Adaptive Learning Guide

## Overview

The Feedback Loop system implements **reinforcement learning** to improve classification confidence over time. It learns from user corrections and automatically adjusts confidence scores based on historical accuracy. All feedback data is stored persistently in MongoDB.

## Key Features

### 1. **Confidence Adjustment**
- Tracks query-document accuracy over time
- Boosts confidence for historically correct predictions (+5 to +10 points)
- Penalizes confidence for historically incorrect predictions (-10 to -20 points)
- Uses exponential moving average for smooth learning

### 2. **Query Pattern Learning**
- Recognizes similar queries using Jaccard similarity
- Learns which documents work best for specific query patterns
- Provides high-confidence predictions (95-100%) for known good matches
- Transfers learning to similar unseen queries

### 3. **Document Accuracy Tracking**
- Monitors each document's overall accuracy rate
- Adjusts confidence based on document reliability
- Identifies top-performing documents

### 4. **Search Engine Performance**
- Tracks accuracy per search engine (CUSTOM_TFIDF, ENHANCED_CUSTOM, HYBRID_CUSTOM)
- Dynamically adjusts engine weights using UCB algorithm
- Enables intelligent ensemble weighting

### 5. **Persistent Learning**
- Saves feedback data to MongoDB
- Persists across server restarts
- Maintains complete history of corrections and predictions
- Supports queries and analytics

## How It Works

### Mathematical Foundation

#### 1. Success Rate Update (Exponential Moving Average)
```
success_rate_new = α × is_correct + (1 - α) × success_rate_old
```
Where:
- α = learning rate (default: 0.1)
- is_correct = 1 if prediction was correct, 0 otherwise
- Smooth adaptation prevents overreaction to single corrections

#### 2. Confidence Adjustment
```
adjusted_confidence = original_confidence + 
                     (success_rate - 0.5) × boost_factor +
                     (doc_accuracy - 0.5) × 5 +
                     similar_query_boost
```
Where:
- boost_factor = 5.0 for correct history, -10.0 for incorrect
- doc_accuracy = document's overall accuracy rate
- similar_query_boost = up to 5 points based on similar successful queries

#### 3. Engine Weight (UCB-inspired)
```
weight = accuracy + sqrt(2 × ln(total_predictions) / total_predictions)
```
Where:
- accuracy = correct / (correct + incorrect)
- Exploration bonus encourages trying less-tested engines

#### 4. Query Similarity (Jaccard)
```
similarity = |words1 ∩ words2| / |words1 ∪ words2|
```

## API Integration

### Recording Predictions
```python
feedback_loop.record_prediction(
    query="negative value error",
    predicted_doc="services/logitrack/NEGATIVE_VALUE.md",
    confidence=75.0,
    engine="HYBRID_CUSTOM"
)
```

### Recording User Feedback
```python
result = feedback_loop.record_feedback(
    query="negative value error",
    predicted_doc="services/logitrack/NEGATIVE_VALUE.md",
    actual_doc="services/logitrack/NEGATIVE_VALUE.md",  # Correct!
    original_confidence=75.0,
    engine="HYBRID_CUSTOM"
)

# Result contains:
# {
#   'is_correct': True,
#   'success_rate': 0.85,
#   'query_total_feedback': 5,
#   'doc_accuracy': 0.92,
#   'engine_accuracy': 0.88,
#   'engine_weight': 0.95
# }
```

### Adjusting Confidence
```python
adjusted = feedback_loop.adjust_confidence(
    query="negative value problem",
    doc="services/logitrack/NEGATIVE_VALUE.md",
    original_confidence=70.0,
    engine="HYBRID_CUSTOM"
)
# Returns: 82.5 (boosted due to similar successful queries)
```

### Getting Best Known Document
```python
best = feedback_loop.get_best_document_for_query("negative value")
if best:
    doc_path, confidence = best
    # Returns: ("services/logitrack/NEGATIVE_VALUE.md", 96.0)
```

## Example Workflow

### Initial State (No Learning)
```
Query: "negative value detected"
Prediction: services/logitrack/NEGATIVE_VALUE.md
Confidence: 75.0%  ← Base TF-IDF + BM25 score
```

### After User Confirms (Correct)
```
Feedback recorded:
  Success rate: 100% (1/1)
  Doc accuracy: 100% (1/1)
  Engine accuracy: 100% (1/1)

Next similar query: "negative value error"
Confidence: 85.0%  ← Boosted +10 points
```

### After 5 Correct Predictions
```
Success rate: 100% (5/5)
Doc accuracy: 100% (15/15)
Engine accuracy: 92% (23/25)

Similar query: "found negative value"
Confidence: 95.0%  ← High confidence from pattern learning
```

### After 1 Incorrect Prediction
```
Query: "negative value in response"
Predicted: services/logitrack/NEGATIVE_VALUE.md
Actual: services/meteo-il/MISSING_FIELD.md (user corrects)

Success rate: 83% (5/6)  ← Smooth decrease
Next similar query confidence: 78.0%  ← Slightly reduced
```

### After Learning Pattern
```
Query: "negative number found"
System recognizes similarity to known good pattern
Confidence: 96.0%  ← Direct lookup from feedback system
Speed: < 5ms  ← Bypasses full search
```

## Configuration

### Learning Rate (α)
```python
FeedbackLoop(learning_rate=0.1)
```
- **Low (0.05)**: Slow learning, stable over time
- **Medium (0.1)**: Balanced (recommended)
- **High (0.2)**: Fast adaptation, may be volatile

### Confidence Boost/Penalty
```python
FeedbackLoop(
    confidence_boost=5.0,    # Points to add for correct
    confidence_penalty=10.0  # Points to subtract for incorrect
)
```
- Adjust based on desired sensitivity
- Higher values = more aggressive learning

## Statistics & Monitoring

### Get Comprehensive Stats
```python
stats = feedback_loop.get_statistics()

# Returns:
{
    'total_feedback': 150,
    'correct_predictions': 138,
    'overall_accuracy': 0.92,
    'unique_queries': 45,
    'unique_documents': 12,
    'engine_stats': {
        'HYBRID_CUSTOM': {
            'predictions': 100,
            'correct': 92,
            'incorrect': 8,
            'accuracy': 0.92,
            'weight': 0.95
        }
    },
    'top_documents': [
        {
            'document': 'services/logitrack/NEGATIVE_VALUE.md',
            'accuracy': 0.98,
            'times_shown': 50,
            'times_correct': 49
        }
    ]
}
```

### Get Engine Weights (for Ensemble)
```python
weights = feedback_loop.get_engine_weights()

# Returns:
{
    'CUSTOM_TFIDF': 0.30,
    'ENHANCED_CUSTOM': 0.33,
    'HYBRID_CUSTOM': 0.37  ← Best performing
}
```

## Integration with Search Engines

The feedback loop is **automatically integrated** into `HybridCustomSearchEngine`:

```python
# In find_relevant_doc():
# 1. Check for known good matches first
feedback_result = self._check_feedback(query_text)
if feedback_result:
    return feedback_result  # Return 95%+ confidence

# 2. Perform normal search
doc_path, confidence = normal_search(query_text)

# 3. Adjust confidence based on history
adjusted_confidence = feedback_loop.adjust_confidence(
    query_text, doc_path, confidence, 'HYBRID_CUSTOM'
)

# 4. Record prediction for future learning
feedback_loop.record_prediction(
    query_text, doc_path, adjusted_confidence, 'HYBRID_CUSTOM'
)

return doc_path, adjusted_confidence
```

### teach_correction() Integration
```python
# When user corrects a prediction:
hybrid_custom.teach_correction(error_text, correct_doc_path)

# Automatically:
# 1. Records feedback (correct/incorrect)
# 2. Updates success rates
# 3. Saves to MongoDB
# 4. Updates feedback system
```

## Benefits

### 1. **Improved Accuracy Over Time**
- System learns from every correction
- Confidence becomes more reliable
- Reduces user correction frequency

### 2. **Faster for Repeated Queries**
- Direct lookup for known patterns (< 5ms)
- No need to recompute full search
- High confidence for validated results

### 3. **Transparent Learning**
- All statistics available via API
- Can inspect what system has learned
- Understand why confidence changed

### 4. **Adaptive to Changes**
- Handles new document additions
- Adjusts to changing query patterns
- No retraining required

### 5. **Multi-Engine Optimization**
- Learns which engine works best
- Automatically adjusts ensemble weights
- No manual tuning needed

## File Storage

Feedback data is persisted to MongoDB:

**Database**: `error_classifier` (configurable)

**Collections**:
- `predictions`: All predictions made by the system
- `corrections`: User feedback (correct/incorrect)
- `query_doc_stats`: Success rates per query-document pair
- `engine_stats`: Performance metrics per search engine
- `document_stats`: Accuracy rates per document
- `query_patterns`: Learned query patterns

**Configuration**:
```bash
# Set in core/.env
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE=error_classifier
```

## Testing

Run the test suite:
```bash
cd core
python src/algorithms/feedback_loop.py
```

Expected output:
```
Testing Feedback Loop System
======================================================================

1. Recording Predictions...
2. Recording User Feedback...
3. Testing Confidence Adjustment...
4. Testing Best Document Lookup...
5. Engine Weights (for ensemble)...
6. Overall Statistics...
7. Testing MongoDB persistence...

✅ All feedback loop tests completed!
```

## Best Practices

### 1. **Start Conservative**
- Use default learning_rate=0.1
- Monitor accuracy for first 50-100 corrections
- Adjust parameters based on performance

### 2. **Persist Regularly**
- Feedback is auto-saved to MongoDB after each correction
- MongoDB handles persistence and backups
- Can query historical data for analytics

### 3. **Monitor Statistics**
- Check `/api/status` endpoint regularly
- Query MongoDB collections for detailed insights
- Investigate documents with poor performance

### 4. **Handle Edge Cases**
- System needs 2-3 corrections to start learning patterns
- Very rare queries won't get much boost
- Consider manual review for critical classifications

### 5. **Combine with Multi-Search**
- Use multi-search for high-stakes decisions
- Feedback loop works with all engines
- Compare adjusted vs original confidence

## Future Enhancements

Potential improvements:
- Context-aware learning (time, user, service)
- Active learning (suggest uncertain cases for review)
- Automatic parameter tuning
- A/B testing of different configurations
- Transfer learning between services

## Summary

The Feedback Loop system transforms the error classifier from a **static model** into an **adaptive, self-improving system**. It learns from every user interaction, automatically adjusting confidence scores and improving accuracy over time. All data is persistently stored in MongoDB for long-term learning and analytics.

**Key Achievement**: Reinforcement learning with persistent MongoDB storage!
