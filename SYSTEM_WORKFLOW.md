# Error Classification System - Workflow Documentation

## Overview

The Error Classification System processes error messages and matches them to relevant documentation using three different search engines. This document describes the complete workflow from data ingestion to result delivery.

---

## General System Workflow

### Phase 1: Data Preparation

```
[CSV Dataset] → [Parse & Load] → [Extract Features] → [Create Training Data]
     ↓
  Service, Error_Category, Raw_Input_Snippet, Root_Cause
     ↓
  Combined Features: "Service Error_Category Raw_Input_Snippet"
```

**Steps:**
1. **Load Dataset**: Read `data/dataset/errors_dataset.csv`
2. **Parse Records**: Extract service name, error category, error snippet, root cause
3. **Combine Features**: Concatenate service + category + snippet for rich context
4. **Map to Documentation**: Link each error type to its documentation file path

### Phase 2: Documentation Indexing

```
[Documentation Files] → [Read Content] → [Process Text] → [Generate Embeddings] → [Store in Index]
          ↓
    data/services/
    ├── logitrack/
    ├── meteo-il/
    └── skyguard/
          ↓
    [Vectorized Knowledge Base]
```

**Steps:**
1. **Scan Directory**: Recursively find all `.md` files in `data/services/`
2. **Read Content**: Load markdown content with metadata (filename, service, path)
3. **Text Processing**: 
   - Clean and normalize text
   - Split into chunks (for Semantic/Hybrid engines)
   - Add contextual metadata to chunks
4. **Generate Embeddings**: Convert text to dense vectors using Sentence Transformers
5. **Index Storage**: Store in appropriate database (ChromaDB, FAISS, BM25)

### Phase 3: Query Processing

```
[User Query] → [Preprocess] → [Search Engines] → [Aggregate Results] → [Return Best Match]
                                     ↓
                    ┌────────────────┼────────────────┐
                    ↓                ↓                ↓
              Vector DB        Semantic Search    Hybrid Search
                    ↓                ↓                ↓
              [Results]          [Results]        [Results]
                    └────────────────┼────────────────┘
                                     ↓
                            [Consensus/Voting]
                                     ↓
                            [Final Classification]
```

**Steps:**
1. **Receive Query**: Error message from user via API or CLI
2. **Preprocess**: Normalize text, extract key terms
3. **Route to Engines**: Query one or all search engines
4. **Execute Search**: Each engine performs similarity matching
5. **Aggregate**: Combine results if multi-engine mode enabled
6. **Return**: Best matching documentation with confidence score

### Phase 4: Feedback Learning

```
[User Feedback] → [Validate] → [Store Correction] → [Update Index] → [Improved Accuracy]
       ↓
 Negative Feedback + Correct Doc Path
       ↓
 [Feedback Collection]
       ↓
 ChromaDB: learned_feedback collection
 FAISS: feedback_store vectorstore
       ↓
 [Future Queries Check Feedback First]
```

**Steps:**
1. **Receive Feedback**: User indicates incorrect classification
2. **Collect Correction**: User provides correct documentation path
3. **Store in Feedback Store**: Add to engine-specific feedback collection
4. **Priority Search**: Future queries check feedback store first
5. **Continuous Improvement**: System accuracy increases over time

---

## Search Engine Workflows

### 1. Vector Database (ChromaDB) - Persistent Storage with Learning

