"""
Purpose:  Shared helpers for the reporting stages -- LaTeX escaping and table
          export -- so the producer and validator cannot drift apart.
Task:     Regional economic development reporting
Inputs:   n/a
Outputs:  writes CSV tables when export_table_to_csv is called
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
"""

import logging
import os
from typing import Optional

import pandas as pd

from lib.paths import VAULT_ASSETS_DIR, ensure_dir

logger = logging.getLogger(__name__)

# Characters that are syntactically meaningful in LaTeX text mode.
LATEX_ESCAPES = {"%": r"\%", "_": r"\_", "&": r"\&", "#": r"\#"}


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters, leaving math blocks untouched.

    Math is delimited by `$`, so odd-indexed segments of a `$`-split are inside
    math mode and must pass through unescaped -- escaping `_` there would break
    subscripts.
    """
    if not text:
        return ""

    parts = str(text).split("$")
    for i, part in enumerate(parts):
        if i % 2 == 0:  # text block
            for char, replacement in LATEX_ESCAPES.items():
                part = part.replace(char, replacement)
            parts[i] = part
    return "$".join(parts)


def export_table_to_csv(
    df: pd.DataFrame, filename: str, assets_dir: Optional[str] = None
) -> str:
    """Write a table to the vault assets directory and return its path."""
    target = ensure_dir(VAULT_ASSETS_DIR if assets_dir is None else __import__("pathlib").Path(assets_dir))
    path = os.path.join(str(target), filename)
    df.to_csv(path, index=False)
    logger.info("Saved Table CSV: %s", filename)
    return path
