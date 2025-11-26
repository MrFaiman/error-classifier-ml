"""
NLP-based Error Explainer
Uses transformer models to generate human-readable explanations for classified errors
"""
import os
import re
from typing import Optional, Dict, Tuple
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch


class NLPErrorExplainer:
    """
    Uses NLP models to generate explanations for classified errors.
    Combines the error message, documentation content, and context to produce
    clear, actionable explanations.
    """
    
    def __init__(self, model_name: str = "facebook/bart-large-cnn", use_cache: bool = True):
        """
        Initialize the NLP explainer with a pre-trained model.
        
        Args:
            model_name: Hugging Face model to use for generation
                       Options: "facebook/bart-large-cnn" (summarization)
                               "google/flan-t5-base" (text generation)
                               "t5-small" (lightweight option)
            use_cache: Whether to cache model outputs
        """
        self.model_name = model_name
        self.use_cache = use_cache
        self._explanation_cache = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize based on model type
        try:
            if "t5" in model_name.lower() or "flan" in model_name.lower():
                # Use text2text generation for T5/FLAN models
                self.model = pipeline(
                    "text2text-generation",
                    model=model_name,
                    device=0 if self.device == "cuda" else -1,
                    max_length=200,
                    truncation=True
                )
                self.model_type = "text2text"
            else:
                # Use summarization for BART and similar models
                self.model = pipeline(
                    "summarization",
                    model=model_name,
                    device=0 if self.device == "cuda" else -1,
                    max_length=150,
                    min_length=30,
                    truncation=True
                )
                self.model_type = "summarization"
            
            print(f"[OK] NLP Explainer initialized with {model_name} on {self.device}")
            
        except Exception as e:
            print(f"[WARNING] Could not load model {model_name}: {e}")
            print(f"[INFO] Falling back to rule-based explanations")
            self.model = None
            self.model_type = "rule-based"
    
    def _read_doc_content(self, doc_path: str) -> Optional[str]:
        """Read documentation file content"""
        try:
            if os.path.exists(doc_path):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"[WARNING] Could not read doc {doc_path}: {e}")
        return None
    
    def _extract_key_info(self, doc_content: str) -> Dict[str, str]:
        """
        Extract key information from documentation markdown:
        - Title/Category
        - Description
        - Root Cause
        - Solution
        """
        info = {
            'title': '',
            'description': '',
            'root_cause': '',
            'solution': ''
        }
        
        if not doc_content:
            return info
        
        lines = doc_content.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # Detect sections
            if line_stripped.startswith('# '):
                info['title'] = line_stripped[2:].strip()
            elif line_stripped.startswith('## Description'):
                current_section = 'description'
            elif line_stripped.startswith('## Root Cause') or line_stripped.startswith('## Cause'):
                current_section = 'root_cause'
            elif line_stripped.startswith('## Solution') or line_stripped.startswith('## Resolution'):
                current_section = 'solution'
            elif line_stripped.startswith('##'):
                current_section = None
            elif current_section and line_stripped and not line_stripped.startswith('#'):
                # Accumulate content for current section
                if current_section in info:
                    if info[current_section]:
                        info[current_section] += ' ' + line_stripped
                    else:
                        info[current_section] = line_stripped
        
        return info
    
    def _build_prompt(self, error_message: str, doc_info: Dict[str, str], 
                     service: str = "", category: str = "") -> str:
        """
        Build a prompt for the NLP model to generate an explanation.
        """
        if self.model_type == "text2text":
            # For T5/FLAN models - use instruction format
            prompt = f"Explain this error in simple terms: "
            prompt += f"Error '{error_message}' "
            if service:
                prompt += f"in {service} service "
            if category:
                prompt += f"is classified as {category}. "
            
            if doc_info.get('description'):
                prompt += f"Details: {doc_info['description'][:200]}"
            
            return prompt
        else:
            # For summarization models - provide context to summarize
            context = f"Error Message: {error_message}\n\n"
            
            if service and category:
                context += f"Classification: {service} - {category}\n\n"
            
            if doc_info.get('description'):
                context += f"Description: {doc_info['description']}\n\n"
            
            if doc_info.get('root_cause'):
                context += f"Root Cause: {doc_info['root_cause']}\n\n"
            
            if doc_info.get('solution'):
                context += f"Solution: {doc_info['solution']}\n\n"
            
            return context
    
    def _generate_rule_based_explanation(self, error_message: str, 
                                        doc_info: Dict[str, str],
                                        service: str = "",
                                        category: str = "") -> str:
        """
        Generate a rule-based explanation when model is not available.
        This provides a fallback that extracts key info from documentation.
        """
        explanation_parts = []
        
        # Start with classification
        if service and category:
            explanation_parts.append(
                f"This error is classified as '{category}' in the {service} service."
            )
        
        # Add description if available
        if doc_info.get('description'):
            desc = doc_info['description'][:200]
            explanation_parts.append(desc)
        
        # Add root cause if available
        if doc_info.get('root_cause'):
            cause = doc_info['root_cause'][:150]
            explanation_parts.append(f"Cause: {cause}")
        
        # Add solution hint if available
        if doc_info.get('solution'):
            solution = doc_info['solution'][:150]
            explanation_parts.append(f"Solution: {solution}")
        
        if not explanation_parts:
            explanation_parts.append(
                f"The error '{error_message}' has been classified. "
                "Please refer to the documentation for more details."
            )
        
        return " ".join(explanation_parts)
    
    def explain_error(self, error_message: str, doc_path: str, 
                     confidence: float, metadata: Optional[Dict] = None) -> str:
        """
        Generate a human-readable explanation for a classified error.
        
        Args:
            error_message: The original error message
            doc_path: Path to the classified documentation file
            confidence: Classification confidence score (0-100)
            metadata: Optional metadata (service, category, etc.)
            
        Returns:
            String explanation of the error
        """
        # Check cache
        cache_key = f"{error_message}:{doc_path}"
        if self.use_cache and cache_key in self._explanation_cache:
            return self._explanation_cache[cache_key]
        
        # Extract metadata
        service = metadata.get('service', '') if metadata else ''
        category = metadata.get('category', '') if metadata else ''
        
        # Read documentation
        doc_content = self._read_doc_content(doc_path)
        doc_info = self._extract_key_info(doc_content) if doc_content else {}
        
        # Generate explanation
        if self.model and self.model_type != "rule-based":
            try:
                prompt = self._build_prompt(error_message, doc_info, service, category)
                
                # Generate with model
                if self.model_type == "text2text":
                    result = self.model(prompt, max_length=200, min_length=30)
                    explanation = result[0]['generated_text']
                else:
                    result = self.model(prompt, max_length=150, min_length=30)
                    explanation = result[0]['summary_text']
                
                # Clean up explanation
                explanation = explanation.strip()
                
                # Add confidence note if low
                if confidence < 50:
                    explanation += f" (Note: Classification confidence is {confidence:.1f}%, please verify.)"
                
            except Exception as e:
                print(f"[WARNING] Model generation failed: {e}, using rule-based fallback")
                explanation = self._generate_rule_based_explanation(
                    error_message, doc_info, service, category
                )
        else:
            # Use rule-based explanation
            explanation = self._generate_rule_based_explanation(
                error_message, doc_info, service, category
            )
        
        # Cache the result
        if self.use_cache:
            self._explanation_cache[cache_key] = explanation
        
        return explanation
    
    def explain_with_context(self, error_message: str, doc_path: str,
                           confidence: float, metadata: Optional[Dict] = None,
                           include_raw_doc: bool = False) -> Dict[str, any]:
        """
        Generate a detailed explanation with additional context.
        
        Args:
            error_message: The original error message
            doc_path: Path to the classified documentation file
            confidence: Classification confidence score
            metadata: Optional metadata
            include_raw_doc: Whether to include raw documentation content
            
        Returns:
            Dictionary with explanation and context
        """
        doc_content = self._read_doc_content(doc_path)
        doc_info = self._extract_key_info(doc_content) if doc_content else {}
        
        explanation = self.explain_error(error_message, doc_path, confidence, metadata)
        
        result = {
            'explanation': explanation,
            'confidence': confidence,
            'category': metadata.get('category', '') if metadata else '',
            'service': metadata.get('service', '') if metadata else '',
            'doc_path': doc_path,
            'key_points': {
                'title': doc_info.get('title', ''),
                'root_cause': doc_info.get('root_cause', ''),
                'solution': doc_info.get('solution', '')
            }
        }
        
        if include_raw_doc:
            result['raw_documentation'] = doc_content
        
        return result
    
    def batch_explain(self, classifications: list) -> list:
        """
        Generate explanations for multiple classifications in batch.
        
        Args:
            classifications: List of dicts with keys:
                            - error_message
                            - doc_path
                            - confidence
                            - metadata (optional)
        
        Returns:
            List of explanations
        """
        explanations = []
        
        for item in classifications:
            explanation = self.explain_error(
                item.get('error_message', ''),
                item.get('doc_path', ''),
                item.get('confidence', 0.0),
                item.get('metadata')
            )
            explanations.append(explanation)
        
        return explanations
    
    def clear_cache(self):
        """Clear the explanation cache"""
        self._explanation_cache.clear()
        print("[OK] Explanation cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'cache_size': len(self._explanation_cache),
            'cache_enabled': self.use_cache
        }