```
┌─────────────────────────────────────────────────────────────────┐
│                     VECTOR DB WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

INITIALIZATION:
┌─────────────────┐
│ Start System    │
└────────┬────────┘
         ↓
┌─────────────────────────────────┐
│ Initialize ChromaDB Client      │
│ Path: ml/models/chroma_db/      │
└────────┬────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ Load/Create Collections:                    │
│ 1. official_docs (training data)           │
│ 2. learned_feedback (user corrections)     │
└────────┬────────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ Load Embedding Function         │
│ Model: sentence-transformers    │
└────────┬────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ Check if official_docs empty    │
└────────┬────────────────────────┘
         ↓
    YES  │  NO
         ↓  └─────────────────────┐
┌─────────────────────────────────┤
│ POPULATE KNOWLEDGE BASE         │
│                                 │
│ 1. Read CSV dataset            │
│ 2. For each row:               │
│    - Extract: Service,         │
│      Category, Snippet,        │
│      Root Cause                │
│    - Combine: "Service         │
│      Category Snippet"         │
│    - Map to doc path          │
│ 3. Batch add to ChromaDB      │
│ 4. Generate embeddings         │
│    (automatic)                 │
└────────┬────────────────────────┘
         ↓
         │←──────────────────────┘
         ↓
┌─────────────────────────────────┐
│ System Ready                    │
└─────────────────────────────────┘


SEARCH QUERY:
┌─────────────────┐
│ Receive Query   │
│ "error_text"    │
└────────┬────────┘
         ↓
┌──────────────────────────────────────────┐
│ STEP 1: Check Learned Feedback First    │
│                                          │
│ Query: learned_feedback.query(          │
│   query_texts=[error_text],            │
│   n_results=1                          │
│ )                                       │
└────────┬─────────────────────────────────┘
         ↓
    ┌────┴────┐
    │ Found?  │
    └────┬────┘
    YES  │  NO
         ↓  │
┌─────────────────────────┐  │
│ Check Distance < 0.4    │  │
└────────┬────────────────┘  │
    YES  │  NO               │
         ↓  │                │
┌──────────────────────┐    │
│ RETURN:              │    │
│ - Doc Path           │    │
│ - Confidence: High   │    │
│ - Source: Learned    │    │
└──────────────────────┘    │
                            │
         ←──────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ STEP 2: Query Official Knowledge Base   │
│                                          │
│ Query: official_docs.query(             │
│   query_texts=[error_text],            │
│   n_results=1                          │
│ )                                       │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Extract Best Match:                      │
│ - Document text                          │
│ - Metadata (doc_path)                   │
│ - Distance score                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Calculate Confidence:                    │
│ - Distance < 0.5: High                  │
│ - Distance < 1.0: Normal                │
│ - Distance >= 1.0: Low                  │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────┐
│ RETURN:              │
│ - Doc Path           │
│ - Confidence Score   │
│ - Source: Official   │
└──────────────────────┘


FEEDBACK LEARNING:
┌──────────────────────────────┐
│ Receive Correction:          │
│ - error_text                 │
│ - correct_doc_path           │
└────────┬─────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Create Feedback Record:                  │
│ {                                        │
│   'text': error_text,                   │
│   'correct_doc': correct_doc_path,      │
│   'timestamp': now(),                   │
│   'added_by': 'user'                    │
│ }                                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Add to learned_feedback Collection:      │
│                                          │
│ learned_feedback.add(                   │
│   documents=[error_text],               │
│   metadatas=[metadata],                 │
│   ids=[unique_id]                       │
│ )                                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Persist to Disk (Automatic)             │
│ Location: ml/models/chroma_db/          │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────┐
│ Learning Complete    │
│ Future queries will  │
│ check this first     │
└──────────────────────┘
```

**Key Features:**
- Persistent storage survives restarts
- Dual collection architecture (official + learned)
- Priority search: learned feedback checked first
- Distance-based confidence scoring
- Automatic embedding generation

---

### 2. Semantic Search (LangChain + FAISS) - Fast In-Memory with Chunking

