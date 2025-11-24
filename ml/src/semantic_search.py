import os
import glob
import torch
from sentence_transformers import SentenceTransformer, util
from constants import EMBEDDING_MODEL, DOCS_ROOT_DIR

class DocumentationSearchEngine:
    def __init__(self, docs_root_dir=None, model_name=None):
        if docs_root_dir is None:
            docs_root_dir = DOCS_ROOT_DIR
        self.docs_root_dir = docs_root_dir
        if model_name is None:
            model_name = EMBEDDING_MODEL
        print(f"Loading Embedding Model ({model_name})...")
        self.model = SentenceTransformer(model_name)
        
        self.doc_paths = []
        self.doc_embeddings = None

        self._index_documents()

    def _index_documents(self):
        print("Indexing documentation files...")
        doc_contents = []
        
        search_pattern = os.path.join(self.docs_root_dir, '**', '*.md')
        files = glob.glob(search_pattern, recursive=True)
        
        if not files:
            print(f"[Warning] No markdown files found in {self.docs_root_dir}")
            return

        for filepath in files:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.doc_paths.append(filepath)
            
            combined_text = f"Filename: {os.path.basename(filepath)}\nContent: {content}"
            doc_contents.append(combined_text)

        self.doc_embeddings = self.model.encode(doc_contents, convert_to_tensor=True)
        print(f"Indexed {len(self.doc_paths)} documents successfully.")

    def find_relevant_doc(self, error_snippet, top_k=1):
        if self.doc_embeddings is None:
            return "No docs indexed", 0.0

        query_embedding = self.model.encode(error_snippet, convert_to_tensor=True)

        cos_scores = util.cos_sim(query_embedding, self.doc_embeddings)[0]

        top_result = torch.topk(cos_scores, k=top_k)
        
        best_score = top_result.values[0].item()
        best_idx = top_result.indices[0].item()
        best_doc_path = self.doc_paths[best_idx]

        return best_doc_path, best_score * 100


if __name__ == "__main__":
    search_engine = DocumentationSearchEngine()

    test_errors = [
        "signal_strength: 999 (Sensor overload)", 
        "base_id: 'DROP TABLE users' (SQL Injection attempt)",
        "lat: 95.0 (GPS coordinates out of range)",
        "Please delete the duplicate item (User comment)"
    ]

    print("\n--- Semantic Search Results ---")
    for error_text in test_errors:
        doc_path, confidence = search_engine.find_relevant_doc(error_text)
        
        print(f"Error: '{error_text}'")
        print(f"--> Matched Doc: {doc_path}")
        print(f"--> Similarity Score: {confidence:.2f}%")
        print("-" * 30)