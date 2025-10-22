<p align="center">
  <b>🌍 Language / Langue:</b><br>
  <a href="./05_README_Francais.md">🇫🇷 Français</a> |
  <a href="./05_README_English.md">🇬🇧 English</a>
</p>

---

# 🧩 Bio-Data-Workflow-Automation  
_A complete and scalable pipeline for enriching and classifying a Bio product catalogue._

---

## **1. Context and Results**

### **1.1 Context**
This project was developed during my internship at **GOOD**, a digital services agency supporting manufacturers and distributors in the **organic (Bio)** sector.  
I worked on the **BioAnalytics** database, which consolidates in-store sales data collected from a panel of partner retailers and serves as the foundation for the market analyses provided to clients.

### **1.2 Importance and Challenges**
The BioAnalytics database is a key tool for **business intelligence**, but its quality must be continuously monitored.  
The main challenges identified:

- **Classification errors** that can distort analytical results;  
- **Manual data entry**, which is slow and repetitive;  
- The need for **frequent updates**;  
- **Multiple heterogeneous sources** (stores, catalogues, websites), making consolidation complex.  

👉 Hence the creation of an automated pipeline to make these processes faster and more reliable.

### **1.3 Results and Added Value**
The pipeline automates **normalization**, **completion**, and **classification** of BioAnalytics products, significantly improving both speed and reliability.

- **Increased efficiency:** daily tasks are reduced to **30–60 minutes**, thanks to modular scripts that can easily be reused across projects.  
- **Fewer human errors:** the algorithm identifies inconsistencies in existing data and allows adjustment of the balance between accuracy and completion rate.  
- **Improved data quality:** standardized formats, regular updates, and **control KPIs** ensure coherence and reliability of the database.

---

## **2. Project Structure**

```text
├── src/
│   ├── main.py                     # Main pipeline script
│   ├── ml_qualification.py         # Machine Learning models for classification
│   ├── extract_contenu.py          # Extraction of product packaging/weight
│   ├── api_openfoodfacts.py        # Completion via OpenFoodFacts API
│   ├── google_api_search.py        # Completion via Google API
│
├── data/
│   ├── Dataset_filtre_pour_entrainement_ML.xlsx  # Training dataset
│   └── Demo_brut_V2.xlsx                          # Example input file
│
├── models/
│   ├── classification_models.pkl
│   └── label_encoders.pkl
│
├── outputs/
│   ├── Demo_classifié_final.xlsx
│   └── Statistiques_Remplissage.xlsx
│
├── README_Francais.md              # French version of the README
├── README_English.md               # English version of the README
│
├── requirements.txt
└── .gitignore
```
---

## **3. Components and Workflow**

The **main.py** script orchestrates all pipeline stages, from data cleaning to report generation.

- **Step 0 – Model Training (optional)**  
  Trains a classification model using an existing dataset, then saves the models (.pkl) for later reuse.

- **Step 1 – Completion via OpenFoodFacts**  
  Retrieves missing information from the OpenFoodFacts public database to fill *Designation* and *Brand* columns.

- **Step 2 – Packaging Extraction (Regex)**  
  Detects product formats (e.g., “6x250 g”, “500 ml”) and computes a standardized *Packaging* value.

- **Step 3 – Automatic Classification (ML)**  
  Predicts *Family*, *Sub-family*, and *Segment* categories based on the product designation, ensuring hierarchical consistency.

- **Step 4 – Search via Google API**  
  Completes missing *Brand* or *Designation* values by analyzing the top web results.

- **Step 5 – Export and Reporting**  
  Produces an enriched Excel file and a summary report showing completion rates before and after processing.

---

## **4. Input and Output**

- **Input:** raw Excel file (e.g., `data/Demo_brut_V2.xlsx`)  
- **Output:** enriched Excel file (e.g., `outputs/Demo_classifié_final.xlsx`)  

### **Example of Data Enrichment**

#### Before Processing
| EAN           | Designation              | Brand    | Family | Sub-family | Segment | Packaging |
|---------------|--------------------------|----------|---------|-------------|----------|-----------|
| 8721082004091 | POP CORN CARAMEL BIO 75G | NON CREE | 9999    | (empty)     | (empty)  | (empty)   |

#### After Processing
| EAN           | Designation (after)       | Brand (after)                        | Family (predicted) | Sub-family (predicted) | Segment (predicted) | Packaging (calculated) |
|---------------|---------------------------|--------------------------------------|--------------------|------------------------|---------------------|------------------------|
| 8721082004091 | Pop Corn Caramel Bio 75 g | Automatically filled (API OpenFoodFacts / Google) | Savory groceries | Baking aids | Bakery | 0.075 kg |

> **Notes:**  
> - *Designation* is standardized automatically.  
> - *Brand* is completed via OpenFoodFacts or Google API.  
> - *Family / Sub-family / Segment* are predicted by the hierarchical ML model.  
> - *Packaging* is extracted from the product format (e.g., “75G”).

---

## **5. Limitations and Improvements**

### **Current Limitations**

Three main factors still limit the pipeline’s performance:

- **Dependence on external sources:** the quality and coverage of public APIs vary by product category. Free usage limits (e.g., Google API quotas) slow down large-scale processing.  
- **Quality of training data:** the ML models often outperform the original classifications but remain constrained by the quality of initial data. As long as reference data include errors or missing values, performance will plateau.  
- **Use of Language Models (LLMs):** although not directly integrated into the pipeline, tools such as *ChatGPT* played a key role in daily work, helping with analysis, verification, and partial automation. Their potential is high, but full integration remains limited by current structural challenges in the AI industry — high computation costs, energy consumption, and limited infrastructure capacity.

### **Improvement Opportunities**

Several enhancements are possible in the short term with moderate investment:

- **Improve data access:** rely on more reliable sources or paid APIs to ensure broader coverage and faster processing.  
- **Strengthen machine learning:** enrich the dataset with more diverse examples and refine automatic verification logic to improve classification accuracy.  
- **Better leverage LLMs:** adopt professional accounts or API-based access to integrate these tools more seamlessly into the pipeline, boosting automation and productivity.

---

📘 *Last updated: October 2025*  
Author: **Yuchen LU**
