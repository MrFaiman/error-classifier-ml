#!/usr/bin/env python3
"""
NLP Explainer Demo Script
Demonstrates the NLP-powered error explanation feature
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from algorithms import get_explainer
from constants import DOCS_ROOT_DIR
import glob


def demo_basic_explanation():
    """Demo 1: Basic error explanation"""
    print("=" * 70)
    print("DEMO 1: Basic Error Explanation")
    print("=" * 70)
    
    # Find a sample documentation file
    pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
    doc_files = glob.glob(pattern, recursive=True)
    
    if not doc_files:
        print("No documentation files found!")
        return
    
    # Use the first file
    sample_doc = doc_files[0]
    
    # Extract metadata from path
    parts = sample_doc.replace('\\', '/').split('/')
    try:
        services_idx = parts.index('services')
        service = parts[services_idx + 1]
        category = parts[services_idx + 2].replace('.md', '')
    except (ValueError, IndexError):
        service = "unknown"
        category = "UNKNOWN"
    
    print(f"\nSample Documentation: {sample_doc}")
    print(f"Service: {service}")
    print(f"Category: {category}")
    
    # Initialize explainer
    print("\n📚 Initializing NLP Explainer...")
    explainer = get_explainer(model_name="t5-small")
    
    # Generate explanation
    error_msg = f"Error detected: validation failed for {category.lower().replace('_', ' ')}"
    print(f"\n❌ Error Message: '{error_msg}'")
    
    print("\n🤖 Generating explanation...")
    explanation = explainer.explain_error(
        error_message=error_msg,
        doc_path=sample_doc,
        confidence=85.5,
        metadata={'service': service, 'category': category}
    )
    
    print(f"\n💡 Explanation:")
    print(f"   {explanation}")
    print()


def demo_detailed_explanation():
    """Demo 2: Detailed explanation with context"""
    print("=" * 70)
    print("DEMO 2: Detailed Explanation with Context")
    print("=" * 70)
    
    # Find a sample documentation file
    pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
    doc_files = glob.glob(pattern, recursive=True)
    
    if not doc_files:
        print("No documentation files found!")
        return
    
    sample_doc = doc_files[0]
    
    # Extract metadata
    parts = sample_doc.replace('\\', '/').split('/')
    try:
        services_idx = parts.index('services')
        service = parts[services_idx + 1]
        category = parts[services_idx + 2].replace('.md', '')
    except (ValueError, IndexError):
        service = "unknown"
        category = "UNKNOWN"
    
    # Initialize explainer
    explainer = get_explainer(model_name="t5-small")
    
    # Generate detailed explanation
    error_msg = f"System error: {category.lower().replace('_', ' ')}"
    print(f"\n❌ Error Message: '{error_msg}'")
    
    print("\n🤖 Generating detailed explanation...")
    detailed = explainer.explain_with_context(
        error_message=error_msg,
        doc_path=sample_doc,
        confidence=90.0,
        metadata={'service': service, 'category': category},
        include_raw_doc=False
    )
    
    print(f"\n📊 Classification Details:")
    print(f"   Service:    {detailed['service']}")
    print(f"   Category:   {detailed['category']}")
    print(f"   Confidence: {detailed['confidence']:.1f}%")
    print(f"   Doc Path:   {os.path.basename(detailed['doc_path'])}")
    
    print(f"\n💡 Explanation:")
    print(f"   {detailed['explanation']}")
    
    if detailed['key_points']['root_cause']:
        print(f"\n🔍 Root Cause:")
        print(f"   {detailed['key_points']['root_cause'][:150]}...")
    
    if detailed['key_points']['solution']:
        print(f"\n✅ Solution:")
        print(f"   {detailed['key_points']['solution'][:150]}...")
    
    print()


def demo_batch_processing():
    """Demo 3: Batch explanation processing"""
    print("=" * 70)
    print("DEMO 3: Batch Processing Multiple Errors")
    print("=" * 70)
    
    # Find sample documentation files
    pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
    doc_files = glob.glob(pattern, recursive=True)[:3]  # Use first 3 files
    
    if not doc_files:
        print("No documentation files found!")
        return
    
    # Initialize explainer
    explainer = get_explainer(model_name="t5-small")
    
    # Prepare batch
    classifications = []
    for i, doc_file in enumerate(doc_files, 1):
        parts = doc_file.replace('\\', '/').split('/')
        try:
            services_idx = parts.index('services')
            service = parts[services_idx + 1]
            category = parts[services_idx + 2].replace('.md', '')
        except (ValueError, IndexError):
            service = "unknown"
            category = "UNKNOWN"
        
        classifications.append({
            'error_message': f"Error {i}: validation failed in {service}",
            'doc_path': doc_file,
            'confidence': 80.0 + i * 5,
            'metadata': {'service': service, 'category': category}
        })
    
    print(f"\n🤖 Processing {len(classifications)} errors in batch...")
    explanations = explainer.batch_explain(classifications)
    
    print(f"\n📋 Results:")
    for i, (classification, explanation) in enumerate(zip(classifications, explanations), 1):
        print(f"\n   Error {i}:")
        print(f"   Message:     {classification['error_message']}")
        print(f"   Service:     {classification['metadata']['service']}")
        print(f"   Category:    {classification['metadata']['category']}")
        print(f"   Confidence:  {classification['confidence']:.1f}%")
        print(f"   Explanation: {explanation[:100]}...")
    
    print()


def demo_cache_performance():
    """Demo 4: Cache performance comparison"""
    print("=" * 70)
    print("DEMO 4: Cache Performance")
    print("=" * 70)
    
    # Find a sample documentation file
    pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
    doc_files = glob.glob(pattern, recursive=True)
    
    if not doc_files:
        print("No documentation files found!")
        return
    
    sample_doc = doc_files[0]
    
    # Extract metadata
    parts = sample_doc.replace('\\', '/').split('/')
    try:
        services_idx = parts.index('services')
        service = parts[services_idx + 1]
        category = parts[services_idx + 2].replace('.md', '')
    except (ValueError, IndexError):
        service = "unknown"
        category = "UNKNOWN"
    
    # Initialize explainer
    explainer = get_explainer(model_name="t5-small")
    
    error_msg = "Cache test error"
    
    import time
    
    # First call (not cached)
    print("\n⏱️  First call (generating explanation)...")
    start = time.time()
    exp1 = explainer.explain_error(
        error_msg, sample_doc, 85.0,
        {'service': service, 'category': category}
    )
    time1 = time.time() - start
    print(f"   Time: {time1*1000:.0f}ms")
    
    # Second call (cached)
    print("\n⚡ Second call (from cache)...")
    start = time.time()
    exp2 = explainer.explain_error(
        error_msg, sample_doc, 85.0,
        {'service': service, 'category': category}
    )
    time2 = time.time() - start
    print(f"   Time: {time2*1000:.0f}ms")
    
    # Verify same result
    assert exp1 == exp2, "Cached result should match original"
    
    print(f"\n📊 Performance improvement: {time1/time2:.1f}x faster")
    
    # Show cache stats
    stats = explainer.get_cache_stats()
    print(f"\n💾 Cache Statistics:")
    print(f"   Cache enabled: {stats['cache_enabled']}")
    print(f"   Cache size:    {stats['cache_size']} entries")
    
    print()


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  NLP-POWERED ERROR EXPLANATION DEMO")
    print("=" * 70 + "\n")
    
    try:
        # Run demos
        demo_basic_explanation()
        input("Press Enter to continue to next demo...")
        
        demo_detailed_explanation()
        input("Press Enter to continue to next demo...")
        
        demo_batch_processing()
        input("Press Enter to continue to next demo...")
        
        demo_cache_performance()
        
        print("=" * 70)
        print("✅ All demos completed successfully!")
        print("=" * 70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
