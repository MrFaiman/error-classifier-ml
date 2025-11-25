import os
import glob
import numpy as np
import pandas as pd
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from constants import EMBEDDING_MODEL, DOCS_ROOT_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from device_utils import get_best_device

class DocumentationSearchEngine:
    def __init__(self, docs_root_dir=None, model_name=None, chunk_size=None, chunk_overlap=None):
        if docs_root_dir is None:
            docs_root_dir = DOCS_ROOT_DIR
        self.docs_root_dir = docs_root_dir
        if model_name is None:
            model_name = EMBEDDING_MODEL
        if chunk_size is None:
            chunk_size = CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = CHUNK_OVERLAP
        
        device = get_best_device()
        print(f"Loading Embedding Model ({model_name}) on {device.upper()}...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Configure text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.vectorstore = None
        self.feedback_store = None  # Separate store for user corrections
        self.feedback_corrections = {}  # Map error text to correct doc path
        self.doc_chunks = []
        
        self._index_documents()
        self._init_feedback_store()

    def _index_documents(self):
        print("Indexing documentation files with chunking...")
        all_documents = []
        
        search_pattern = os.path.join(self.docs_root_dir, '**', '*.md')
        files = glob.glob(search_pattern, recursive=True)
        
        if not files:
            print(f"[Warning] No markdown files found in {self.docs_root_dir}")
            return

        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create a Document object with metadata
                filename = os.path.basename(filepath)
                service = os.path.basename(os.path.dirname(filepath))
                
                doc = Document(
                    page_content=content,
                    metadata={
                        'source': filepath,
                        'filename': filename,
                        'service': service,
                    }
                )
                
                # Split document into chunks
                chunks = self.text_splitter.split_documents([doc])
                
                # Add filename context to each chunk for better retrieval
                for chunk in chunks:
                    chunk.page_content = f"File: {filename}\nService: {service}\n\n{chunk.page_content}"
                
                all_documents.extend(chunks)
                
            except Exception as e:
                print(f"[Warning] Failed to process {filepath}: {e}")
                continue
        
        if all_documents:
            # Create FAISS vectorstore from documents
            self.vectorstore = FAISS.from_documents(all_documents, self.embeddings)
            print(f"Indexed {len(files)} documents into {len(all_documents)} chunks successfully.")
        else:
            print("[Error] No documents were successfully indexed.")
    
    def _init_feedback_store(self):
        """Initialize empty feedback store for user corrections"""
        self.feedback_corrections = {}
        print("Feedback system initialized for Semantic Search")

    def find_relevant_doc(self, error_snippet, top_k=1):
        if self.vectorstore is None:
            return "No docs indexed", 0.0
        
        # Step 1: Check feedback corrections first
        if self.feedback_store is not None:
            try:
                feedback_results = self.feedback_store.similarity_search_with_score(error_snippet, k=1)
                if feedback_results:
                    feedback_doc, feedback_score = feedback_results[0]
                    # Use stricter threshold for feedback (0.3)
                    if feedback_score < 0.3:
                        feedback_path = feedback_doc.metadata.get('correct_doc_path', '')
                        if feedback_path:
                            similarity_percentage = max(0, (1 - feedback_score / 2) * 100)
                            print(f"[Semantic Search] Using learned correction (score: {similarity_percentage:.2f}%)")
                            return feedback_path, similarity_percentage
            except Exception as e:
                # Feedback store might be empty or not initialized
                pass

        # Step 2: Perform standard similarity search
        results = self.vectorstore.similarity_search_with_score(error_snippet, k=top_k)
        
        if not results:
            return "No match found", 0.0
        
        # Get the best result
        best_doc, best_score = results[0]
        best_doc_path = best_doc.metadata.get('source', 'Unknown')
        
        # Convert distance to similarity percentage (lower distance = higher similarity)
        # FAISS returns L2 distance, so we convert it to a similarity score
        similarity_percentage = max(0, (1 - best_score / 2) * 100)
        
        return best_doc_path, similarity_percentage
    
    def teach_correction(self, error_text, correct_doc_path):
        """Learn from user correction"""
        correction_id = f"correction_{uuid.uuid4().hex[:8]}"
        
        print(f"[Semantic Search] Learning correction...")
        
        # Create a document for the feedback
        feedback_doc = Document(
            page_content=error_text,
            metadata={
                'correct_doc_path': correct_doc_path,
                'added_by': 'user',
                'timestamp': pd.Timestamp.now().isoformat(),
                'correction_id': correction_id
            }
        )
        
        # Add to feedback store
        if self.feedback_store is None:
            self.feedback_store = FAISS.from_documents([feedback_doc], self.embeddings)
        else:
            # Add to existing store
            temp_store = FAISS.from_documents([feedback_doc], self.embeddings)
            self.feedback_store.merge_from(temp_store)
        
        # Also store in simple dict for quick lookup
        self.feedback_corrections[error_text] = correct_doc_path
        
        print(f"[Semantic Search] Correction learned: {correct_doc_path}")
    
    def find_relevant_chunks(self, error_snippet, top_k=3):
        """Find the most relevant document chunks for an error snippet"""
        if self.vectorstore is None:
            return []

        results = self.vectorstore.similarity_search_with_score(error_snippet, k=top_k)
        
        return [
            {
                'content': doc.page_content,
                'source': doc.metadata.get('source', 'Unknown'),
                'filename': doc.metadata.get('filename', 'Unknown'),
                'service': doc.metadata.get('service', 'Unknown'),
                'score': max(0, (1 - score / 2) * 100)
            }
            for doc, score in results
        ]


if __name__ == "__main__":
    search_engine = DocumentationSearchEngine()

    test_errors = [
        "signal_strength: 999 (Sensor overload)", 
        "base_id: 'DROP TABLE users' (SQL Injection attempt)",
        "lat: 95.0 (GPS coordinates out of range)",
        "Please delete the duplicate item (User comment)"
    ]

    print("\n" + "="*70)
    print("SEMANTIC SEARCH WITH LANGCHAIN CHUNKING")
    print("="*70)
    
    for error_text in test_errors:
        print(f"\nError: '{error_text}'")
        doc_path, confidence = doc_search_engine.find_relevant_doc(error_text)
        
        print(f"Matched Doc: {doc_path}")
        print(f"Similarity Score: {confidence:.2f}%")
        
        # Show top relevant chunks
        print(f"\nTop 3 Relevant Chunks:")
        chunks = search_engine.find_relevant_chunks(error_text, top_k=3)
        for i, chunk in enumerate(chunks, 1):
            print(f"  {i}. [{chunk['service']}] {chunk['filename']} (Score: {chunk['score']:.2f}%)")
            print(f"     {chunk['content'][:100]}...")
        
        print("-" * 70)