```
┌─────────────────────────────────────────────────────────────────┐
│                   SEMANTIC SEARCH WORKFLOW                      │
└─────────────────────────────────────────────────────────────────┘

INITIALIZATION:
┌─────────────────┐
│ Start Engine    │
└────────┬────────┘
         ↓
┌──────────────────────────────────────────┐
│ Detect GPU Device:                       │
│ - Apple Silicon → MPS                   │
│ - NVIDIA GPU → CUDA                     │
│ - Fallback → CPU                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Load Embedding Model:                    │
│ HuggingFaceEmbeddings(                  │
│   model=EMBEDDING_MODEL,                │
│   device=detected_device                │
│ )                                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Initialize Text Splitter:                │
│ RecursiveCharacterTextSplitter(         │
│   chunk_size=500,                       │
│   chunk_overlap=50,                     │
│   separators=["\n\n", "\n", ". ", " "] │
│ )                                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ INDEX DOCUMENTS:                         │
│                                          │
│ 1. Scan data/services/**/*.md           │
│ 2. For each file:                       │
│    ┌──────────────────────────┐        │
│    │ Read markdown content    │        │
│    └──────────┬───────────────┘        │
│               ↓                         │
│    ┌──────────────────────────┐        │
│    │ Create Document object   │        │
│    │ with metadata:           │        │
│    │ - source (file path)    │        │
│    │ - filename              │        │
│    │ - service               │        │
│    └──────────┬───────────────┘        │
│               ↓                         │
│    ┌──────────────────────────┐        │
│    │ Split into chunks        │        │
│    │ (500 chars, 50 overlap) │        │
│    └──────────┬───────────────┘        │
│               ↓                         │
│    ┌──────────────────────────┐        │
│    │ Add context to chunk:    │        │
│    │ "File: {filename}        │        │
│    │  Service: {service}      │        │
│    │  {content}"             │        │
│    └──────────┬───────────────┘        │
│               ↓                         │
│    └──→ Collect all chunks             │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Create FAISS Vectorstore:                │
│                                          │
│ FAISS.from_documents(                   │
│   documents=all_chunks,                 │
│   embedding=embeddings                  │
│ )                                        │
│                                          │
│ Process:                                 │
│ - Generate embeddings for all chunks    │
│ - Build FAISS index (in-memory)        │
│ - Store document references             │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Initialize Feedback Store:               │
│ Create empty FAISS vectorstore          │
│ for future corrections                  │
└────────┬─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ System Ready                    │
│ Total Chunks: N                 │
│ Index Type: FAISS (In-Memory)  │
└─────────────────────────────────┘


SEARCH QUERY:
┌─────────────────┐
│ Receive Query   │
│ "error_text"    │
└────────┬────────┘
         ↓
┌──────────────────────────────────────────┐
│ STEP 1: Check Feedback Store             │
│                                          │
│ IF feedback_store exists:                │
│   results = feedback_store               │
│     .similarity_search_with_score(      │
│       error_text, k=1                   │
│     )                                    │
└────────┬─────────────────────────────────┘
         ↓
    ┌────┴────────┐
    │ Found &     │
    │ score < 0.3?│
    └────┬────────┘
    YES  │  NO
         ↓  │
┌──────────────────────────┐  │
│ Extract correction:      │  │
│ - service                │  │
│ - category               │  │
│ - confidence             │  │
└────────┬─────────────────┘  │
         ↓                    │
┌──────────────────────────┐  │
│ Find matching doc in     │  │
│ original documents       │  │
└────────┬─────────────────┘  │
         ↓                    │
┌──────────────────────┐      │
│ RETURN:              │      │
│ - Doc Path           │      │
│ - High Confidence    │      │
│ - Source: Learned    │      │
└──────────────────────┘      │
                              │
         ←────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ STEP 2: Main FAISS Search                │
│                                          │
│ results = vectorstore                    │
│   .similarity_search_with_score(        │
│     query=error_text,                   │
│     k=1                                  │
│   )                                      │
│                                          │
│ Process:                                 │
│ 1. Embed query text                     │
│ 2. Compute L2 distance to all chunks    │
│ 3. Return closest match                 │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Extract Result:                          │
│ - Document chunk                         │
│ - Metadata (source, filename, service)  │
│ - Distance score                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Convert Distance to Similarity:          │
│ similarity = (1 - distance/2) * 100     │
│                                          │
│ Examples:                                │
│ - distance=0.1 → 95% similarity         │
│ - distance=0.5 → 75% similarity         │
│ - distance=1.0 → 50% similarity         │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────┐
│ RETURN:              │
│ - Doc Path           │
│ - Similarity %       │
└──────────────────────┘


FEEDBACK LEARNING:
┌──────────────────────────────┐
│ Receive Correction:          │
│ - error_message              │
│ - correct_service            │
│ - correct_category           │
└────────┬─────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Generate Correction ID:                  │
│ correction_id = uuid4()                  │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Store Metadata:                          │
│ feedback_corrections[id] = {             │
│   'error_message': error_message,       │
│   'service': correct_service,           │
│   'category': correct_category,         │
│   'timestamp': now()                    │
│ }                                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Create Correction Document:              │
│ Document(                                │
│   page_content=                          │
│     f"Error: {error_message}\n"         │
│     f"Service: {service}\n"             │
│     f"Category: {category}",            │
│   metadata={                             │
│     'correction_id': id,                │
│     'service': service,                 │
│     'category': category,               │
│     'type': 'correction'                │
│   }                                      │
│ )                                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Add to Feedback Store:                   │
│                                          │
│ IF feedback_store is None:               │
│   feedback_store = FAISS.from_documents( │
│     [correction_doc], embeddings        │
│   )                                      │
│ ELSE:                                    │
│   new_store = FAISS.from_documents(     │
│     [correction_doc], embeddings        │
│   )                                      │
│   feedback_store.merge_from(new_store)  │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────┐
│ Learning Complete    │
│ (In-Memory Only)     │
└──────────────────────┘
```