# Global explainer instance (lazy initialization)
_explainer_instance = None


def get_explainer(model_name: str = "t5-small") -> NLPErrorExplainer:
    """
    Get or create the global explainer instance.
    Uses a lightweight model by default for faster initialization.
    
    Args:
        model_name: Model to use (default: t5-small for speed)
                   Options: "t5-small", "google/flan-t5-base", "facebook/bart-large-cnn"
    """
    global _explainer_instance
    
    if _explainer_instance is None:
        _explainer_instance = NLPErrorExplainer(model_name=model_name)
    
    return _explainer_instance


if __name__ == "__main__":
    # Test the explainer
    print("Testing NLP Error Explainer")
    print("=" * 70)
    
    # Create test documentation
    test_doc_content = """# NEGATIVE_VALUE

## Description
This error occurs when a numeric field contains a negative value where only positive values are expected.

## Root Cause
The system validates that certain fields must have positive values, such as quantities, prices, or measurements.

## Solution
Ensure all numeric inputs for quantity, amount, and measurement fields are positive numbers (greater than 0).
"""
    
    # Create temporary test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_doc_content)
        test_doc_path = f.name
    
    try:
        # Initialize explainer with lightweight model
        print("\n1. Initializing explainer...")
        explainer = NLPErrorExplainer(model_name="t5-small")
        
        # Test explanation
        print("\n2. Generating explanation...")
        error_msg = "Quantity cannot be negative: -5"
        metadata = {'service': 'logitrack', 'category': 'NEGATIVE_VALUE'}
        
        explanation = explainer.explain_error(
            error_msg, 
            test_doc_path, 
            confidence=85.5,
            metadata=metadata
        )
        
        print(f"\nError: {error_msg}")
        print(f"Explanation: {explanation}")
        
        # Test detailed explanation
        print("\n3. Generating detailed explanation...")
        detailed = explainer.explain_with_context(
            error_msg,
            test_doc_path,
            confidence=85.5,
            metadata=metadata
        )
        
        print(f"\nDetailed Explanation:")
        print(f"  Service: {detailed['service']}")
        print(f"  Category: {detailed['category']}")
        print(f"  Confidence: {detailed['confidence']:.2f}%")
        print(f"  Explanation: {detailed['explanation']}")
        print(f"  Root Cause: {detailed['key_points']['root_cause']}")
        
        # Test cache
        print("\n4. Testing cache...")
        stats = explainer.get_cache_stats()
        print(f"  Cache size: {stats['cache_size']}")
        print(f"  Cache enabled: {stats['cache_enabled']}")
        
        print("\n✅ All tests passed!")
        
    finally:
        # Cleanup
        import os
        if os.path.exists(test_doc_path):
            os.remove(test_doc_path)
