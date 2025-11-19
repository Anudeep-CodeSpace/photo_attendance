import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Admin API Token
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

# Qdrant settings
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

# Embedding dimension (set to what your model uses)
VECTOR_DIMENSION = os.getenv("VECTOR_DIMENSIONS")  # or 512 for antelopev2

# RetinaFace detector
DETECTOR_MODEL_NAME = os.getenv("DETECTOR_MODEL_NAME", "buffalo_l")  # or your MobileNet-based RetinaFace
DETECTOR_PROVIDER = os.getenv("DETECTOR_PROVIDER", "CPUExecutionProvider")

# InsightFace embedding model
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "buffalo_l")  # or mobilefacenet.onnx
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "CPUExecutionProvider")

# Collection name in Qdrant
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "face_embeddings")
