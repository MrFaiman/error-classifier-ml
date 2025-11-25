import os
import glob
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from constants import EMBEDDING_MODEL, DOCS_ROOT_DIR, CHUNK_SIZE, CHUNK_OVERLAP

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
        
        print(f"Loading Embedding Model ({model_name})...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
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
        self.doc_chunks = []
        
        self._index_documents()

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

    def find_relevant_doc(self, error_snippet, top_k=1):
        if self.vectorstore is None:
            return "No docs indexed", 0.0

        # Perform similarity search
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
        print(f"\n📝 Error: '{error_text}'")
        doc_path, confidence = search_engine.find_relevant_doc(error_text)
        
        print(f"📁 Matched Doc: {doc_path}")
        print(f"💯 Similarity Score: {confidence:.2f}%")
        
        # Show top relevant chunks
        print(f"\n🔍 Top 3 Relevant Chunks:")
        chunks = search_engine.find_relevant_chunks(error_text, top_k=3)
        for i, chunk in enumerate(chunks, 1):
            print(f"  {i}. [{chunk['service']}] {chunk['filename']} (Score: {chunk['score']:.2f}%)")
            print(f"     {chunk['content'][:100]}...")
        
        print("-" * 70)