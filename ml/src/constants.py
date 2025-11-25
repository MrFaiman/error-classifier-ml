import os

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Model paths
CHECKPOINT_DIR = os.path.join(MODELS_DIR, 'checkpoints')
CHROMA_DB_DIR = os.path.join(MODELS_DIR, 'chroma_db')

# Data paths
DOCS_ROOT_DIR = os.path.join(DATA_DIR, 'services')
DATASET_PATH = os.path.join(DATA_DIR, 'dataset', 'errors_dataset.csv')
INPUT_EXAMPLES_PATH = os.path.join(DATA_DIR, 'input_examples.json')

# Model configuration
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
# Chunking configuration for LangChain
CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 50  # Overlap between chunks
# API configuration
API_PORT = 3100