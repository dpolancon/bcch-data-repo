"""
Stage:    06 -- Generate the coverage LaTeX
Purpose:  Format the coverage inventory and figures into LaTeX sources for the
          data coverage report.
Task:     Regional data coverage reporting
Inputs:   bcch-data-repo-vault/report2_REG_ECON_DEV/assets/*
Outputs:  bcch-data-repo-vault/report2_REG_ECON_DEV/tex/*.tex
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon
Run:      python scripts/06_generate_coverage_tex.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.paths import REPO_ROOT

import os
import re
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
ROOT_DIR = str(REPO_ROOT)
REPORT_DIR = os.path.join(ROOT_DIR, "bcch-data-repo-vault", "report2_REG_ECON_DEV")
ASSETS_DIR = os.path.join(REPORT_DIR, "assets")
TEX_DIR = os.path.join(REPORT_DIR, "tex")
os.makedirs(TEX_DIR, exist_ok=True)

MD_PATH = os.path.join(REPORT_DIR, "data_coverage_report_ES.md")
TEX_PATH = os.path.join(TEX_DIR, "report_REG_ECON_DEV_coverage_ES.tex")

def escape_latex(text):
    """
    Escapes LaTeX special characters outside of math blocks.
    Math blocks are delimited by $.
    """
    if not text:
        return ""
    
    parts = text.split('$')
    for i in range(len(parts)):
        if i % 2 == 0:  # Text block (even index)
            t = parts[i]
            # Escape %, _, &, #
            t = t.replace('%', '\\%')
            t = t.replace('_', '\\_')
            t = t.replace('&', '\\&')
            t = t.replace('#', '\\#')
            parts[i] = t
        else:  # Math block (odd index)
            # Do not escape math blocks
            pass
            
    return '$'.join(parts)

def parse_md_to_tex():
    logger.info("Starting Markdown to LaTeX parsing...")
    
    if not os.path.exists(MD_PATH):
        raise FileNotFoundError(f"Markdown report not found at {MD_PATH}")
        
    with open(MD_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    tex_content = []
    
    # Document header
    tex_content.append(r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{hyperref}
\usepackage{caption}
\usepackage{float}
\usepackage{microtype}
\usepackage{adjustbox}

\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=cyan,
    pdftitle={Reporte de Cobertura de Datos Regionales - BCCh},
    pdfpagemode=FullScreen,
}

\title{\textbf{Reporte de Cobertura de Datos Regionales:\\ Banco Central de Chile (BCCh)}}
\author{\textbf{Análisis de Macro-Datos y Desarrollo Regional}}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
Este reporte presenta una auditoría exhaustiva y un análisis de cobertura de todas las series de datos a nivel regional (16 regiones administrativas, $r = 1 \dots 16$) y sectorial ($s = 1 \dots 12$) disponibles a través de la API del Banco Central de Chile (BCCh). Esta versión expandida pone especial énfasis en el \textbf{Desarrollo Sectorial Integrado}, analizando conjuntamente las variables del \textbf{Sistema Financiero Regional} (cuentas corrientes y cuentas vista) y los indicadores de \textbf{Uso de Suelo y Desarrollo Territorial} (metros cuadrados de edificación autorizados y superficies comerciales).
\end{abstract}

\strut
""")
    
    in_itemize = False
    in_enumerate = False
    in_table = False
    table_rows = []
    table_cols_count = 0
    
    # Regex patterns
    bold_pattern = re.compile(r'\*\*([^*]+)\*\*')
    italic_pattern = re.compile(r'\*([^*]+)\*')
    image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    
    # Skip the title line and intro since we put them in abstract/title
    skip_intro = True
    
    for idx, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Determine if we should skip intro lines
        if skip_intro:
            if line_stripped.startswith("## **1. Resumen Ejecutivo"):
                skip_intro = False
            else:
                continue
                
        # Close list environments if next line is not a list item
        is_bullet = line_stripped.startswith("- ") or line_stripped.startswith("* ")
        is_numbered = re.match(r'^\d+\.\s', line_stripped) is not None
        
        if in_itemize and not is_bullet and line_stripped:
            tex_content.append("\\end{itemize}\n")
            in_itemize = False
        if in_enumerate and not is_numbered and line_stripped:
            tex_content.append("\\end{enumerate}\n")
            in_enumerate = False
            
        # Close table environment if table ends
        is_table_row = line_stripped.startswith("|")
        if in_table and not is_table_row:
            # We finished a table, format it
            if table_rows:
                header = table_rows[0]
                rows = table_rows[1:]
                
                col_format = "l" + "c" * (table_cols_count - 1)
                tex_content.append("\\begin{table}[H]\n\\centering\n")
                tex_content.append(f"\\caption{{Matriz Comparativa Regional Seleccionada: Indicadores Financieros y Físicos de Suelo}}\n")
                tex_content.append(f"\\begin{{adjustbox}}{{width=\\textwidth}}\n")
                tex_content.append(f"\\begin{{tabular}}{{{col_format}}}\n\\toprule\n")
                
                # Header row
                tex_content.append(" & ".join(header) + " \\\\\n\\midrule\n")
                
                # Body rows
                for r in rows:
                    tex_content.append(" & ".join(r) + " \\\\\n")
                    
                tex_content.append("\\bottomrule\n\\end{tabular}\n\\end{adjustbox}\n\\end{table}\n\n")
                
            in_table = False
            table_rows = []
            
        # Parse line content (bold, italics, etc.)
        parsed_line = line_stripped
        
        # Replace bold and italics
        parsed_line = bold_pattern.sub(r'\\textbf{\1}', parsed_line)
        parsed_line = italic_pattern.sub(r'\\textit{\1}', parsed_line)
        
        # Replace image links
        img_match = image_pattern.search(parsed_line)
        if img_match:
            caption = img_match.group(1)
            img_path = img_match.group(2)
            # Extract filename
            img_name = os.path.basename(img_path)
            
            tex_content.append(f"""\\begin{{figure}}[H]
\\centering
\\includegraphics[width=0.85\\textwidth]{{{img_name}}}
\\caption{{{caption}}}
\\label{{fig:{img_name.split('.')[0]}}}
\\end{{figure}}
""")
            continue
            
        # Parse headers
        if parsed_line.startswith("## "):
            # Strip Section number prefix like "## **1. Section Title**" -> "\section{Section Title}"
            header_text = parsed_line[3:].strip()
            header_text = re.sub(r'^\\textbf\{\d+\.\s*(.*?)\}', r'\1', header_text)
            header_text = re.sub(r'^\d+\.\s*(.*?)$', r'\1', header_text)
            tex_content.append(f"\n\\section{{{escape_latex(header_text)}}}\n")
            
        elif parsed_line.startswith("### "):
            header_text = parsed_line[4:].strip()
            # Strip formatting
            header_text = re.sub(r'^\\textbf\{(.*?)\}', r'\1', header_text)
            header_text = header_text.rstrip(':')
            tex_content.append(f"\n\\subsection{{{escape_latex(header_text)}}}\n")
            
        elif parsed_line.startswith("#### "):
            # We skip figure headers since they are in figure environment caption
            if "Figura" in parsed_line:
                continue
            header_text = parsed_line[5:].strip()
            header_text = re.sub(r'^\\textbf\{(.*?)\}', r'\1', header_text)
            tex_content.append(f"\n\\subsubsection{{{escape_latex(header_text)}}}\n")
            
        # Parse list items
        elif is_bullet:
            if not in_itemize:
                tex_content.append("\\begin{itemize}\n")
                in_itemize = True
            item_text = parsed_line[2:].strip()
            tex_content.append(f"  \\item {escape_latex(item_text)}\n")
            
        elif is_numbered:
            if not in_enumerate:
                tex_content.append("\\begin{enumerate}\n")
                in_enumerate = True
            # Extract item text after "1. "
            item_text = re.sub(r'^\d+\.\s*', '', parsed_line).strip()
            tex_content.append(f"  \\item {escape_latex(item_text)}\n")
            
        # Parse tables
        elif is_table_row:
            # Check if divider row
            if '---' in line_stripped:
                continue
                
            in_table = True
            # Extract cells
            cells = [c.strip() for c in line_stripped.split('|')[1:-1]]
            
            # Escape LaTeX in cells
            escaped_cells = [escape_latex(c) for c in cells]
            
            # Track column count
            table_cols_count = max(table_cols_count, len(escaped_cells))
            table_rows.append(escaped_cells)
            
        # Normal text lines
        else:
            if line_stripped:
                # Check for divider lines
                if line_stripped == "---":
                    tex_content.append("\n\\strut\n")
                else:
                    tex_content.append(escape_latex(parsed_line) + "\n")
            else:
                tex_content.append("\n")
                
    # Close any open list environments at the end of file
    if in_itemize:
        tex_content.append("\\end{itemize}\n")
    if in_enumerate:
        tex_content.append("\\end{enumerate}\n")
        
    # Document footer
    tex_content.append("\n\\end{document}\n")
    
    # Save the LaTeX content
    with open(TEX_PATH, "w", encoding="utf-8") as f:
        f.write("".join(tex_content))
    logger.info(f"Successfully compiled and saved LaTeX report: {TEX_PATH}")

def copy_assets():
    logger.info("Copying image assets to TeX folder...")
    assets = [
        "fig1_frequencies.png",
        "fig2_regional_heatmap.png",
        "fig3_sectoral_matrix.png"
    ]
    for asset in assets:
        src = os.path.join(ASSETS_DIR, asset)
        dst = os.path.join(TEX_DIR, asset)
        if os.path.exists(src):
            shutil.copy(src, dst)
            logger.info(f"Copied asset: {asset}")
        else:
            logger.warning(f"Asset not found: {src}")

def main():
    parse_md_to_tex()
    copy_assets()
    logger.info("LaTeX compiler run complete!")

if __name__ == "__main__":
    main()
