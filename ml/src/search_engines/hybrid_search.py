import os
import glob
import numpy as np
from rank_bm25 import BM25Okapi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from constants import EMBEDDING_MODEL, DOCS_ROOT_DIR, CHUNK_SIZE, CHUNK_OVERLAP


class HybridSearchEngine:
    """
    Hybrid search combining BM25 (keyword-based) and semantic search (embeddings).
    Provides best of both worlds: exact keyword matches + semantic similarity.
    """
    
    def __init__(self, docs_root_dir=None, model_name=None, chunk_size=None, chunk_overlap=None,
                 semantic_weight=0.5, bm25_weight=0.5):
        if docs_root_dir is None:
            docs_root_dir = DOCS_ROOT_DIR
        self.docs_root_dir = docs_root_dir
        if model_name is None:
            model_name = EMBEDDING_MODEL
        if chunk_size is None:
            chunk_size = CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = CHUNK_OVERLAP
            
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        
        print(f"Loading Hybrid Search Engine...")
        print(f"  - Semantic Weight: {semantic_weight}")
        print(f"  - BM25 Weight: {bm25_weight}")
        
        # Initialize embeddings for semantic search
        print(f"Loading Embedding Model ({model_name})...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Configure text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Storage for both search methods
        self.vectorstore = None  # FAISS for semantic search
        self.bm25 = None  # BM25 for keyword search
        self.documents = []  # Store documents for BM25
        self.doc_texts = []  # Store tokenized texts for BM25
        
        self._index_documents()
    
    def _index_documents(self):
        print("Indexing documentation files with hybrid search...")
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
                
                # Add context to each chunk
                for chunk in chunks:
                    chunk.page_content = f"File: {filename}\nService: {service}\n\n{chunk.page_content}"
                
                all_documents.extend(chunks)
                
            except Exception as e:
                print(f"[Warning] Failed to process {filepath}: {e}")
                continue
        
        if all_documents:
            # Store documents
            self.documents = all_documents
            
            # Create FAISS vectorstore for semantic search
            self.vectorstore = FAISS.from_documents(all_documents, self.embeddings)
            
            # Create BM25 index for keyword search
            # Tokenize documents for BM25
            self.doc_texts = [doc.page_content.lower().split() for doc in all_documents]
            self.bm25 = BM25Okapi(self.doc_texts)
            
            print(f"Indexed {len(files)} documents into {len(all_documents)} chunks.")
            print(f"  ✓ Semantic index (FAISS): Ready")
            print(f"  ✓ Keyword index (BM25): Ready")
        else:
            print("[Error] No documents were successfully indexed.")
    
    def _normalize_scores(self, scores):
        """Normalize scores to 0-1 range using min-max normalization"""
        if len(scores) == 0:
            return scores
        scores = np.array(scores)
        min_score = scores.min()
        max_score = scores.max()
        if max_score == min_score:
            return np.ones_like(scores)
        return (scores - min_score) / (max_score - min_score)
    
    def find_relevant_doc(self, error_snippet, top_k=1):
        """Find most relevant document using hybrid search"""
        if self.vectorstore is None or self.bm25 is None:
            return "No docs indexed", 0.0
        
        # 1. Semantic search with FAISS
        semantic_results = self.vectorstore.similarity_search_with_score(error_snippet, k=10)
        
        # 2. BM25 keyword search
        query_tokens = error_snippet.lower().split()
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # Get top BM25 results
        top_bm25_indices = np.argsort(bm25_scores)[::-1][:10]
        
        # 3. Combine scores
        # Create a dictionary to aggregate scores by document
        combined_scores = {}
        
        # Add semantic scores (convert distance to similarity)
        for doc, distance in semantic_results:
            doc_id = id(doc)
            semantic_score = max(0, (1 - distance / 2))  # Convert L2 distance to similarity
            combined_scores[doc_id] = {
                'doc': doc,
                'semantic': semantic_score,
                'bm25': 0,
                'combined': 0
            }
        
        # Add BM25 scores
        for idx in top_bm25_indices:
            doc = self.documents[idx]
            doc_id = id(doc)
            bm25_score = bm25_scores[idx]
            
            if doc_id in combined_scores:
                combined_scores[doc_id]['bm25'] = bm25_score
            else:
                combined_scores[doc_id] = {
                    'doc': doc,
                    'semantic': 0,
                    'bm25': bm25_score,
                    'combined': 0
                }
        
        # Normalize and combine scores
        semantic_scores_list = [v['semantic'] for v in combined_scores.values()]
        bm25_scores_list = [v['bm25'] for v in combined_scores.values()]
        
        normalized_semantic = self._normalize_scores(semantic_scores_list)
        normalized_bm25 = self._normalize_scores(bm25_scores_list)
        
        # Calculate combined scores
        for i, doc_id in enumerate(combined_scores.keys()):
            combined_scores[doc_id]['combined'] = (
                self.semantic_weight * normalized_semantic[i] +
                self.bm25_weight * normalized_bm25[i]
            )
        
        # Get top result
        best_match = max(combined_scores.values(), key=lambda x: x['combined'])
        best_doc = best_match['doc']
        best_score = best_match['combined'] * 100
        best_doc_path = best_doc.metadata.get('source', 'Unknown')
        
        return best_doc_path, best_score
    
    def find_relevant_chunks(self, error_snippet, top_k=3):
        """Find the most relevant document chunks using hybrid search"""
        if self.vectorstore is None or self.bm25 is None:
            return []
        
        # Similar to find_relevant_doc but return top_k results
        semantic_results = self.vectorstore.similarity_search_with_score(error_snippet, k=10)
        query_tokens = error_snippet.lower().split()
        bm25_scores = self.bm25.get_scores(query_tokens)
        top_bm25_indices = np.argsort(bm25_scores)[::-1][:10]
        
        combined_scores = {}
        
        for doc, distance in semantic_results:
            doc_id = id(doc)
            semantic_score = max(0, (1 - distance / 2))
            combined_scores[doc_id] = {
                'doc': doc,
                'semantic': semantic_score,
                'bm25': 0,
                'combined': 0
            }
        
        for idx in top_bm25_indices:
            doc = self.documents[idx]
            doc_id = id(doc)
            bm25_score = bm25_scores[idx]
            
            if doc_id in combined_scores:
                combined_scores[doc_id]['bm25'] = bm25_score
            else:
                combined_scores[doc_id] = {
                    'doc': doc,
                    'semantic': 0,
                    'bm25': bm25_score,
                    'combined': 0
                }
        
        semantic_scores_list = [v['semantic'] for v in combined_scores.values()]
        bm25_scores_list = [v['bm25'] for v in combined_scores.values()]
        
        normalized_semantic = self._normalize_scores(semantic_scores_list)
        normalized_bm25 = self._normalize_scores(bm25_scores_list)
        
        for i, doc_id in enumerate(combined_scores.keys()):
            combined_scores[doc_id]['combined'] = (
                self.semantic_weight * normalized_semantic[i] +
                self.bm25_weight * normalized_bm25[i]
            )
        
        # Get top_k results
        sorted_results = sorted(combined_scores.values(), key=lambda x: x['combined'], reverse=True)[:top_k]
        
        return [
            {
                'content': result['doc'].page_content,
                'source': result['doc'].metadata.get('source', 'Unknown'),
                'filename': result['doc'].metadata.get('filename', 'Unknown'),
                'service': result['doc'].metadata.get('service', 'Unknown'),
                'score': result['combined'] * 100,
                'semantic_score': result['semantic'] * 100,
                'bm25_score': result['bm25'],
            }
            for result in sorted_results
        ]


if __name__ == "__main__":
    hybrid_engine = HybridSearchEngine()

    test_errors = [
        "signal_strength: 999 (Sensor overload)", 
        "base_id: 'DROP TABLE users' (SQL Injection attempt)",
        "lat: 95.0 (GPS coordinates out of range)",
        "Please delete the duplicate item (User comment)"
    ]

    print("\n" + "="*70)
    print("HYBRID SEARCH (BM25 + Semantic)")
    print("="*70)
    
    for error_text in test_errors:
        print(f"\n📝 Error: '{error_text}'")
        doc_path, confidence = hybrid_engine.find_relevant_doc(error_text)
        
        print(f"📁 Matched Doc: {doc_path}")
        print(f"💯 Hybrid Score: {confidence:.2f}%")
        
        # Show top relevant chunks with breakdown
        print(f"\n🔍 Top 3 Relevant Chunks:")
        chunks = hybrid_engine.find_relevant_chunks(error_text, top_k=3)
        for i, chunk in enumerate(chunks, 1):
            print(f"  {i}. [{chunk['service']}] {chunk['filename']}")
            print(f"     Combined: {chunk['score']:.2f}% | Semantic: {chunk['semantic_score']:.2f}% | BM25: {chunk['bm25_score']:.2f}")
            print(f"     {chunk['content'][:80]}...")
        
        print("-" * 70)
