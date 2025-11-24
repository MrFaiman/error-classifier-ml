import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from constants import CHECKPOINT_DIR, DOCS_ROOT_DIR, DATASET_PATH, INPUT_EXAMPLES_PATH

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
        f"{DOCS_ROOT_DIR}\\services\\{row['Service'].lower()}\\{row['Error_Category']}.md", axis=1)

    df['combined_features'] = (
        df['Service'] + " " +
        df['Error_Category'] + " " +
        df['Raw_Input_Snippet'] + " " +
        df['Root_Cause']
    )

    return df

def build_model():
    text_clf = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), analyzer='word')), 
        ('clf', RandomForestClassifier(n_estimators=100, random_state=42)),
    ])
    return text_clf

def save_checkpoint(model):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"model_v1_{timestamp}.pkl"
    filepath = os.path.join(CHECKPOINT_DIR, filename)
    
    joblib.dump(model, filepath)
    print(f"\n[Checkpoint] Model saved successfully to: {filepath}")
    
    latest_path = os.path.join(CHECKPOINT_DIR, "latest_model.pkl")
    joblib.dump(model, latest_path)

def load_latest_checkpoint():
    latest_path = os.path.join(CHECKPOINT_DIR, "latest_model.pkl")
    if os.path.exists(latest_path):
        print(f"\n[Checkpoint] Loading latest model from: {latest_path}")
        return joblib.load(latest_path)
    else:
        return None

FORCE_RETRAIN = True 

model = None

if not FORCE_RETRAIN:
    model = load_latest_checkpoint()

if model is None:
    print("Starting Training Session...")
    df = load_and_prep_data(DATASET_PATH)
    model = build_model()
    model.fit(df['combined_features'], df['target_doc'])
    print("Training Complete.")
    
    save_checkpoint(model)

def classify_error(log_line_dict):
    input_text = f"{log_line_dict['Service']} {log_line_dict['Error_Category']} {log_line_dict['Raw_Input_Snippet']}"
    
    prediction = model.predict([input_text])[0]
    probs = model.predict_proba([input_text])
    confidence = np.max(probs) * 100
    
    return prediction, confidence

if os.path.exists(INPUT_EXAMPLES_PATH):
    with open(INPUT_EXAMPLES_PATH, 'r', encoding='utf-8') as f:
        new_errors = json.load(f)

    print("\n--- Running Inference ---")
    for new_error in new_errors:
        doc_path, conf = classify_error(new_error)

        print(f"Input Snippet: {new_error['Raw_Input_Snippet']}")
        print(f"AI Classification: {doc_path}")
        print(f"Confidence Level: {conf:.2f}%")
        print("-" * 30)
else:
    print(f"No {INPUT_EXAMPLES_PATH} found to test.")