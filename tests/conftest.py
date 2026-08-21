"""
Purpose:  Put the scripts/ directory on sys.path so tests can `import lib.*`
          exactly as the pipeline stages do.
Task:     Repository infrastructure
Inputs:   n/a
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
"""

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
