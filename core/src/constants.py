import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ML_DIR, 'models')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Model paths (kept for backward compatibility)
CHECKPOINT_DIR = os.path.join(MODELS_DIR, 'checkpoints')

# Data paths
DOCS_ROOT_DIR = os.path.join(DATA_DIR, 'services')
DATASET_PATH = os.path.join(DATA_DIR, 'dataset', 'errors_dataset.csv')
INPUT_EXAMPLES_PATH = os.path.join(DATA_DIR, 'input_examples.json')

# MongoDB Configuration
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING', 'mongodb://localhost:27017/')

# API configuration
API_PORT = 3100