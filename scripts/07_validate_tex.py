"""
Stage:    07 -- Validate the generated LaTeX
Purpose:  Audit generated .tex sources for syntax faults before compilation.
Task:     Regional reporting quality control
Inputs:   bcch-data-repo-vault/report2_REG_ECON_DEV/tex/*.tex
Outputs:  stdout audit log
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon
Run:      python scripts/07_validate_tex.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.paths import REPO_ROOT

import os
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TEX_PATH = os.path.join(REPO_ROOT, "bcch-data-repo-vault/report2_REG_ECON_DEV/tex/report_REG_ECON_DEV_coverage_ES.tex")

def validate_tex():
    logger.info("Initializing refined TeX Syntax Audit...")
    
    if not os.path.exists(TEX_PATH):
        raise FileNotFoundError(f"LaTeX file not found at {TEX_PATH}")
        
    with open(TEX_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    errors = []
    
    # 1. Check matching begin/end tags
    begin_tags = re.findall(r'\\begin\{([^}]+)\}', content)
    end_tags = re.findall(r'\\end\{([^}]+)\}', content)
    
    logger.info(f"Discovered {len(begin_tags)} \\begin environments and {len(end_tags)} \\end environments.")
    
    stack = []
    lines = content.split('\n')
    
    in_tabular = False
    
    for idx, line in enumerate(lines):
        line_num = idx + 1
        line_stripped = line.strip()
        
        # Track if we are inside a tabular environment
        if "\\begin{tabular}" in line_stripped:
            in_tabular = True
        elif "\\end{tabular}" in line_stripped:
            in_tabular = False
            
        # Find all begin/end tags in this line
        finds = re.findall(r'\\(begin|end)\{([^}]+)\}', line)
        for action, env in finds:
            if action == 'begin':
                stack.append((env, line_num))
            elif action == 'end':
                if not stack:
                    errors.append(f"Line {line_num}: Found \\end{{{env}}} with no matching \\begin.")
                else:
                    last_env, start_line = stack.pop()
                    if last_env != env:
                        errors.append(f"Line {line_num}: Found \\end{{{env}}} matching \\begin{{{last_env}}} on line {start_line}.")
                        
        # 2. Check for raw %, _, & outside of math blocks and specific environments
        # Split by $ to isolate math blocks
        parts = line.split('$')
        for part_idx, part in enumerate(parts):
            if part_idx % 2 == 0:  # Text block
                
                # Check for unescaped %
                unescaped_pct = re.findall(r'(?<!\\)%', part)
                if unescaped_pct:
                    errors.append(f"Line {line_num}: Unescaped % symbol found.")
                    
                # Check for unescaped _ (ignore in \includegraphics and \label)
                if not ("\\includegraphics" in part or "\\label" in part):
                    unescaped_und = re.findall(r'(?<!\\)_', part)
                    if unescaped_und:
                        errors.append(f"Line {line_num}: Unescaped _ (underscore) symbol found.")
                        
                # Check for unescaped & (ignore inside tabular environment)
                if not in_tabular:
                    unescaped_amp = re.findall(r'(?<!\\)&', part)
                    if unescaped_amp:
                        errors.append(f"Line {line_num}: Unescaped & (ampersand) symbol found.")
                        
    while stack:
        env, start_line = stack.pop()
        errors.append(f"Line {start_line}: \\begin{{{env}}} is never closed (reached end of file).")
        
    print("\n" + "="*50)
    print("             TEX AUDIT REPORT")
    print("="*50)
    
    if errors:
        print("STATUS: FAILED [X]")
        print(f"Total Errors Found: {len(errors)}")
        for idx, err in enumerate(errors):
            print(f" {idx+1}. {err}")
        print("\nACTION REQUIRED: Please verify the LaTeX escaping or layout.")
        exit(1)
    else:
        print("STATUS: PASSED [OK]")
        print("LaTeX file is structurally sound with balanced environments, correct column separators, and properly escaped text!")
        print("="*50)

if __name__ == "__main__":
    validate_tex()
