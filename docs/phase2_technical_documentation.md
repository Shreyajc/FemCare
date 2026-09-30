# Phase 2 technical documentation — Part K

This file is the editable contents list for the technical submission. Paths are relative to the repository root. The original data has 17,976 cycle records. The final cleaned fused CSV has 17,976 rows and 56 columns.

| Required item | Uploaded file or folder | What it provides |
| --- | --- | --- |
| 1. Source code | `app.py`, `analytics/`, `utils/`, `scripts/`, `embeddings/`, `rag/` | Application, API collection, fusion, cleaning, analysis, and assistant code. |
| 2. Original dataset | `data/menstrual_dataset.csv` | Original cycle records used before API enrichment. |
| 3. API-collected datasets | `data/api_fusion/static/census_state.csv`, `data/api_fusion/static/cdc_places_state.csv`, `data/api_fusion/dynamic/open_meteo_row_level.csv`, `data/api_fusion/dynamic/us_state_capital_coordinates.csv` | Collected Census and CDC state context, weather by cycle date, and representative state capital coordinates. |
| 4. Final fused CSV | `data/api_fusion/final/femcare_final_fused_dataset.csv`, `data/api_fusion/final/femcare_final_cleaned.csv` | Fusion output and final cleaned analysis/RAG input. |
| 5. EDA script and outputs | `scripts/eda_final_dataset.py`, `data/api_fusion/eda/` | Reproducible summaries, correlations, and figures. |
| 6. LLM/RAG implementation | `embeddings/build_phase2_knowledge_base.py`, `rag/phase2_retriever.py`, `rag/llm.py`, `vectorstore/phase2_original_index/index.joblib`, `vectorstore/phase2_fused_index/index.joblib` | Builds and uses comparable TF-IDF indexes; Llama receives retrieved context. |
| 7. Screenshots | `screenshots/` | Earlier app screenshots are present. New Phase 2 screenshots requested below are still needed. |
| 8. README | `README.md`, this file | Setup, reproduction steps, and submission map. |
| 9. API references | Links below and collection scripts in `scripts/` | API sources and exact endpoints/fields used. |
| 10. Results and observations | `report/phase2/FemCare_Phase_2_Report.docx`, `report/phase2/assets/phase2_rag_summary.csv`, `report/phase2/assets/phase2_rag_evaluation.csv`, `report/phase2/assets/knowledge_base_manifest.json`, `data/api_fusion/eda/` | Report, per-question evidence, aggregate measures, knowledge-base counts, and EDA outputs. |

## Files involved in creating the fused CSV

| Stage | Code | Output or role |
| --- | --- | --- |
| Census API | `scripts/api_census.py` | Reads 2024 ACS 5-year state values into `data/api_fusion/static/census_state.csv`. The key comes from `CENSUS_API_KEY`. |
| CDC PLACES API | `scripts/api_cdc_places.py` | Collects county data and computes population-weighted state indicators in `data/api_fusion/static/cdc_places_state.csv`. |
| Open-Meteo API | `scripts/api_open_meteo.py` | Uses state capitals and cycle dates to produce `data/api_fusion/dynamic/open_meteo_row_level.csv`. `scripts/retry_indiana_weather.py` records a weather collection retry. |
| Fusion | `scripts/final_fusion.py` | Joins the original data to Census and CDC by state and weather by cycle-level keys, producing `femcare_final_fused_dataset.csv`. |
| Cleaning | `scripts/clean_final_dataset.py` | Validates and produces `femcare_final_cleaned.csv`, including cleaning flags. |
| EDA | `scripts/eda_final_dataset.py` | Produces the summaries and charts in `data/api_fusion/eda/`. |
| RAG preparation | `embeddings/build_phase2_knowledge_base.py` | Turns selected fields into text documents and creates the baseline and enhanced TF-IDF indexes. |
| Retrieval and LLM | `rag/phase2_retriever.py`, `rag/llm.py`, `app.py` | Retrieves relevant text, passes it to Llama, and displays the answer. |
| Comparison | `scripts/evaluate_phase2_rag.py` | Runs the fixed before/after question set and saves the results. |

The baseline and enhanced comparisons use the same TF-IDF retrieval method and Llama model. The enhanced index adds 17,976 cycle documents, 50 state summaries, and 3 fusion analysis summaries. The baseline contains 31 medical knowledge sections and 1 original-data summary. The searchable text excludes `user_id`, latitude, and longitude. The CSV itself retains its original fields for reproducibility.

## API documentation

| Source | Documentation | Endpoint used in code |
| --- | --- | --- |
| U.S. Census 2024 ACS 5-year | [ACS dataset documentation](https://api.census.gov/data/2024/acs/acs5.html) | `https://api.census.gov/data/2024/acs/acs5` |
| CDC PLACES county data | [Dataset API reference](https://dev.socrata.com/foundry/data.cdc.gov/i46a-9kgh) | `https://data.cdc.gov/resource/i46a-9kgh.json` |
| Open-Meteo historical weather | [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) | `https://archive-api.open-meteo.com/v1/archive` |
| Open-Meteo location search | [Geocoding API](https://open-meteo.com/en/docs/geocoding-api) | `https://geocoding-api.open-meteo.com/v1/search` |

## Results and interpretation

The stored ten-question run reports 5/10 correct answers before fusion and 10/10 after fusion. The average local response times were 24.8 and 35.8 seconds, respectively. These are results for a small, hand-designed test set and one local run; they do not establish general accuracy or medical safety. State-level health values are context about a population and should not be interpreted as patient-level measurements. Weather represents a state capital, not each user's exact location.

## Screenshots still needed for the Phase 2 demonstration

Save new captures in `screenshots/phase2/` and update this checklist and the report as needed. Hide API keys, personal chat history, account details, and any private identifiers before capturing.

1. `phase2_home.png` — current FemCare home/chat screen showing that the app opens.
2. `phase2_general_answer.png` — a general menstrual-health question with its answer and source, such as “What is PCOS?”
3. `phase2_state_answer.png` — a fused-data question, such as “What is the median household income in California?”, with the answer and source visible.
4. `phase2_comparison_answer.png` — a comparison question, such as “Compare average menstrual pain in California and Texas,” with both values visible.
5. `phase2_limitations_answer.png` — a question such as “Does living in California cause higher period pain?” showing an appropriate caution about causation.
6. `phase2_analytics.png` — the current app's analytics view using the fused data, if that view is part of the demonstration.

The figures in `data/api_fusion/eda/figures/` and `report/phase2/assets/` are generated charts, not screenshots of the running application.
