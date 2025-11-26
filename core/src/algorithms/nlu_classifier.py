"""
Natural Language Understanding (NLU) Module for Error Classification
Provides intent classification, entity extraction, and semantic understanding
"""
from typing import Dict, List, Tuple, Optional
import re
from transformers import pipeline
import warnings

warnings.filterwarnings('ignore')


class NLUErrorClassifier:
    """
    NLU-based error classifier using transformer models
    Provides intent classification and entity extraction
    """
    
    def __init__(self, use_zero_shot=True, use_ner=True):
        """
        Initialize NLU classifier
        
        Args:
            use_zero_shot: Enable zero-shot intent classification
            use_ner: Enable named entity recognition
        """
        self.use_zero_shot = use_zero_shot
        self.use_ner = use_ner
        
        # Intent classification intents
        self.intents = [
            "validation error",
            "security threat",
            "data corruption",
            "sensor failure",
            "configuration error",
            "type mismatch",
            "missing data",
            "format error"
        ]
        
        # Error category patterns (rule-based fallback)
        self.category_patterns = {
            'NEGATIVE_VALUE': r'negative|minus|-\d+|below zero',
            'MISSING_FIELD': r'missing|absent|undefined|null|not found|empty',
            'TYPE_MISMATCH': r'type|expected \w+ got|string|number|boolean|array',
            'SCHEMA_VALIDATION': r'validation|schema|invalid|out of range|exceeds',
            'GEO_OUT_OF_BOUNDS': r'latitude|longitude|geo|coordinates|bounds',
            'REGEX_MISMATCH': r'regex|pattern|format|mismatch',
            'INVALID_ENUM': r'enum|allowed values|not in list|invalid status',
            'INVALID_DATE': r'date|timestamp|time|format|iso|epoch',
            'SECURITY_ALERT': r'injection|xss|script|malicious|security|attack',
        }
        
        # Initialize models lazily
        self._zero_shot_classifier = None
        self._ner_model = None
        
        print("[NLU] Initialized (models will load on first use)")
    
    def _get_zero_shot_classifier(self):
        """Lazy load zero-shot classifier"""
        if self._zero_shot_classifier is None:
            print("[NLU] Loading zero-shot classification model...")
            self._zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU
            )
            print("[NLU] ✓ Zero-shot classifier loaded")
        return self._zero_shot_classifier
    
    def _get_ner_model(self):
        """Lazy load NER model"""
        if self._ner_model is None:
            print("[NLU] Loading NER model...")
            self._ner_model = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                device=-1  # CPU
            )
            print("[NLU] ✓ NER model loaded")
        return self._ner_model
    
    def classify_intent(self, error_message: str) -> Tuple[str, float]:
        """
        Classify the intent of an error message
        
        Args:
            error_message: Error text to classify
            
        Returns:
            Tuple of (intent, confidence_score)
        """
        if not self.use_zero_shot:
            return self._rule_based_intent(error_message)
        
        try:
            classifier = self._get_zero_shot_classifier()
            result = classifier(error_message, self.intents, multi_label=False)
            return result['labels'][0], result['scores'][0]
        except Exception as e:
            print(f"[NLU Warning] Zero-shot failed: {e}, using rule-based")
            return self._rule_based_intent(error_message)
    
    def _rule_based_intent(self, error_message: str) -> Tuple[str, float]:
        """Rule-based intent classification as fallback"""
        error_lower = error_message.lower()
        
        # Pattern matching for intents
        if re.search(r'injection|xss|script|malicious', error_lower):
            return "security threat", 0.9
        elif re.search(r'missing|absent|undefined|null', error_lower):
            return "missing data", 0.85
        elif re.search(r'type|expected|mismatch', error_lower):
            return "type mismatch", 0.85
        elif re.search(r'validation|invalid|out of range', error_lower):
            return "validation error", 0.8
        elif re.search(r'sensor|signal|device|hardware', error_lower):
            return "sensor failure", 0.8
        elif re.search(r'format|regex|pattern', error_lower):
            return "format error", 0.8
        else:
            return "validation error", 0.5  # Default
    
    def extract_entities(self, error_message: str) -> Dict[str, List[Dict]]:
        """
        Extract named entities from error message
        
        Args:
            error_message: Error text to analyze
            
        Returns:
            Dictionary of entity types and their values
        """
        entities = {
            'fields': [],
            'values': [],
            'numbers': [],
            'keywords': []
        }
        
        # Extract field names (common patterns)
        field_pattern = r'\b(\w+)(?=\s*[:=]|\s+field)'
        fields = re.findall(field_pattern, error_message, re.IGNORECASE)
        entities['fields'] = list(set(fields))
        
        # Extract numeric values
        number_pattern = r'-?\d+\.?\d*'
        numbers = re.findall(number_pattern, error_message)
        entities['numbers'] = [float(n) if '.' in n else int(n) for n in numbers]
        
        # Extract quoted values
        value_pattern = r'["\']([^"\']+)["\']'
        values = re.findall(value_pattern, error_message)
        entities['values'] = values
        
        # Extract error keywords
        for category, pattern in self.category_patterns.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                entities['keywords'].append(category)
        
        # Use NER model if enabled
        if self.use_ner:
            try:
                ner = self._get_ner_model()
                ner_results = ner(error_message)
                entities['ner_entities'] = [
                    {'text': ent['word'], 'type': ent['entity'], 'score': ent['score']}
                    for ent in ner_results if ent['score'] > 0.8
                ]
            except Exception as e:
                print(f"[NLU Warning] NER failed: {e}")
                entities['ner_entities'] = []
        
        return entities
    
    def predict_category(self, error_message: str) -> Tuple[str, float]:
        """
        Predict error category using NLU
        
        Args:
            error_message: Error text to classify
            
        Returns:
            Tuple of (category, confidence)
        """
        error_lower = error_message.lower()
        
        # Score each category
        scores = {}
        for category, pattern in self.category_patterns.items():
            match = re.search(pattern, error_lower)
            if match:
                # Base score from pattern match
                scores[category] = 0.7
                
                # Boost score based on keyword prominence
                match_pos = match.start() / max(len(error_lower), 1)
                if match_pos < 0.3:  # Early in message
                    scores[category] += 0.15
                
                # Boost if multiple keywords match
                all_matches = re.findall(pattern, error_lower)
                if len(all_matches) > 1:
                    scores[category] += 0.1
        
        if not scores:
            return "UNKNOWN", 0.3
        
        # Get best category
        best_category = max(scores, key=scores.get)
        confidence = min(scores[best_category], 0.95)
        
        return best_category, confidence
    
    def analyze_error(self, error_message: str) -> Dict:
        """
        Complete NLU analysis of an error message
        
        Args:
            error_message: Error text to analyze
            
        Returns:
            Dictionary with intent, entities, category, and confidence
        """
        intent, intent_confidence = self.classify_intent(error_message)
        entities = self.extract_entities(error_message)
        category, category_confidence = self.predict_category(error_message)
        
        return {
            'error_message': error_message,
            'intent': intent,
            'intent_confidence': intent_confidence,
            'category': category,
            'category_confidence': category_confidence,
            'entities': entities,
            'nlu_score': (intent_confidence + category_confidence) / 2
        }
    
    def batch_analyze(self, error_messages: List[str]) -> List[Dict]:
        """Analyze multiple error messages"""
        return [self.analyze_error(msg) for msg in error_messages]


