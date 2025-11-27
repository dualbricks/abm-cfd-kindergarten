import os
import sys
from pathlib import Path

os.environ["VADERE_PATH"] = "INSERT VADERE PATH"
sys.path.append(os.path.abspath(".."))

VADERE_PATH = os.environ["VADERE_PATH"]

OUTPUT_PATH = "INSERT OUPUT PATH"

PROJECT_PATH = Path(__file__).resolve().parent
