#!/usr/bin/env python3
"""
Demo script for NLU Error Classifier
Shows intent classification, entity extraction, and semantic search
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from algorithms import NLUErrorClassifier, SemanticNLUSearch
from constants import DOCS_ROOT_DIR
import glob
import os


def demo_intent_classification():
    """Demo: Intent classification"""
    print("\n" + "=" * 70)
    print("DEMO 1: Intent Classification")
    print("=" * 70)
    
    # Initialize NLU (lightweight mode - no heavy models for demo)
    nlu = NLUErrorClassifier(use_zero_shot=False, use_ner=False)
    
    test_cases = [
        "quantity: -5 validation failed",
        "sensor_id field is missing from request",
        "expected number but got string '100'",
        "SQL injection attempt detected: OR 1=1",
        "latitude value 91.5 exceeds valid range",
        "timestamp format invalid: 24/11/2025",
        "status must be one of: ACTIVE, INACTIVE, PENDING",
        "XSS attempt: <script>alert('hack')</script>",
        "temperature sensor offline - no data received",
        "signal_strength: 999 out of range (0-100)"
    ]
    
    print("\nClassifying error intents:\n")
    for error in test_cases:
        intent, confidence = nlu.classify_intent(error)
        print(f"Error: {error}")
        print(f"  → Intent: {intent.upper()} (confidence: {confidence:.2%})")
        print()


def demo_entity_extraction():
    """Demo: Entity extraction"""
    print("\n" + "=" * 70)
    print("DEMO 2: Entity Extraction")
    print("=" * 70)
    
    nlu = NLUErrorClassifier(use_zero_shot=False, use_ner=False)
    
    test_cases = [
        "quantity: -5 validation failed for item_id '12345'",
        "sensor reading 999 exceeds maximum threshold of 100",
        "user_id field is null but email='test@example.com'",
        "latitude: 91.5 and longitude: 200 are out of bounds",
        "price cannot be negative, received: -50.75"
    ]
    
    print("\nExtracting entities from errors:\n")
    for error in test_cases:
        entities = nlu.extract_entities(error)
        print(f"Error: {error}")
        print(f"  Fields found: {entities['fields']}")
        print(f"  Numbers: {entities['numbers']}")
        print(f"  Values: {entities['values']}")
        print(f"  Keywords: {entities['keywords']}")
        print()


def demo_category_prediction():
    """Demo: Category prediction"""
    print("\n" + "=" * 70)
    print("DEMO 3: Category Prediction")
    print("=" * 70)
    
    nlu = NLUErrorClassifier(use_zero_shot=False, use_ner=False)
    
    test_cases = [
        ("quantity: -5 is not allowed", "NEGATIVE_VALUE"),
        ("user_id field is missing from payload", "MISSING_FIELD"),
        ("expected integer but got string", "TYPE_MISMATCH"),
        ("latitude 95.0 is out of valid range", "GEO_OUT_OF_BOUNDS"),
        ("timestamp format should be ISO-8601", "INVALID_DATE"),
        ("status 'UNKNOWN' not in enum list", "INVALID_ENUM"),
        ("transponder code does not match pattern", "REGEX_MISMATCH"),
        ("SQL injection detected in query", "SECURITY_ALERT"),
    ]
    
    print("\nPredicting error categories:\n")
    correct = 0
    for error, expected in test_cases:
        predicted, confidence = nlu.predict_category(error)
        match = "✓" if predicted == expected else "✗"
        if predicted == expected:
            correct += 1
        
        print(f"{match} Error: {error}")
        print(f"  Expected: {expected}")
        print(f"  Predicted: {predicted} (confidence: {confidence:.2%})")
        print()
    
    accuracy = correct / len(test_cases)
    print(f"Accuracy: {correct}/{len(test_cases)} = {accuracy:.1%}")


def demo_full_analysis():
    """Demo: Complete NLU analysis"""
    print("\n" + "=" * 70)
    print("DEMO 4: Complete NLU Analysis")
    print("=" * 70)
    
    nlu = NLUErrorClassifier(use_zero_shot=False, use_ner=False)
    
    error = "sensor_id: 'SNS-001' reported signal_strength: 999 which exceeds valid range (0-100)"
    
    print(f"\nAnalyzing error message:")
    print(f"  \"{error}\"\n")
    
    analysis = nlu.analyze_error(error)
    
    print("Analysis Results:")
    print(f"  Intent: {analysis['intent']} ({analysis['intent_confidence']:.2%})")
    print(f"  Category: {analysis['category']} ({analysis['category_confidence']:.2%})")
    print(f"  NLU Score: {analysis['nlu_score']:.2%}")
    print(f"\n  Entities:")
    print(f"    Fields: {analysis['entities']['fields']}")
    print(f"    Numbers: {analysis['entities']['numbers']}")
    print(f"    Values: {analysis['entities']['values']}")
    print(f"    Keywords: {analysis['entities']['keywords']}")


def demo_semantic_search():
    """Demo: Semantic search with sentence transformers"""
    print("\n" + "=" * 70)
    print("DEMO 5: Semantic Search (requires sentence-transformers)")
    print("=" * 70)
    
    try:
        import sentence_transformers
    except ImportError:
        print("\n⚠️  sentence-transformers not installed")
        print("Install with: pip install sentence-transformers")
        print("Skipping semantic search demo")
        return
    
    # Initialize semantic search
    semantic = SemanticNLUSearch(model_name='all-MiniLM-L6-v2')
    
    # Load documentation
    print("\nLoading documentation files...")
    search_pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
    files = glob.glob(search_pattern, recursive=True)
    
    documents = []
    doc_paths = []
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append(content)
                doc_paths.append(filepath)
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}")
    
    print(f"Found {len(documents)} documents")
    
    # Index documents
    semantic.index_documents(documents, doc_paths)
    
    # Test semantic search
    test_queries = [
        "sensor value too high",
        "data field not present",
        "wrong data type received",
        "coordinate outside valid area"
    ]
    
    print("\nSemantic Search Results:\n")
    for query in test_queries:
        print(f"Query: '{query}'")
        results = semantic.search(query, top_k=3)
        for i, (path, score) in enumerate(results, 1):
            filename = os.path.basename(path)
            print(f"  {i}. {filename} (similarity: {score:.3f})")
        print()


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("NLU Error Classifier - Demo Suite")
    print("Natural Language Understanding for Error Classification")
    print("=" * 70)
    
    try:
        demo_intent_classification()
        demo_entity_extraction()
        demo_category_prediction()
        demo_full_analysis()
        demo_semantic_search()
        
        print("\n" + "=" * 70)
        print("✅ All demos completed!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
