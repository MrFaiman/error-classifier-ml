"""
Tests for NLP Error Explainer
"""
import pytest
import os
import tempfile
from algorithms.nlp_explainer import NLPErrorExplainer, get_explainer


@pytest.fixture
def sample_doc():
    """Create a sample documentation file"""
    content = """# NEGATIVE_VALUE

## Description
This error occurs when a numeric field contains a negative value where only positive values are expected.

## Root Cause
The system validates that certain fields must have positive values, such as quantities, prices, or measurements.

## Solution
Ensure all numeric inputs for quantity, amount, and measurement fields are positive numbers (greater than 0).
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def explainer():
    """Create an NLP explainer instance"""
    # Use lightweight model for testing
    return NLPErrorExplainer(model_name="t5-small", use_cache=True)


def test_explainer_initialization():
    """Test that explainer initializes correctly"""
    explainer = NLPErrorExplainer(model_name="t5-small")
    assert explainer is not None
    assert explainer.model_type in ["text2text", "summarization", "rule-based"]
    assert explainer.use_cache == True


def test_rule_based_fallback():
    """Test rule-based explanation when model is unavailable"""
    # Initialize with invalid model to force rule-based fallback
    explainer = NLPErrorExplainer(model_name="invalid-model-name")
    assert explainer.model_type == "rule-based"


def test_extract_key_info(explainer, sample_doc):
    """Test extraction of key information from documentation"""
    with open(sample_doc, 'r') as f:
        content = f.read()
    
    info = explainer._extract_key_info(content)
    
    assert 'title' in info
    assert 'description' in info
    assert 'root_cause' in info
    assert 'solution' in info
    assert info['title'] == 'NEGATIVE_VALUE'
    assert 'numeric field' in info['description']
    assert len(info['root_cause']) > 0
    assert len(info['solution']) > 0


def test_explain_error(explainer, sample_doc):
    """Test basic error explanation generation"""
    error_msg = "Quantity cannot be negative: -5"
    metadata = {'service': 'logitrack', 'category': 'NEGATIVE_VALUE'}
    
    explanation = explainer.explain_error(
        error_msg,
        sample_doc,
        confidence=85.5,
        metadata=metadata
    )
    
    assert explanation is not None
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    # Should mention something relevant to the error
    assert any(word in explanation.lower() for word in ['negative', 'value', 'error', 'field', 'positive'])


def test_explain_with_low_confidence(explainer, sample_doc):
    """Test that low confidence is indicated in explanation"""
    error_msg = "Test error"
    metadata = {'service': 'test', 'category': 'TEST'}
    
    explanation = explainer.explain_error(
        error_msg,
        sample_doc,
        confidence=35.0,  # Low confidence
        metadata=metadata
    )
    
    # For model-based explanations, check for confidence warning
    if explainer.model_type != "rule-based":
        assert 'confidence' in explanation.lower() or 'verify' in explanation.lower()


def test_explain_with_context(explainer, sample_doc):
    """Test detailed explanation with context"""
    error_msg = "Invalid value: -10"
    metadata = {'service': 'logitrack', 'category': 'NEGATIVE_VALUE'}
    
    result = explainer.explain_with_context(
        error_msg,
        sample_doc,
        confidence=90.0,
        metadata=metadata,
        include_raw_doc=True
    )
    
    assert 'explanation' in result
    assert 'confidence' in result
    assert 'category' in result
    assert 'service' in result
    assert 'doc_path' in result
    assert 'key_points' in result
    assert 'raw_documentation' in result
    
    assert result['confidence'] == 90.0
    assert result['category'] == 'NEGATIVE_VALUE'
    assert result['service'] == 'logitrack'
    assert 'title' in result['key_points']
    assert 'root_cause' in result['key_points']
    assert 'solution' in result['key_points']


def test_batch_explain(explainer, sample_doc):
    """Test batch explanation generation"""
    classifications = [
        {
            'error_message': 'Error 1: negative value',
            'doc_path': sample_doc,
            'confidence': 85.0,
            'metadata': {'service': 'logitrack', 'category': 'NEGATIVE_VALUE'}
        },
        {
            'error_message': 'Error 2: invalid number',
            'doc_path': sample_doc,
            'confidence': 75.0,
            'metadata': {'service': 'logitrack', 'category': 'NEGATIVE_VALUE'}
        }
    ]
    
    explanations = explainer.batch_explain(classifications)
    
    assert len(explanations) == 2
    assert all(isinstance(exp, str) for exp in explanations)
    assert all(len(exp) > 0 for exp in explanations)


def test_caching(explainer, sample_doc):
    """Test that caching works correctly"""
    error_msg = "Test caching error"
    metadata = {'service': 'test', 'category': 'TEST'}
    
    # First call - should generate and cache
    exp1 = explainer.explain_error(error_msg, sample_doc, 80.0, metadata)
    
    # Second call - should use cache
    exp2 = explainer.explain_error(error_msg, sample_doc, 80.0, metadata)
    
    # Should be identical
    assert exp1 == exp2
    
    # Check cache stats
    stats = explainer.get_cache_stats()
    assert stats['cache_enabled'] == True
    assert stats['cache_size'] > 0


def test_cache_clear(explainer, sample_doc):
    """Test cache clearing"""
    error_msg = "Test cache clear"
    metadata = {'service': 'test', 'category': 'TEST'}
    
    # Generate explanation
    explainer.explain_error(error_msg, sample_doc, 80.0, metadata)
    
    # Check cache has items
    stats = explainer.get_cache_stats()
    assert stats['cache_size'] > 0
    
    # Clear cache
    explainer.clear_cache()
    
    # Verify cache is empty
    stats = explainer.get_cache_stats()
    assert stats['cache_size'] == 0


def test_nonexistent_doc(explainer):
    """Test handling of non-existent documentation file"""
    error_msg = "Test error"
    fake_doc = "/fake/path/to/doc.md"
    metadata = {'service': 'test', 'category': 'TEST'}
    
    # Should handle gracefully and return explanation
    explanation = explainer.explain_error(error_msg, fake_doc, 50.0, metadata)
    
    assert explanation is not None
    assert isinstance(explanation, str)
    # Should still provide some explanation even without doc content


def test_empty_metadata(explainer, sample_doc):
    """Test explanation generation without metadata"""
    error_msg = "Error without metadata"
    
    explanation = explainer.explain_error(
        error_msg,
        sample_doc,
        confidence=70.0,
        metadata=None
    )
    
    assert explanation is not None
    assert isinstance(explanation, str)
    assert len(explanation) > 0


def test_get_explainer_singleton():
    """Test that get_explainer returns singleton instance"""
    explainer1 = get_explainer(model_name="t5-small")
    explainer2 = get_explainer(model_name="t5-small")
    
    # Should be same instance
    assert explainer1 is explainer2


def test_rule_based_explanation_generation(sample_doc):
    """Test rule-based explanation when no model is available"""
    # Force rule-based by using invalid model
    explainer = NLPErrorExplainer(model_name="invalid-model")
    
    error_msg = "Negative value detected"
    metadata = {'service': 'logitrack', 'category': 'NEGATIVE_VALUE'}
    
    explanation = explainer._generate_rule_based_explanation(
        error_msg,
        explainer._extract_key_info(explainer._read_doc_content(sample_doc)),
        service=metadata['service'],
        category=metadata['category']
    )
    
    assert explanation is not None
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    assert 'NEGATIVE_VALUE' in explanation
    assert 'logitrack' in explanation


def test_build_prompt_text2text(sample_doc):
    """Test prompt building for text2text models"""
    explainer = NLPErrorExplainer(model_name="t5-small")
    
    # Read doc and extract info
    doc_content = explainer._read_doc_content(sample_doc)
    doc_info = explainer._extract_key_info(doc_content)
    
    prompt = explainer._build_prompt(
        "Test error",
        doc_info,
        service="logitrack",
        category="NEGATIVE_VALUE"
    )
    
    assert "Explain this error" in prompt
    assert "Test error" in prompt
    assert "logitrack" in prompt
    assert "NEGATIVE_VALUE" in prompt


def test_multiple_services_categories(explainer, sample_doc):
    """Test explanations for different services and categories"""
    services = ['logitrack', 'meteo-il', 'skyguard']
    categories = ['NEGATIVE_VALUE', 'MISSING_FIELD', 'SCHEMA_VALIDATION']
    
    for service in services:
        for category in categories:
            error_msg = f"Error in {service} - {category}"
            metadata = {'service': service, 'category': category}
            
            explanation = explainer.explain_error(
                error_msg,
                sample_doc,
                confidence=75.0,
                metadata=metadata
            )
            
            assert explanation is not None
            assert len(explanation) > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
