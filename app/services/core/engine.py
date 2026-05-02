import math
import re

class SearchEngine:
    @staticmethod
    def tokenize(text):
        """Tokenize text into lowercase words."""
        if not text:
            return []
        return re.findall(r'\w+', text.lower())

    @staticmethod
    def calculate_tf(tokens):
        """Calculate Term Frequency (TF) for a list of tokens."""
        if not tokens:
            return {}
        freqs = {}
        for token in tokens:
            freqs[token] = freqs.get(token, 0) + 1
        
        total_tokens = len(tokens)
        return {token: count / total_tokens for token, count in freqs.items()}

    @staticmethod
    def calculate_idf(num_docs, docs_with_word):
        """Calculate Inverse Document Frequency (IDF)."""
        if docs_with_word == 0:
            return 0
        return math.log10(num_docs / docs_with_word)

    @staticmethod
    def calculate_cosine_similarity(query_vector, doc_vector):
        """Calculate Cosine Similarity between two vectors (dicts of word: weight)."""
        # Intersection of words
        common_words = set(query_vector.keys()) & set(doc_vector.keys())
        
        dot_product = sum(query_vector[word] * doc_vector[word] for word in common_words)
        
        norm_q = math.sqrt(sum(weight ** 2 for weight in query_vector.values()))
        norm_d = math.sqrt(sum(weight ** 2 for weight in doc_vector.values()))
        
        if norm_q == 0 or norm_d == 0:
            return 0
            
        return dot_product / (norm_q * norm_d)

    def get_query_vector(self, query, idf_provider_func):
        """
        Generate query vector (TF-IDF).
        idf_provider_func should take a word and return its IDF.
        """
        tokens = self.tokenize(query)
        tf_map = self.calculate_tf(tokens)
        
        query_vector = {}
        for word, tf in tf_map.items():
            idf = idf_provider_func(word)
            query_vector[word] = tf * idf
            
        return query_vector