**Key Features:**
- GPU-accelerated embeddings
- Document chunking for long texts
- In-memory FAISS for very fast search (<30ms)
- Feedback store with FAISS merge
- No persistence (reindex on restart)

---

### 3. Hybrid Search (BM25 + Semantic) - Best Accuracy with Fusion

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID SEARCH WORKFLOW                       │
└─────────────────────────────────────────────────────────────────┘

INITIALIZATION:
┌─────────────────┐
│ Start Engine    │
└────────┬────────┘
         ↓
┌──────────────────────────────────────────┐
│ Detect GPU Device                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Load Embedding Model (GPU-accelerated)  │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Initialize Text Splitter                 │
│ (chunk_size=500, overlap=50)            │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ DUAL INDEXING PROCESS:                   │
│                                          │
│ 1. Scan all markdown files              │
│ 2. For each file:                       │
│    - Read content                       │
│    - Create Document with metadata      │
│    - Split into chunks                  │
│    - Add context to chunks              │
│                                          │
│ 3. Build TWO indexes in parallel:       │
│                                          │
│    ┌──────────────────────┐            │
│    │ SEMANTIC INDEX:      │            │
│    │                      │            │
│    │ FAISS.from_documents(│            │
│    │   all_chunks,        │            │
│    │   embeddings         │            │
│    │ )                    │            │
│    │                      │            │
│    │ - Dense vectors      │            │
│    │ - Similarity search  │            │
│    └──────────────────────┘            │
│                                          │
│    ┌──────────────────────┐            │
│    │ BM25 INDEX:          │            │
│    │                      │            │
│    │ Tokenize all chunks: │            │
│    │ doc_texts = [        │            │
│    │   chunk.lower()      │            │
│    │   .split()           │            │
│    │   for chunk in docs  │            │
│    │ ]                    │            │
│    │                      │            │
│    │ BM25Okapi(doc_texts) │            │
│    │                      │            │
│    │ - Keyword-based      │            │
│    │ - Term frequency     │            │
│    └──────────────────────┘            │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Initialize Feedback Store (FAISS)        │
└────────┬─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ System Ready                    │
│ - Semantic Weight: 0.5          │
│ - BM25 Weight: 0.5              │
│ - Index Type: Dual              │
└─────────────────────────────────┘


SEARCH QUERY:
┌─────────────────┐
│ Receive Query   │
│ "error_text"    │
└────────┬────────┘
         ↓
┌──────────────────────────────────────────┐
│ STEP 1: Check Feedback Store             │
│ (Same as Semantic Search)                │
│                                          │
│ IF found with high confidence:           │
│   RETURN learned correction              │
└────────┬─────────────────────────────────┘
         ↓
         │ (If not found in feedback)
         ↓
┌──────────────────────────────────────────┐
│ STEP 2: PARALLEL SEARCH                  │
└────────┬─────────────────────────────────┘
         ↓
    ┌────┴────┐
    │         │
    ↓         ↓
┌────────────────────┐  ┌─────────────────────┐
│ SEMANTIC SEARCH    │  │ BM25 KEYWORD SEARCH │
│                    │  │                     │
│ results = FAISS    │  │ Tokenize query:     │
│   .similarity_     │  │ tokens = query      │
│   search_with_     │  │   .lower()          │
│   score(           │  │   .split()          │
│   query, k=10      │  │                     │
│ )                  │  │ scores = bm25       │
│                    │  │   .get_scores(      │
│ Returns:           │  │   tokens            │
│ - Top 10 chunks    │  │ )                   │
│ - L2 distances     │  │                     │
│                    │  │ Returns:            │
│                    │  │ - Scores for ALL    │
│                    │  │   documents         │
│                    │  │ - Get top 10        │
└────────┬───────────┘  └─────────┬───────────┘
         │                        │
         └────────┬───────────────┘
                  ↓
