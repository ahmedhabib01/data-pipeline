import os
from dotenv import load_dotenv

load_dotenv()

# ── Folder Paths ──────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR       = os.path.join(BASE_DIR, 'data')
QUARANTINE_DIR = os.path.join(BASE_DIR, 'quarantine')
LOG_DIR        = os.path.join(BASE_DIR, 'logs')
SAMPLE_DIR     = os.path.join(BASE_DIR, 'sample_data', 'batches')

# ── Database Config ───────────────────────────────────────
DB_CONFIG = {
    'host'    : os.getenv('DB_HOST', 'localhost'),
    'port'    : os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'sensor_pipeline'),
    'user'    : os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
}

DB_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# ── Watcher Config ────────────────────────────────────────
WATCH_INTERVAL = 5  # seconds between folder scans

# ── Validation Rules ──────────────────────────────────────
REQUIRED_COLUMNS = ['ts', 'device', 'co', 'humidity', 'light', 'lpg', 'motion', 'smoke', 'temp']

NUMERIC_COLUMNS  = ['co', 'humidity', 'lpg', 'smoke', 'temp']
BOOLEAN_COLUMNS  = ['light', 'motion']

VALUE_RANGES = {
    'temp'    : (-50, 50),
    'humidity': (0, 100),
    'co'      : (0, 1),
    'lpg'     : (0, 1),
    'smoke'   : (0, 1),
}

# ── Retry Config ──────────────────────────────────────────
MAX_RETRIES    = 3
RETRY_DELAY    = 5  # seconds