class SemanticNLUSearch:
    """
    Semantic search using sentence transformers
    More advanced than TF-IDF - understands meaning, not just keywords
    """
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize semantic search
        
        Args:
            model_name: Sentence transformer model to use
        """
        print(f"[NLU] Loading sentence transformer: {model_name}...")
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.embeddings = None
            self.documents = []
            self.doc_paths = []
            print(f"[NLU] ✓ Semantic search initialized")
        except ImportError:
            print("[NLU Warning] sentence-transformers not installed")
            print("Install with: pip install sentence-transformers")
            self.model = None
    
    def index_documents(self, documents: List[str], doc_paths: List[str]):
        """
        Index documents with semantic embeddings
        
        Args:
            documents: List of document texts
            doc_paths: List of document file paths
        """
        if self.model is None:
            raise RuntimeError("Sentence transformers not available")
        
        print(f"[NLU] Encoding {len(documents)} documents...")
        self.documents = documents
        self.doc_paths = doc_paths
        self.embeddings = self.model.encode(documents, show_progress_bar=True)
        print(f"[NLU] ✓ Indexed {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Semantic search for most relevant documents
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            List of (doc_path, similarity_score) tuples
        """
        if self.model is None or self.embeddings is None:
            raise RuntimeError("Index not built")
        
        # Encode query
        query_embedding = self.model.encode([query])[0]
        
        # Calculate cosine similarity
        from numpy import dot
        from numpy.linalg import norm
        
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = dot(query_embedding, doc_embedding) / (
                norm(query_embedding) * norm(doc_embedding)
            )
            similarities.append((self.doc_paths[i], float(similarity)))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]


if __name__ == "__main__":
    # Test NLU classifier
    print("Testing NLU Error Classifier")
    print("=" * 70)
    
    # Initialize (lightweight mode - no heavy models)
    nlu = NLUErrorClassifier(use_zero_shot=False, use_ner=False)
    
    # Test cases
    test_errors = [
        "quantity: -5 validation failed",
        "sensor_id field is missing from request",
        "expected number but got string '100'",
        "SQL injection attempt detected: OR 1=1",
        "latitude value 91.5 exceeds valid range",
        "timestamp format invalid: 24/11/2025",
        "status must be one of: ACTIVE, INACTIVE, PENDING"
    ]
    
    print("\nAnalyzing error messages:\n")
    
    for error in test_errors:
        print(f"Error: {error}")
        analysis = nlu.analyze_error(error)
        print(f"  Intent: {analysis['intent']} ({analysis['intent_confidence']:.2%})")
        print(f"  Category: {analysis['category']} ({analysis['category_confidence']:.2%})")
        print(f"  Fields: {analysis['entities']['fields']}")
        print(f"  Numbers: {analysis['entities']['numbers']}")
        print(f"  Keywords: {analysis['entities']['keywords']}")
        print()
    
    print("✅ NLU tests completed!")
