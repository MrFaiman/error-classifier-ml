import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os
from constants import DATASET_PATH, DOCS_ROOT_DIR, EMBEDDING_MODEL, CHROMA_DB_DIR

class VectorKnowledgeBase:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = CHROMA_DB_DIR
        self.client = chromadb.PersistentClient(path=db_path)
        
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        
        self.docs_col = self.client.get_or_create_collection(
            name="official_docs",
            embedding_function=self.embedding_fn
        )
        
        self.feedback_col = self.client.get_or_create_collection(
            name="learned_feedback",
            embedding_function=self.embedding_fn
        )

    def populate_initial_knowledge(self, csv_path):
        if self.docs_col.count() > 0:
            print("Knowledge base already populated. Skipping.")
            return

        print(f"Ingesting data from {csv_path}...")
        
        ids = []
        documents = []
        metadatas = []

        try:
            with open(csv_path, 'r', encoding='utf-8') as fh:
                # Skip the header line
                header = fh.readline()
                
                for line_number, line in enumerate(fh, start=2):
                    raw_line = line.rstrip('\n')
                    if not raw_line:
                        continue
                    
                    # 1. Manual parsing logic (like in load_and_prep_data)
                    # Split only on the first 3 commas: Timestamp, Service, Error_Category
                    base_parts = raw_line.split(',', 3)
                    
                    if len(base_parts) < 4:
                        print(f"[Warning] Line {line_number} skipped (malformed structure)")
                        continue
                        
                    # The fourth part contains the Snippet and the Root Cause
                    # We split from the end (rsplit) once to separate the cause
                    try:
                        raw_snippet, root_cause = base_parts[3].rsplit(',', 1)
                    except ValueError:
                        print(f"[Warning] Line {line_number} skipped (missing root cause)")
                        continue

                    timestamp = base_parts[0].strip()
                    service = base_parts[1].strip()
                    category = base_parts[2].strip()
                    clean_snippet = raw_snippet.strip()
                    clean_cause = root_cause.strip()

                    # Create multiple embeddings for better partial matching
                    # 1. Full error log
                    full_text = f"{service} {category} {clean_snippet} {clean_cause}"
                    ids.append(f"err_{line_number}_full")
                    documents.append(full_text)
                    metadatas.append({
                        "service": service,
                        "category": category,
                        "doc_path": f"{DOCS_ROOT_DIR}/{service.lower()}/{category}.md",
                        "root_cause": clean_cause,
                        "raw_snippet": clean_snippet,
                        "match_type": "full"
                    })
                    
                    # 2. Just root cause (for when users search by error message only)
                    ids.append(f"err_{line_number}_cause")
                    documents.append(clean_cause)
                    metadatas.append({
                        "service": service,
                        "category": category,
                        "doc_path": f"{DOCS_ROOT_DIR}/{service.lower()}/{category}.md",
                        "root_cause": clean_cause,
                        "raw_snippet": clean_snippet,
                        "match_type": "cause_only"
                    })
                    
                    # 3. Just raw snippet (for when users search by technical data only)
                    ids.append(f"err_{line_number}_snippet")
                    documents.append(f"{service} {category} {clean_snippet}")
                    metadatas.append({
                        "service": service,
                        "category": category,
                        "doc_path": f"{DOCS_ROOT_DIR}/{service.lower()}/{category}.md",
                        "root_cause": clean_cause,
                        "raw_snippet": clean_snippet,
                        "match_type": "snippet_only"
                    })

            if ids:
                self.docs_col.add(ids=ids, documents=documents, metadatas=metadatas)
                print(f"Indexed {len(ids)} variations (Original records: {line_number}).")

        except Exception as e:
            print(f"Error: {e}")

    def search(self, error_query, threshold=0.3):
        print(f"\n--- Analyzing: '{error_query}' ---")
        
        # Step 1: Check dynamic memory (Feedback)
        # We look for the single best result
        feedback_results = self.feedback_col.query(
            query_texts=[error_query],
            n_results=1
        )
        
        # Check if something relevant was found (Low Distance = High Similarity)
        # In Chroma, the distance is L2 or Cosine. Default is L2: lower is better.
        # Assume a distance less than 0.5 is a good match.
        if feedback_results['ids'][0]:
            distance = feedback_results['distances'][0][0]
            if distance < 0.4: # Strict threshold for feedback
                metadata = feedback_results['metadatas'][0][0]
                return {
                    "source": "LEARNED_MEMORY (Feedback)",
                    "doc_path": metadata['correct_doc_path'],
                    "confidence": "High",
                    "reason": "Previous user correction matched"
                }

        # Step 2: If no feedback, search in official knowledge base
        doc_results = self.docs_col.query(
            query_texts=[error_query],
            n_results=1
        )
        
        if doc_results['ids'][0]:
            metadata = doc_results['metadatas'][0][0]
            return {
                "source": "OFFICIAL_KNOWLEDGE",
                "doc_path": metadata['doc_path'],
                "confidence": "Normal",
                "root_cause": metadata['root_cause']
            }
            
        return {"source": "UNKNOWN", "doc_path": "N/A"}

    def teach_system(self, error_text, correct_doc_path):
        import uuid
        
        correction_id = f"fix_{uuid.uuid4().hex[:8]}"
        
        print(f"[Learning] Saving correction to Vector DB...")
        
        self.feedback_col.add(
            ids=[correction_id],
            documents=[error_text],
            metadatas=[{
                "correct_doc_path": correct_doc_path,
                "added_by": "user",
                "timestamp": pd.Timestamp.now().isoformat()
            }]
        )
        print("Knowledge updated instantly.")

def initialize_vector_db():
    """Initialize the vector database and populate with training data if needed."""
    print("Initializing Vector Database...")
    kb = VectorKnowledgeBase()
    
    if os.path.exists(DATASET_PATH):
        kb.populate_initial_knowledge(DATASET_PATH)
    else:
        print(f"Warning: Dataset not found at {DATASET_PATH}")
    
    return kb

if __name__ == "__main__":
    kb = initialize_vector_db()
    
    # Test search
    test_error = "User 'admin' tried DELETE on table 'inventory'"
    result = kb.search(test_error)
    print(f"\nTest Result: {result}")
