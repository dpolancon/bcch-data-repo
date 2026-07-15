
---

# **Report: Regional Economic Disparities in Chile - A Descriptive Analysis (2000-2025)**

## **Report Structure**

### **1. Introduction**
- Brief motivation on Chile's regional development challenges
- Data source: BCCh Regional GDP (chained volume, reference 2018)
- Scope: 16 regions, annual and quarterly frequency

---

### **2. Section 1: Regional Economic Size and Growth Dynamics**

**Table 1: Summary Statistics of Regional Economic Output (2000-2025)**

| Region        | Mean GDP (Billion CLP) | Share of National GDP (%) | Avg. Annual Growth Rate | Output Volatility (Std. Dev.) |
| ------------- | ---------------------- | ------------------------- | ----------------------- | ----------------------------- |
| Metropolitana | [value]                | [~40-45%]                 | [value]                 | [value]                       |
| Antofagasta   | [value]                | [~10-12%]                 | [value]                 | [high - mining volatility]    |
| Biobío        | [value]                | [~8-10%]                  | [value]                 | [value]                       |
| ...           | ...                    | ...                       | ...                     | ...                           |
| Aysén         | [value]                | [<1%]                     | [value]                 | [value]                       |

**Corresponding Figures:**

**Figure 1.1: Regional GDP Distribution - The Santiago Dominance**
- **Type:** Horizontal bar chart (log scale optional)
- **X-axis:** Mean GDP (Billion CLP, 2018 prices)
- **Y-axis:** 16 regions (sorted descending)
- **Visual cue:** Color-code RM in red, mining regions (Antofagasta, Atacama) in orange, others in blue
- **Purpose:** Immediately shows the extreme concentration in RM

**Figure 1.2: Growth vs. Size - Convergence Patterns**
- **Type:** Scatter plot
- **X-axis:** Initial GDP level (2000)
- **Y-axis:** Average annual growth rate (2000-2025)
- **Bubble size:** Share of national GDP
- **Trend line:** Include negative slope if convergence exists
- **Annotations:** Label outliers (e.g., high-growth mining regions)
- **Purpose:** Tests for β-convergence visually (do poorer regions grow faster?)

---

### **3. Section 2: Regional Economic Specialization**

**Table 2: Location Quotients (LQ) by Region and Sector**

| Region | Mining | Manufacturing | Construction | Commerce | Services | Agriculture |
|--------|--------|---------------|--------------|----------|----------|-------------|
| **Antofagasta** | [>3.0] | [0.3] | [0.8] | [0.7] | [0.6] | [0.1] |
| **Metropolitana** | [0.1] | [1.1] | [1.2] | [1.3] | [1.4] | [0.2] |
| **Biobío** | [0.2] | [1.5] | [1.0] | [0.9] | [0.8] | [0.6] |
| **Los Lagos** | [0.1] | [0.8] | [0.9] | [0.9] | [0.8] | [1.8] |
| **Araucanía** | [0.1] | [0.6] | [0.8] | [0.8] | [0.7] | [2.0] |
| ... | ... | ... | ... | ... | ... | ... |

*Note: LQ > 1 indicates regional specialization (sector share higher than national average)*

**Corresponding Figures:**

**Figure 2.1: Specialization Heatmap**
- **Type:** Heatmap (color gradient)
- **X-axis:** Economic sectors (Mining, Manufacturing, Construction, Commerce, Services, Agriculture)
- **Y-axis:** 16 regions (grouped geographically: North, Center, South)
- **Color scale:** Blue (LQ < 1, under-specialized) to Red (LQ > 1, highly specialized)
- **Purpose:** Instantly reveals regional economic identities (mining north, services center, agriculture south)

**Figure 2.2: Regional Specialization Radar Charts**
- **Type:** Multi-panel radar charts (small multiples)
- **Select 4 representative regions:**
  1. **Antofagasta** (mining enclave)
  2. **Metropolitana** (services hub)
  3. **Biobío** (industrial/manufacturing)
  4. **Araucanía/Los Lagos** (agriculture/agro-industry)
- **Axes:** 6 sectors normalized to national average (=1)
- **Purpose:** Shows the "economic DNA" of each region type

---

### **4. Section 3: Evolution of Spatial Inequality**

**Table 3: Spatial Inequality Indices Over Time**

| Year | Gini Coefficient | Theil Index | HHI (Output Concentration) |
|------|------------------|-------------|----------------------------|
| 2000 | [value] | [value] | [value] |
| 2005 | [value] | [value] | [value] |
| 2010 | [value] | [value] | [value] |
| 2015 | [value] | [value] | [value] |
| 2020 | [value] | [value] | [value] |
| 2025 | [value] | [value] | [value] |

*Note: Higher values = greater spatial inequality/concentration*

**Corresponding Figures:**

**Figure 3.1: Spatial Inequality Trends (2000-2025)**
- **Type:** Multi-line chart with dual axes
- **X-axis:** Years (2000-2025)
- **Left Y-axis:** Gini Coefficient (0-1 scale)
- **Right Y-axis:** Theil Index and HHI
- **Lines:** 
  - Gini (solid, bold)
  - Theil (dashed)
  - HHI (dotted)
- **Annotations:** Mark key events (2009 crisis, 2010 earthquake, 2020 pandemic)
- **Purpose:** Shows whether regional inequality is increasing, decreasing, or stable

**Figure 3.2: Regional GDP Share Evolution - Stacked Area**
- **Type:** 100% stacked area chart
- **X-axis:** Years (2000-2025)
- **Y-axis:** Cumulative % of national GDP (0-100%)
- **Areas:** Each region as a colored band
- **Highlight:** RM as the bottom layer (showing if its dominance is growing or shrinking)
- **Purpose:** Visualizes the changing composition of Chile's economic geography

---

### **5. Conclusions & Policy Implications**
- Summary of key findings from the three tables/figures
- Discussion of persistent spatial concentration
- Implications for regional development policy
- Next steps: Adding sectorial data and labor market indicators

---

## **Technical Notes for Implementation**

**Data Requirements from BCCh API:**
1. **For Table 1:** Total regional GDP (annual) - codes like `F035.PIB.FLU.R.CLP.2018.Z.Z.Z.[REGION].0.A`
2. **For Table 2:** Sectorial GDP by region - codes like `F035.PIB.FLU.R.CLP.2018.[SECTOR].Z.Z.[REGION].0.A`
3. **For Table 3:** Same as Table 1 (calculate indices from the panel)

**Key Formulas:**
- **Location Quotient:** LQ = (Regional Sector GDP / Regional Total GDP) ÷ (National Sector GDP / National Total GDP)
- **Gini Coefficient:** Standard inequality formula applied to regional GDP per capita or total GDP
- **Theil Index:** T = Σ(yᵢ/ȳ) × ln(yᵢ/ȳ) where y is regional GDP
- **HHI:** Σ(sᵢ)² where s is region i's share of national GDP

