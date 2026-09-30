# FemCare AI

FemCare is a Streamlit menstrual health prototype with a local Llama 3.2 assistant. Phase 1 joined cycle records with Census, CDC PLACES, and Open-Meteo data. Phase 2 made selected fused data searchable and compared answers before and after enrichment.

**Start here:** [Phase 2 technical documentation](docs/phase2_technical_documentation.md) contains an editable Part K contents table, the data flow, API references, results, and the screenshot checklist. The [Phase 2 report](report/phase2/FemCare_Phase_2_Report.docx) contains the written analysis.

## Run the Phase 2 assistant

From the repository root, install `requirements.txt`, start Ollama with `llama3.2:3b`, and run:

```powershell
streamlit run app.py
```

The application uses the Phase 2 TF-IDF index at `vectorstore/phase2_fused_index/index.joblib`. Rebuild both Phase 2 indexes after changing the data or knowledge files:

```powershell
python embeddings/build_phase2_knowledge_base.py
```

The older MiniLM/FAISS implementation remains in `embeddings/create_vector_db.py` and `rag/retriever.py` for historical context. The current app imports `rag/phase2_retriever.py`.

## Reproduce the submitted work

The collected API CSV files are included, so the collection calls are optional. To collect Census data again, set `CENSUS_API_KEY` in the environment. Never commit the key.

```powershell
python scripts/api_census.py
python scripts/api_cdc_places.py
python scripts/api_open_meteo.py
python scripts/final_fusion.py
python scripts/clean_final_dataset.py
python scripts/eda_final_dataset.py
python embeddings/build_phase2_knowledge_base.py
python scripts/evaluate_phase2_rag.py
```

The evaluation requires Ollama and `llama3.2:3b`. Results can vary with model execution and machine speed. The submitted ten-question comparison is evidence for this test set only; it is not clinical validation. The assistant provides educational information and cannot replace professional medical care.
