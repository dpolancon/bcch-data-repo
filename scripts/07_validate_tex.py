"""
Stage:    07 -- Validate the generated LaTeX
Purpose:  Audit generated .tex sources for syntax faults before compilation.
Task:     Regional reporting quality control
Inputs:   bcch-data-repo-vault/report2_REG_ECON_DEV/tex/*.tex
Outputs:  stdout audit log
Created:  2026-07-06
Updated:  2026-08-22
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

# Both generated LaTeX documents. Only the coverage report used to be checked,
# so the analysis LaTeX that stage 05 produces was never validated at all.
TEX_PATHS = [
    os.path.join(REPO_ROOT, "bcch-data-repo-vault", "report1_REG_ECON_DEV", "tex_es",
                 "report_REG_ECON_DEV_ES.tex"),
    os.path.join(REPO_ROOT, "bcch-data-repo-vault", "report2_REG_ECON_DEV", "tex",
                 "report_REG_ECON_DEV_coverage_ES.tex"),
]

def validate_tex(tex_path):
    logger.info("Auditing %s", os.path.basename(tex_path))

    if not os.path.exists(tex_path):
        raise FileNotFoundError(f"LaTeX file not found at {tex_path}")

    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    errors = []
    
    # 1. Check matching begin/end tags
    begin_tags = re.findall(r'\\begin\{([^}]+)\}', content)
    end_tags = re.findall(r'\\end\{([^}]+)\}', content)
    
    logger.info(f"Discovered {len(begin_tags)} \\begin environments and {len(end_tags)} \\end environments.")
    
    stack = []
    lines = content.split('\n')
    
    in_tabular = False
    in_math_env = False

    # Environments whose bodies are math mode, where _ and ^ are meaningful and
    # must NOT be escaped. Without these the validator reported every subscript
    # in every displayed equation as an error.
    MATH_ENVS = {"equation", "equation*", "align", "align*", "displaymath",
                 "eqnarray", "eqnarray*", "gather", "gather*", "multline"}
    # Commands whose braced argument is an identifier, not prose.
    IDENT_ARG = re.compile(
        r"\\(?:ref|label|cite|includegraphics|input|include|url|href)\s*(?:\[[^\]]*\])?\{[^}]*\}"
    )

    for idx, line in enumerate(lines):
        line_num = idx + 1
        line_stripped = line.strip()
        
        # Track if we are inside a tabular environment
        if "\\begin{tabular}" in line_stripped:
            in_tabular = True
        elif "\\end{tabular}" in line_stripped:
            in_tabular = False

        # Track math environments. Their bodies are math mode, where _ and ^
        # are syntax rather than text, so escaping rules do not apply. Without
        # this every subscript in every displayed equation was reported as an
        # unescaped underscore.
        for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", line_stripped):
            if m.group(2) in MATH_ENVS:
                in_math_env = m.group(1) == "begin"
            
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
        if in_math_env:
            continue  # math body: _ and ^ are syntax, not text

        # Strip identifier arguments before checking: the braced argument of
        # ref, label, cite and includegraphics is an identifier or a path, so
        # underscores there are legitimate rather than unescaped prose.
        line = IDENT_ARG.sub("", line)
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
        raise SystemExit(1)
    else:
        print("STATUS: PASSED [OK]")
        print("LaTeX file is structurally sound with balanced environments, correct column separators, and properly escaped text!")
        print("="*50)

def main():
    """Validate every generated LaTeX document, reporting all of them.

    Runs all files before exiting so a fault in the first does not hide faults
    in the second.
    """
    failed = []
    for tex_path in TEX_PATHS:
        try:
            validate_tex(tex_path)
        except SystemExit:
            failed.append(os.path.basename(tex_path))
        except FileNotFoundError as exc:
            logger.error("%s", exc)
            failed.append(os.path.basename(tex_path))

    if failed:
        print(f"\nFAILED: {', '.join(failed)}")
        raise SystemExit(1)
    print("\nAll generated LaTeX documents passed validation.")


if __name__ == "__main__":
    main()
