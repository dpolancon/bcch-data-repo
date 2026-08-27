# Audit & Handoff 04: Tri-Repository Architecture, Deployment Pipeline & Live Status

**Fecha de Verificación:** 2026-08-27  
**Estado General:** 100% Sincronizado, Auditado y en Vivo (HTTP 200 OK)

---

## 1. Arquitectura de los Tres Repositorios

El desarrollo y publicación del sitio web se articula en una estructura tri-repositorio altamente aislada y reproducible:

```
c:\ReposGitHub\
├── bcch-data-repo/          [main]  Pipelines Python, scripts de descarga/panelización, bóveda.
├── bcch-site/               [site]  Worktree aislado con la fuente Quarto (.qmd), assets y JS.
└── dpolancon.github.io/     [master] Servidor de producción en GitHub Pages (/bcch/).
```

### Detalle de Repositorios y Ramas:
1. **`bcch-data-repo` (Rama `main`):**
   - Aloja el motor analítico (`scripts/`), las pruebas automatizadas (`tests/`), las definiciones de familias (`scripts/lib/families.py`), los paneles CSV (`data/`) y las notas técnicas (`bcch-data-repo-vault/`).
2. **`bcch-site` (Rama `site`):**
   - Git worktree huérfano en `C:\ReposGitHub\bcch-site` configurado como destino de la generación Quarto (`scripts/10_generate_site.py`). Contiene las librerías vendoreadas `d3.min.js` y `plot.umd.min.js`.
3. **`dpolancon.github.io` (Rama `master`):**
   - Repositorio del sitio web personal de GitHub Pages. El sitio se despliega en el subdirectorio `bcch/`, compilado a HTML estático en `docs/`.

---

## 2. Secuencia Completa del Pipeline de Publicación

Para realizar cualquier modificación y publicarla en vivo, la sesión debe ejecutar la siguiente cadena estandarizada:

```bash
# 1. Regenerar los paneles temáticos si hay cambios en los datos crudos:
python scripts/09_build_theme_panels.py --family <familia>

# 2. Generar la estructura de páginas Quarto (.qmd) y assets en el worktree:
python scripts/10_generate_site.py

# 3. Renderizar el sitio HTML estático con Quarto:
& "C:\Program Files\Quarto\bin\quarto.exe" render C:\ReposGitHub\bcch-site

# 4. Ejecutar la auditoría forense de datos e invariancia:
python scripts/11_audit_site.py

# 5. Sincronizar el directorio compilado con el repositorio de producción:
python scripts/12_deploy_site.py

# 6. Commitear y pushear los tres repositorios:
git -C "C:\ReposGitHub\bcch-data-repo" add .
git -C "C:\ReposGitHub\bcch-data-repo" commit -m "..."
git -C "C:\ReposGitHub\bcch-data-repo" push origin main

git -C "C:\ReposGitHub\bcch-site" add .
git -C "C:\ReposGitHub\bcch-site" commit -m "..."
git -C "C:\ReposGitHub\bcch-site" push origin site

git -C "C:\ReposGitHub\dpolancon.github.io" add bcch
git -C "C:\ReposGitHub\dpolancon.github.io" commit -m "..."
git -C "C:\ReposGitHub\dpolancon.github.io" push origin master
```

---

## 3. Estado de Sincronización y Commits Recientes

Al cierre de la sesión actual, la auditoría de control de versiones confirma:

- **`bcch-data-repo` (`main`):** `Commit e63b450` — *Actualización de scripts y briefings con nuevo orden secuencial de reportes y prosa narrativa implícita*. (Rama limpia y al día con `origin/main`).
- **`bcch-site` (`site`):** `Commit 9331382` — *Reordenamiento de reportes y purga de códigos explícitos de hipótesis*. (Rama limpia y al día con `origin/site`).
- **`dpolancon.github.io` (`master`):** `Commit 50118bf` — *Reordenamiento de reportes (1. Cobertura de datos) y conversión de hipótesis a prosa implícita*. (Subdirectorio `bcch/` limpio y al día con `origin/master`).

---

## 4. Verificación de Estatus HTTP 200 OK en Vivo

Se ejecutó la verificación de peticiones HTTP en tiempo real contra los endpoints públicos del servidor de GitHub Pages, confirmando la disponibilidad inmediata de las páginas y recursos:

| Endpoint en Vivo | Estatus HTTP | Tamaño de Respuesta |
|:---|:---:|:---:|
| `https://dpolancon.github.io/bcch/reportes/report1-cobertura.html` | **200 OK** | 61,1 KB |
| `https://dpolancon.github.io/bcch/reportes/report2-disparidades.html` | **200 OK** | 77,0 KB |
| `https://dpolancon.github.io/bcch/reportes/report3-dos-ejes.html` | **200 OK** | 39,3 KB |
| `https://dpolancon.github.io/bcch/assets/fig3_1_dos_ejes.png` | **200 OK** | 311,1 KB |
| `https://dpolancon.github.io/bcch/reportes/report4-construccion.html` | **200 OK** | 54,4 KB |
| `https://dpolancon.github.io/bcch/reportes/report8-tasas.html` | **200 OK** | 42,9 KB |

---

## 5. Instrucciones para Siguientes Sesiones

1. **No alterar los scripts de generación manual:** Toda modificación a la prosa de los reportes debe realizarse en `scripts/10_generate_site.py` o en las plantillas de `bcch-data-repo-vault/`.
2. **Correr siempre `11_audit_site.py` antes de desplegar:** Si la auditoría falla, la página web no debe desplegarse hasta corregir la discrepancia cuantitativa.
3. **Preservar la regla de tipos CSV:** Al manipular dataframes en nuevos scripts, incluir explícitamente `dtype={"region_id": str, "sector_id": str}`.