┌──────────────────────────────────────────┐
│ STEP 3: SCORE NORMALIZATION              │
│                                          │
│ Create combined_scores dict:            │
│                                          │
│ FOR each semantic result:                │
│   doc_id = id(doc)                      │
│   semantic_score = 1 - distance/2       │
│   combined_scores[doc_id] = {           │
│     'doc': doc,                         │
│     'semantic': semantic_score,         │
│     'bm25': 0,                          │
│     'combined': 0                       │
│   }                                      │
│                                          │
│ FOR each BM25 result:                    │
│   doc_id = id(doc)                      │
│   IF doc_id in combined_scores:         │
│     combined_scores[doc_id]['bm25'] =   │
│       bm25_score                        │
│   ELSE:                                  │
│     combined_scores[doc_id] = {         │
│       'doc': doc,                       │
│       'semantic': 0,                    │
│       'bm25': bm25_score,               │
│       'combined': 0                     │
│     }                                    │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ STEP 4: MIN-MAX NORMALIZATION            │
│                                          │
│ Extract all semantic scores:             │
│ semantic_list = [                        │
│   v['semantic']                          │
│   for v in combined_scores.values()     │
│ ]                                        │
│                                          │
│ Normalize to 0-1:                        │
│ normalized_semantic = (                  │
│   (scores - min) / (max - min)          │
│ )                                        │
│                                          │
│ Extract all BM25 scores:                 │
│ bm25_list = [...]                        │
│                                          │
│ Normalize to 0-1:                        │
│ normalized_bm25 = (                      │
│   (scores - min) / (max - min)          │
│ )                                        │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ STEP 5: WEIGHTED FUSION                  │
│                                          │
│ FOR each doc_id:                         │
│   combined_scores[doc_id]['combined'] = │
│     (semantic_weight *                   │
│      normalized_semantic[i]) +          │
│     (bm25_weight *                       │
│      normalized_bm25[i])                │
│                                          │
│ Default weights: 0.5 each                │
│                                          │
│ Example:                                 │
│   semantic_norm = 0.8                    │
│   bm25_norm = 0.6                        │
│   combined = 0.5*0.8 + 0.5*0.6 = 0.7   │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ STEP 6: SELECT BEST MATCH                │
│                                          │
│ best_match = max(                        │
│   combined_scores.values(),             │
│   key=lambda x: x['combined']           │
│ )                                        │
│                                          │
│ Extract:                                 │
│ - best_doc = best_match['doc']          │
│ - best_score = best_match['combined']   │
│ - best_doc_path = metadata['source']    │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────┐
│ RETURN:              │
│ - Doc Path           │
│ - Combined Score %   │
│ - Semantic Score %   │
│ - BM25 Score         │
└──────────────────────┘


FEEDBACK LEARNING:
┌──────────────────────────────┐
│ Same as Semantic Search:     │
│ - Create correction doc      │
│ - Add to feedback FAISS      │
│ - Merge if exists           │
└──────────────────────────────┘
```

**Key Features:**
- Dual indexing: FAISS + BM25
- Parallel search execution
- Min-max score normalization
- Weighted score fusion (configurable)
- Best for technical terms + natural language
- GPU acceleration for semantic component

---

## Multi-Engine Aggregation Workflow

When user enables "Multi-Engine Search":

```
┌─────────────────────────────────────────────────────────────────┐
│              MULTI-ENGINE CONSENSUS WORKFLOW                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│ User Query      │
│ + Multi-Search  │
│   Enabled       │
└────────┬────────┘
         ↓
┌──────────────────────────────────────────┐
│ Execute ALL Three Engines in Parallel:   │
│                                          │
│   ┌────────────┐  ┌────────────┐       │
│   │ Vector DB  │  │ Semantic   │       │
│   │   Search   │  │   Search   │       │
│   └──────┬─────┘  └──────┬─────┘       │
│          │                │              │
│          │    ┌───────────┴─────┐       │
│          │    │ Hybrid Search   │       │
│          │    └────────┬────────┘       │
│          │             │                 │
│          └──────┬──────┘                 │
│                 ↓                        │
│    ┌────────────────────────┐           │
│    │ Collect All Results:   │           │
│    │                        │           │
│    │ [                      │           │
│    │   {                    │           │
│    │     'method': 'VECTOR',│           │
│    │     'doc': '...md',    │           │
│    │     'conf': 85.5       │           │
│    │   },                   │           │
│    │   {                    │           │
│    │     'method': 'SEMANTIC',│         │
│    │     'doc': '...md',    │           │
│    │     'conf': 78.3       │           │
│    │   },                   │           │
│    │   {                    │           │
│    │     'method': 'HYBRID',│           │
│    │     'doc': '...md',    │           │
│    │     'conf': 92.1       │           │
│    │   }                    │           │
│    │ ]                      │           │
│    └────────┬───────────────┘           │
└─────────────┼───────────────────────────┘
              ↓
