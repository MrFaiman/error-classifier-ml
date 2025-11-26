import os

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

# API configuration
API_PORT = 3100