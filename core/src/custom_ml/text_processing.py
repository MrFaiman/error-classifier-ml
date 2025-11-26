"""
Custom Text Preprocessing and Chunking Implementation
Replaces LangChain's RecursiveCharacterTextSplitter
"""
from typing import List, Optional
import re


class TextChunker:
    """
    Custom text chunking implementation for splitting documents into smaller chunks
    
    This replaces LangChain's RecursiveCharacterTextSplitter with a custom implementation
    that gives us full control over the chunking strategy.
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, 
                 separators: Optional[List[str]] = None):
        """
        Initialize text chunker
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to try (in order of preference)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Default separators (ordered by preference)
        if separators is None:
            self.separators = [
                "\n\n",  # Double newline (paragraphs)
                "\n",    # Single newline
                ". ",    # Sentence end
                "! ",    # Exclamation
                "? ",    # Question
                "; ",    # Semicolon
                ", ",    # Comma
                " ",     # Space
                ""       # Character-level split (last resort)
            ]
        else:
            self.separators = separators
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks using recursive splitting strategy
        
        Algorithm:
        1. Try to split on the first separator
        2. If resulting chunks are still too large, try next separator
        3. Recursively split until all chunks are within size limit
        4. Add overlap between consecutive chunks
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text] if text else []
        
        # Find the best separator for this text
        chunks = self._split_with_separators(text, self.separators)
        
        # Add overlap between chunks
        if self.chunk_overlap > 0:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _split_with_separators(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text using list of separators
        
        Args:
            text: Text to split
            separators: List of separators to try
            
        Returns:
            List of chunks
        """
        if not separators:
            # Last resort: character-level splitting
            return self._character_split(text)
        
        # Try current separator
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if separator == "":
            # Character-level split
            return self._character_split(text)
        
        # Split on current separator
        splits = text.split(separator)
        
        # Rebuild chunks, keeping separator
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, split in enumerate(splits):
            # Add separator back (except for last split)
            if i < len(splits) - 1:
                split_with_sep = split + separator
            else:
                split_with_sep = split
            
            split_size = len(split_with_sep)
            
            # Check if adding this split exceeds chunk size
            if current_size + split_size <= self.chunk_size:
                current_chunk.append(split_with_sep)
                current_size += split_size
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append("".join(current_chunk))
                
                # Check if this split itself is too large
                if split_size > self.chunk_size and remaining_separators:
                    # Recursively split this piece with next separator
                    sub_chunks = self._split_with_separators(split_with_sep, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = []
                    current_size = 0
                else:
                    # Start new chunk with this split
                    current_chunk = [split_with_sep]
                    current_size = split_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append("".join(current_chunk))
        
        return chunks
    
    def _character_split(self, text: str) -> List[str]:
        """
        Split text at character level (last resort)
        
        Args:
            text: Text to split
            
        Returns:
            List of chunks
        """
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """
        Add overlap between consecutive chunks
        
        Args:
            chunks: List of chunks without overlap
            
        Returns:
            List of chunks with overlap
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i in range(len(chunks)):
            chunk = chunks[i]
            
            # Add overlap from previous chunk
            if i > 0 and self.chunk_overlap > 0:
                prev_chunk = chunks[i - 1]
                overlap = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) >= self.chunk_overlap else prev_chunk
                chunk = overlap + chunk
            
            overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    def split_documents(self, documents: List[str], add_metadata: bool = False) -> List[dict]:
        """
        Split multiple documents into chunks with optional metadata
        
        Args:
            documents: List of document texts
            add_metadata: Whether to add metadata (doc index, chunk index)
            
        Returns:
            List of dictionaries with 'text' and optional 'metadata'
        """
        all_chunks = []
        
        for doc_idx, doc in enumerate(documents):
            chunks = self.split_text(doc)
            
            for chunk_idx, chunk in enumerate(chunks):
                if add_metadata:
                    all_chunks.append({
                        'text': chunk,
                        'metadata': {
                            'doc_index': doc_idx,
                            'chunk_index': chunk_idx,
                            'total_chunks': len(chunks)
                        }
                    })
                else:
                    all_chunks.append({'text': chunk})
        
        return all_chunks