┌──────────────────────────────────────────┐
│ Aggregate by Document Path:              │
│                                          │
│ Count how many engines agree on each doc│
│                                          │
│ doc_votes = {}                           │
│ FOR each result:                         │
│   doc_path = result['doc']              │
│   IF doc_path not in doc_votes:         │
│     doc_votes[doc_path] = {             │
│       'count': 0,                       │
│       'methods': [],                    │
│       'confidences': []                 │
│     }                                    │
│   doc_votes[doc_path]['count'] += 1     │
│   doc_votes[doc_path]['methods'].append(│
│     result['method']                    │
│   )                                      │
│   doc_votes[doc_path]['confidences']    │
│     .append(result['conf'])             │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Determine Consensus:                     │
│                                          │
│ best_doc = max(                          │
│   doc_votes.items(),                    │
│   key=lambda x: (                       │
│     x[1]['count'],          # Vote count│
│     mean(x[1]['confidences']) # Avg conf│
│   )                                      │
│ )                                        │
│                                          │
│ Example:                                 │
│ - Doc A: 3 votes, avg conf 85%         │
│ - Doc B: 1 vote, conf 95%              │
│ Winner: Doc A (unanimous)               │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────────────────────────┐
│ Calculate Final Confidence:              │
│                                          │
│ IF consensus_count == 3:                 │
│   confidence = mean(all_confidences)    │
│   strength = "STRONG"                   │
│ ELIF consensus_count == 2:               │
│   confidence = mean(consensus_confs)    │
│   strength = "MODERATE"                 │
│ ELSE:                                    │
│   confidence = max(all_confidences)     │
│   strength = "WEAK"                     │
└────────┬─────────────────────────────────┘
         ↓
┌──────────────────────┐
│ RETURN:              │
│ - Best Doc Path      │
│ - Final Confidence   │
│ - Consensus Count    │
│ - Methods Agreed     │
│ - All Individual     │
│   Results            │
└──────────────────────┘
```

---

## System Performance Characteristics

### Speed Comparison

| Engine | Typical Latency | GPU Accelerated | Persistent |
|--------|----------------|-----------------|------------|
| Vector DB | 30-80ms | No | Yes |
| Semantic Search | 10-30ms | Yes | No |
| Hybrid Search | 50-150ms | Yes (partial) | No |
| Multi-Engine | 50-150ms | Yes (parallel) | Mixed |

### Accuracy Characteristics

| Engine | Best For | Weakness |
|--------|----------|----------|
| Vector DB | Exact semantic matches | May miss keyword-specific |
| Semantic Search | Long documents, context | May miss exact terms |
| Hybrid Search | Technical terms + semantics | Slower, more complex |
| Multi-Engine | Highest confidence needed | Slowest, requires all engines |

---

## Data Flow Summary

```
[Raw Error] 
    ↓
[Preprocessing]
    ↓
[Feature Extraction]
    ↓
[Embedding Generation] ←─── [Pre-trained Model]
    ↓
[Similarity Search] ←─── [Indexed Documentation]
    ↓                         ↑
[Score Calculation]           │
    ↓                         │
[Result Selection]            │
    ↓                         │
[Return to User]              │
    ↓                         │
[User Feedback] ──────────────┘
    ↓
[Update Feedback Store]
    ↓
[Improved Future Searches]
```

---

## Configuration Parameters

### Chunking (Semantic & Hybrid)
- **chunk_size**: 500 characters
- **chunk_overlap**: 50 characters
- **separators**: `["\n\n", "\n", ". ", " ", ""]`

### Scoring Thresholds
- **Feedback threshold**: < 0.3 (strict)
- **High confidence**: < 0.5 distance or > 80%
- **Normal confidence**: 0.5-1.0 distance or 50-80%
- **Low confidence**: > 1.0 distance or < 50%

### Hybrid Search Weights
- **semantic_weight**: 0.5 (default)
- **bm25_weight**: 0.5 (default)
- **Configurable** at initialization

### Device Detection
- **Priority**: MPS > CUDA > CPU
- **Automatic**: No manual configuration needed
- **Models affected**: HuggingFaceEmbeddings only

---

This document describes the complete workflow from data ingestion through query processing to feedback learning for all three search engines in the Error Classification System.
