"""
Custom Edit Distance and Fuzzy Matching Implementation
Implements Levenshtein distance and fuzzy string matching from scratch
"""
import numpy as np
from typing import List, Tuple


class EditDistance:
    """
    Edit distance (Levenshtein distance) calculator
    
    Levenshtein distance is the minimum number of single-character edits 
    (insertions, deletions, or substitutions) required to change one string into another.
    
    This is useful for fuzzy matching and finding similar errors even with typos.
    """
    
    @staticmethod
    def levenshtein(s1: str, s2: str, case_sensitive: bool = False) -> int:
        """
        Calculate Levenshtein distance between two strings
        
        Algorithm: Dynamic Programming approach using a matrix
        - Matrix[i][j] represents the distance between s1[0:i] and s2[0:j]
        - We fill the matrix by considering three operations:
          1. Insertion: Matrix[i][j-1] + 1
          2. Deletion: Matrix[i-1][j] + 1
          3. Substitution: Matrix[i-1][j-1] + (0 if chars match, 1 if different)
        
        Args:
            s1: First string
            s2: Second string
            case_sensitive: Whether to consider case
            
        Returns:
            Edit distance (number of edits needed)
        """
        if not case_sensitive:
            s1 = s1.lower()
            s2 = s2.lower()
        
        m, n = len(s1), len(s2)
        
        # Create distance matrix
        # dp[i][j] = minimum edits to transform s1[0:i] to s2[0:j]
        dp = np.zeros((m + 1, n + 1), dtype=int)
        
        # Initialize base cases
        # Transforming empty string to s2[0:j] requires j insertions
        for j in range(n + 1):
            dp[0][j] = j
        
        # Transforming s1[0:i] to empty string requires i deletions
        for i in range(m + 1):
            dp[i][0] = i
        
        # Fill the matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    # Characters match, no edit needed
                    dp[i][j] = dp[i-1][j-1]
                else:
                    # Take minimum of three operations
                    dp[i][j] = 1 + min(
                        dp[i-1][j],      # Deletion
                        dp[i][j-1],      # Insertion
                        dp[i-1][j-1]     # Substitution
                    )
        
        return int(dp[m][n])
    
    @staticmethod
    def similarity_ratio(s1: str, s2: str, case_sensitive: bool = False) -> float:
        """
        Calculate similarity ratio between two strings (0.0 to 1.0)
        
        Similarity = 1 - (edit_distance / max_length)
        
        Args:
            s1: First string
            s2: Second string
            case_sensitive: Whether to consider case
            
        Returns:
            Similarity ratio (1.0 = identical, 0.0 = completely different)
        """
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        distance = EditDistance.levenshtein(s1, s2, case_sensitive)
        similarity = 1.0 - (distance / max_len)
        
        return similarity
    
    @staticmethod
    def damerau_levenshtein(s1: str, s2: str) -> int:
        """
        Calculate Damerau-Levenshtein distance (allows transpositions)
        
        Extends Levenshtein distance by allowing transposition of adjacent characters
        (e.g., "ab" -> "ba" is 1 edit instead of 2)
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Damerau-Levenshtein distance
        """
        m, n = len(s1), len(s2)
        
        # Create distance matrix with extra space for transpositions
        dp = np.zeros((m + 1, n + 1), dtype=int)
        
        # Initialize
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        # Fill matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # Deletion
                    dp[i][j-1] + 1,      # Insertion
                    dp[i-1][j-1] + cost  # Substitution
                )
                
                # Check for transposition
                if i > 1 and j > 1 and s1[i-1] == s2[j-2] and s1[i-2] == s2[j-1]:
                    dp[i][j] = min(dp[i][j], dp[i-2][j-2] + cost)
        
        return int(dp[m][n])


class FuzzyMatcher:
    """
    Fuzzy string matching using edit distance
    """
    
    def __init__(self, strings: List[str], case_sensitive: bool = False):
        """
        Initialize fuzzy matcher with a list of reference strings
        
        Args:
            strings: List of reference strings to match against
            case_sensitive: Whether matching is case-sensitive
        """
        self.strings = strings
        self.case_sensitive = case_sensitive
        
    def find_closest_match(self, query: str, top_k: int = 1) -> List[Tuple[str, float, int]]:
        """
        Find the closest matching string(s) using edit distance
        
        Args:
            query: Query string to match
            top_k: Number of matches to return
            
        Returns:
            List of tuples: (matched_string, similarity_ratio, edit_distance)
        """
        matches = []
        
        for ref_string in self.strings:
            distance = EditDistance.levenshtein(query, ref_string, self.case_sensitive)
            similarity = EditDistance.similarity_ratio(query, ref_string, self.case_sensitive)
            matches.append((ref_string, similarity, distance))
        
        # Sort by similarity (descending) and distance (ascending)
        matches.sort(key=lambda x: (-x[1], x[2]))
        
        return matches[:top_k]
    
    def find_matches_above_threshold(self, query: str, threshold: float = 0.7) -> List[Tuple[str, float, int]]:
        """
        Find all matches with similarity above threshold
        
        Args:
            query: Query string
            threshold: Minimum similarity ratio (0.0 to 1.0)
            
        Returns:
            List of tuples: (matched_string, similarity_ratio, edit_distance)
        """
        matches = []
        
        for ref_string in self.strings:
            similarity = EditDistance.similarity_ratio(query, ref_string, self.case_sensitive)
            if similarity >= threshold:
                distance = EditDistance.levenshtein(query, ref_string, self.case_sensitive)
                matches.append((ref_string, similarity, distance))
        
        # Sort by similarity
        matches.sort(key=lambda x: -x[1])
        
        return matches
    
    def is_fuzzy_match(self, query: str, max_distance: int = 2) -> bool:
        """
        Check if query fuzzy matches any reference string
        
        Args:
            query: Query string
            max_distance: Maximum allowed edit distance
            
        Returns:
            True if any match found within max_distance
        """
        for ref_string in self.strings:
            distance = EditDistance.levenshtein(query, ref_string, self.case_sensitive)
            if distance <= max_distance:
                return True
        return False