class TextPreprocessor:
    """
    Custom text preprocessing utilities
    """
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Remove extra whitespace and normalize newlines"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    @staticmethod
    def remove_urls(text: str) -> str:
        """Remove URLs from text"""
        url_pattern = r'https?://\S+|www\.\S+'
        return re.sub(url_pattern, '', text)
    
    @staticmethod
    def remove_emails(text: str) -> str:
        """Remove email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, '', text)
    
    @staticmethod
    def remove_special_chars(text: str, keep_chars: str = '.!?,;:') -> str:
        """
        Remove special characters except specified ones
        
        Args:
            text: Input text
            keep_chars: Characters to keep (default: punctuation)
        """
        pattern = f'[^a-zA-Z0-9\\s{re.escape(keep_chars)}]'
        return re.sub(pattern, '', text)
    
    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """
        Extract sentences from text
        
        Uses simple heuristics for sentence boundary detection
        """
        # Split on sentence-ending punctuation followed by space
        sentences = re.split(r'[.!?]+\s+', text)
        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text"""
        return len(text.split())
    
    @staticmethod
    def count_sentences(text: str) -> int:
        """Count sentences in text"""
        return len(TextPreprocessor.extract_sentences(text))
    
    @staticmethod
    def get_text_stats(text: str) -> dict:
        """
        Get comprehensive text statistics
        
        Returns:
            Dictionary with various text metrics
        """
        sentences = TextPreprocessor.extract_sentences(text)
        words = text.split()
        
        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'whitespace_ratio': text.count(' ') / len(text) if text else 0
        }


if __name__ == "__main__":
    # Test text chunking
    print("Testing Custom Text Chunker")
    print("=" * 70)
    
    # Sample document
    sample_text = """
    Machine learning is a subset of artificial intelligence (AI) that provides systems 
    the ability to automatically learn and improve from experience without being explicitly 
    programmed. Machine learning focuses on the development of computer programs that can 
    access data and use it to learn for themselves.
    
    The process of learning begins with observations or data, such as examples, direct 
    experience, or instruction, in order to look for patterns in data and make better 
    decisions in the future based on the examples that we provide. The primary aim is to 
    allow the computers learn automatically without human intervention or assistance and 
    adjust actions accordingly.
    
    Some machine learning methods include supervised learning, unsupervised learning, 
    semi-supervised learning, and reinforcement learning. Each method has its own 
    advantages and use cases.
    """
    
    print(f"Original text length: {len(sample_text)} characters")
    print(f"Original text preview: {sample_text[:100]}...")
    
    # Test chunking
    print("\n1. Basic Chunking (chunk_size=200, overlap=50)")
    print("-" * 70)
    chunker = TextChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.split_text(sample_text)
    
    print(f"Number of chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} (length: {len(chunk)}):")
        print(f"  {chunk[:80]}...")
    
    # Test with metadata
    print("\n2. Chunking with Metadata")
    print("-" * 70)
    documents = [sample_text[:300], sample_text[300:]]
    chunker2 = TextChunker(chunk_size=150, chunk_overlap=30)
    chunks_with_meta = chunker2.split_documents(documents, add_metadata=True)
    
    print(f"Total chunks from {len(documents)} documents: {len(chunks_with_meta)}")
    for chunk_data in chunks_with_meta[:3]:
        meta = chunk_data['metadata']
        print(f"\n  Doc {meta['doc_index']}, Chunk {meta['chunk_index']}/{meta['total_chunks']}")
        print(f"  Text: {chunk_data['text'][:60]}...")
    
    # Test preprocessing
    print("\n3. Text Preprocessing")
    print("-" * 70)
    preprocessor = TextPreprocessor()
    
    messy_text = "Visit   https://example.com  or email  test@example.com  for   more   info!!!"
    print(f"Original: {messy_text}")
    
    cleaned = preprocessor.normalize_whitespace(messy_text)
    print(f"Normalized whitespace: {cleaned}")
    
    no_urls = preprocessor.remove_urls(cleaned)
    print(f"URLs removed: {no_urls}")
    
    no_emails = preprocessor.remove_emails(no_urls)
    print(f"Emails removed: {no_emails}")
    
    # Text statistics
    print("\n4. Text Statistics")
    print("-" * 70)
    stats = preprocessor.get_text_stats(sample_text)
    print(f"Character count: {stats['char_count']}")
    print(f"Word count: {stats['word_count']}")
    print(f"Sentence count: {stats['sentence_count']}")
    print(f"Average word length: {stats['avg_word_length']:.2f}")
    print(f"Average sentence length: {stats['avg_sentence_length']:.2f} words")
    
    print("\n✅ All tests completed successfully!")
