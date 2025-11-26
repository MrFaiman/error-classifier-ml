import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from constants import CHECKPOINT_DIR, DOCS_ROOT_DIR, DATASET_PATH, INPUT_EXAMPLES_PATH

# Use custom ML implementations
from custom_ml import TfidfVectorizer
from search_engines import CustomTfidfSearchEngine, EnhancedCustomSearchEngine

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def load_and_prep_data(csv_path):
    """Load the CSV"""
    records = []
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")
        
    with open(csv_path, encoding='utf-8') as fh:
        header = fh.readline().strip().split(',')
        for line_number, line in enumerate(fh, start=2):
            raw_line = line.rstrip('\n')
            if not raw_line:
                continue
            base_parts = raw_line.split(',', 3)
            if len(base_parts) < 4:
                print(f"[Warning] Line {line_number} skipped (malformed)")
                continue
            try:
                raw_snippet, root_cause = base_parts[3].rsplit(',', 1)
            except ValueError as exc:
                print(f"[Warning] Line {line_number} skipped (missing root cause)")
                continue
            row_values = base_parts[:3] + [raw_snippet.strip(), root_cause.strip()]
            records.append(row_values)
    
    df = pd.DataFrame(records, columns=header)

    df['target_doc'] = df.apply(lambda row:
        os.path.join(DOCS_ROOT_DIR, row['Service'].lower(), f"{row['Error_Category']}.md"), axis=1)

    # Include Service and Category in features for better classification accuracy
    # API will only accept error_message, but model uses full context
    df['combined_features'] = (
        df['Service'] + " " +
        df['Error_Category'] + " " +
        df['Raw_Input_Snippet'] + " " +
        df['Root_Cause']
    )

    return df

def build_model():
    """
    Build a custom TF-IDF based classifier
    Note: This is now replaced by CustomTfidfSearchEngine for actual classification
    This function is kept for backward compatibility
    """
    print("[INFO] Using CustomTfidfSearchEngine - No blackbox ML libraries!")
    return None

def save_checkpoint(model):
    """
    Checkpointing is no longer needed with custom search engines
    They automatically index documents on initialization
    """
    print("[INFO] Custom search engines don't require checkpointing - they index on startup")
    pass

def load_latest_checkpoint():
    """
    No longer needed - custom search engines initialize directly
    """
    return None

FORCE_RETRAIN = False  # No longer relevant with custom search engines

# Initialize custom search engines
print("\n=== Initializing Custom ML Search Engines ===")
print("100% Custom Implementation - No Blackbox Libraries!")

custom_tfidf = None
enhanced_custom = None

try:
    custom_tfidf = CustomTfidfSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
    print("[OK] Custom TF-IDF initialized")
except Exception as e:
    print(f"[ERROR] Custom TF-IDF failed: {e}")

try:
    enhanced_custom = EnhancedCustomSearchEngine(docs_root_dir=DOCS_ROOT_DIR)
    print("[OK] Enhanced Custom Search initialized")
except Exception as e:
    print(f"[ERROR] Enhanced Custom Search failed: {e}")

def classify_error(error_message, use_enhanced=False):
    """
    Classify an error using custom ML implementations
    
    Args:
        error_message: The error text to classify
        use_enhanced: If True, use Enhanced Custom (all algorithms), else use Custom TF-IDF
    
    Returns:
        (doc_path, confidence)
    """
    if use_enhanced and enhanced_custom:
        return enhanced_custom.find_relevant_doc(error_message)
    elif custom_tfidf:
        return custom_tfidf.find_relevant_doc(error_message)
    else:
        raise RuntimeError("No search engine available")

if os.path.exists(INPUT_EXAMPLES_PATH):
    with open(INPUT_EXAMPLES_PATH, 'r', encoding='utf-8') as f:
        new_errors = json.load(f)

    # Test both custom search engines
    print("\n=== Testing Custom Search Engines ===\n")
    
    # Test Custom TF-IDF
    if custom_tfidf:
        print("--- Custom TF-IDF Results ---")
        for new_error in new_errors:
            try:
                doc_path, confidence = custom_tfidf.find_relevant_doc(new_error['Raw_Input_Snippet'])
                print(f"Input: {new_error['Raw_Input_Snippet']}")
                print(f"Classification: {doc_path}")
                print(f"Confidence: {confidence:.2f}%")
                print("-" * 50)
            except Exception as e:
                print(f"Error classifying: {e}")
    
    # Test Enhanced Custom
    if enhanced_custom:
        print("\n--- Enhanced Custom Search Results ---")
        for new_error in new_errors:
            try:
                doc_path, confidence = enhanced_custom.find_relevant_doc(new_error['Raw_Input_Snippet'])
                print(f"Input: {new_error['Raw_Input_Snippet']}")
                print(f"Classification: {doc_path}")
                print(f"Confidence: {confidence:.2f}%")
                print("-" * 50)
            except Exception as e:
                print(f"Error classifying: {e}")
else:
    print(f"\nNo {INPUT_EXAMPLES_PATH} found to test.")
    print("Custom search engines are ready for API use.")