## Where the evaluation outputs get written. Kept in one place so every script agrees,
## and so the paths work no matter which directory you run the scripts from.

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

Q_TABLE = PROJECT_ROOT / "q_table_trained"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
PLOTS_DIR = PROJECT_ROOT / "evaluation" / "plots"

MATCHUPS_CSV = RESULTS_DIR / "matchups.csv"
CURVES_JSON = RESULTS_DIR / "curves.json"
STUDY_CSV = RESULTS_DIR / "study.csv"
RESULTS_MD = RESULTS_DIR / "results.md"


def ensure_dirs():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
