from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        # We load the free, powerful MiniLM model.
        # It converts text into a mathematical vector of length 384.
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_embedding(self, text: str) -> list[float]:
        """Convert a text string into a list of floats (the embedding)."""
        if not text:
            return []
        
        # The model returns a numpy array, we convert it to a normal Python list
        embedding_array = self.model.encode(text)
        return embedding_array.tolist()

# Create a single instance to be used across the app
embedding_service = EmbeddingService()