def fuzzy_search(query: str, documents: List[str], top_k: int = 5) -> List[Tuple[int, str, float]]:
    """
    Perform fuzzy search on documents using edit distance
    
    Args:
        query: Search query
        documents: List of documents to search
        top_k: Number of results to return
        
    Returns:
        List of tuples: (doc_index, document, similarity_score)
    """
    results = []
    
    for idx, doc in enumerate(documents):
        # Calculate similarity for entire document
        similarity = EditDistance.similarity_ratio(query, doc)
        results.append((idx, doc, similarity))
    
    # Sort by similarity
    results.sort(key=lambda x: -x[2])
    
    return results[:top_k]


if __name__ == "__main__":
    # Test edit distance implementations
    print("Testing Custom Edit Distance and Fuzzy Matching")
    print("=" * 70)
    
    # Test 1: Basic Levenshtein distance
    print("\n1. Levenshtein Distance")
    print("-" * 70)
    
    test_pairs = [
        ("kitten", "sitting"),
        ("saturday", "sunday"),
        ("book", "back"),
        ("python", "python"),  # Identical
        ("", "abc"),  # Empty string
    ]
    
    for s1, s2 in test_pairs:
        distance = EditDistance.levenshtein(s1, s2)
        similarity = EditDistance.similarity_ratio(s1, s2)
        print(f"'{s1}' <-> '{s2}':")
        print(f"  Distance: {distance}")
        print(f"  Similarity: {similarity:.2%}")
    
    # Test 2: Case sensitivity
    print("\n2. Case Sensitivity")
    print("-" * 70)
    s1, s2 = "Hello", "hello"
    case_sensitive_dist = EditDistance.levenshtein(s1, s2, case_sensitive=True)
    case_insensitive_dist = EditDistance.levenshtein(s1, s2, case_sensitive=False)
    print(f"'{s1}' <-> '{s2}':")
    print(f"  Case-sensitive distance: {case_sensitive_dist}")
    print(f"  Case-insensitive distance: {case_insensitive_dist}")
    
    # Test 3: Damerau-Levenshtein (with transpositions)
    print("\n3. Damerau-Levenshtein Distance (with transpositions)")
    print("-" * 70)
    s1, s2 = "abcd", "abdc"
    lev_dist = EditDistance.levenshtein(s1, s2)
    dam_lev_dist = EditDistance.damerau_levenshtein(s1, s2)
    print(f"'{s1}' <-> '{s2}' (transposed 'cd'):")
    print(f"  Levenshtein: {lev_dist} (2 substitutions)")
    print(f"  Damerau-Levenshtein: {dam_lev_dist} (1 transposition)")
    
    # Test 4: Fuzzy matching
    print("\n4. Fuzzy Matching")
    print("-" * 70)
    
    error_types = [
        "SECURITY_ALERT",
        "NEGATIVE_VALUE",
        "SCHEMA_VALIDATION",
        "GEO_OUT_OF_BOUNDS",
        "REGEX_MISMATCH",
        "MISSING_FIELD"
    ]
    
    matcher = FuzzyMatcher(error_types, case_sensitive=False)
    
    queries = [
        "SECURITY_ALRT",   # Typo
        "negative value",  # Case difference
        "SCHEMA_VALID",    # Partial match
        "GEO_BOUNDS"       # Missing part
    ]
    
    for query in queries:
        matches = matcher.find_closest_match(query, top_k=3)
        print(f"\nQuery: '{query}'")
        print("  Top 3 matches:")
        for match, similarity, distance in matches:
            print(f"    {match}: {similarity:.2%} similarity (distance: {distance})")
    
    # Test 5: Threshold-based matching
    print("\n5. Threshold-Based Matching")
    print("-" * 70)
    query = "SECURITY"
    threshold = 0.5
    matches = matcher.find_matches_above_threshold(query, threshold=threshold)
    print(f"Query: '{query}'")
    print(f"Matches with similarity >= {threshold:.0%}:")
    for match, similarity, distance in matches:
        print(f"  {match}: {similarity:.2%}")
    
    # Test 6: Fuzzy document search
    print("\n6. Fuzzy Document Search")
    print("-" * 70)
    documents = [
        "Error: Invalid user credentials provided",
        "Warning: Database connection timeout",
        "Error: Schema validation failed for user input",
        "Info: User login successful"
    ]
    
    query = "user validation error"
    results = fuzzy_search(query, documents, top_k=3)
    
    print(f"Query: '{query}'")
    print("Top 3 matching documents:")
    for idx, doc, similarity in results:
        print(f"  [{idx}] {similarity:.2%} - {doc}")
    
    print("\n✅ All tests completed successfully!")
