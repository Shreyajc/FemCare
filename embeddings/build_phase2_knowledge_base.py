from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_DATASET = ROOT / "data" / "menstrual_dataset.csv"
FUSED_DATASET = ROOT / "data" / "api_fusion" / "final" / "femcare_final_cleaned.csv"
KNOWLEDGE_DIR = ROOT / "knowledge"
ORIGINAL_INDEX = ROOT / "vectorstore" / "phase2_original_index" / "index.joblib"
FUSED_INDEX = ROOT / "vectorstore" / "phase2_fused_index" / "index.joblib"
MANIFEST = ROOT / "report" / "phase2" / "assets" / "knowledge_base_manifest.json"


def split_markdown_sections(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    sections: list[dict] = []
    current_title = path.stem.replace("_", " ").title()
    current_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(
                {
                    "text": f"{current_title}\n{body}",
                    "source": path.name,
                    "record_type": "medical_knowledge",
                }
            )

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            current_title = line[3:].strip()
            current_lines = []
        elif not line.startswith("# "):
            current_lines.append(line)
    flush()
    return sections


def medical_documents() -> list[dict]:
    documents: list[dict] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.txt")):
        documents.extend(split_markdown_sections(path))
    return documents


def original_summary_document(df: pd.DataFrame) -> dict:
    return {
        "text": (
            "Original FemCare dataset summary. "
            f"The dataset contains {len(df):,} menstrual-cycle records for "
            f"{df['user_id'].nunique():,} users across {df['state'].nunique()} US states. "
            f"Average cycle length is {df['cycle_length_days'].mean():.3f} days, "
            f"average pain is {df['pain_level'].mean():.3f} out of 10, and "
            f"average cycle stress is {df['stress_score_cycle'].mean():.3f} out of 10. "
            "The original dataset contains cycle, symptom, hormone, wellness and lifestyle fields, "
            "but it does not contain Census, CDC PLACES or weather attributes."
        ),
        "source": "data/menstrual_dataset.csv",
        "record_type": "original_dataset_summary",
    }


def cycle_documents(df: pd.DataFrame) -> list[dict]:
    documents: list[dict] = []
    for row in df.itertuples(index=False):
        text = (
            f"Fused menstrual cycle record. State: {row.state}. Date: {row.start_date}. "
            f"Cycle number: {row.cycle_number}. Cycle length: {row.cycle_length_days} days. "
            f"Pain: {row.pain_level}/10. Cycle stress: {row.stress_score_cycle}/10. "
            f"Cycle sleep: {row.sleep_hours_cycle} hours. Mood: {row.mood_score}. "
            f"Flow: {row.flow_level}. PCOS diagnosed: {row.pcos_diagnosed}. "
            f"Temperature: {row.temperature_mean} C. Humidity: {row.humidity_mean} percent. "
            f"Precipitation: {row.precipitation}. Wind speed: {row.wind_speed_mean}. "
            f"State population: {row.census_total_population}. "
            f"Median household income: {row.census_median_household_income} dollars. "
            f"CDC obesity prevalence: {row.cdc_obesity_prevalence} percent. "
            f"CDC physical inactivity prevalence: {row.cdc_physical_inactivity_prevalence} percent. "
            f"CDC smoking prevalence: {row.cdc_smoking_prevalence} percent. "
            f"CDC depression prevalence: {row.cdc_depression_prevalence} percent."
        )
        documents.append(
            {
                "text": text,
                "source": "data/api_fusion/final/femcare_final_cleaned.csv",
                "record_type": "fused_cycle_record",
                "record_key": f"{row.state}|{row.start_date}|cycle-{row.cycle_number}",
            }
        )
    return documents


def state_summary_documents(df: pd.DataFrame) -> list[dict]:
    api_first = [
        "census_total_population",
        "census_female_population",
        "census_female_20_24",
        "census_female_25_29",
        "census_female_30_34",
        "census_median_household_income",
        "cdc_obesity_prevalence",
        "cdc_physical_inactivity_prevalence",
        "cdc_smoking_prevalence",
        "cdc_depression_prevalence",
    ]
    records: list[dict] = []
    for state, group in df.groupby("state", sort=True):
        first = group.iloc[0]
        text = (
            f"Fused state summary for {state}. Cycle records: {len(group)}. "
            f"Census total population: {int(first['census_total_population']):,}. "
            f"Census female population: {int(first['census_female_population']):,}. "
            f"Census female population age 20 to 24: {int(first['census_female_20_24']):,}. "
            f"Age 25 to 29: {int(first['census_female_25_29']):,}. "
            f"Age 30 to 34: {int(first['census_female_30_34']):,}. "
            f"Median household income: ${int(first['census_median_household_income']):,}. "
            f"CDC obesity prevalence: {first['cdc_obesity_prevalence']:.3f} percent. "
            f"CDC physical inactivity prevalence: {first['cdc_physical_inactivity_prevalence']:.3f} percent. "
            f"CDC smoking prevalence: {first['cdc_smoking_prevalence']:.3f} percent. "
            f"CDC depression prevalence: {first['cdc_depression_prevalence']:.3f} percent. "
            f"Average menstrual pain: {group['pain_level'].mean():.3f}. "
            f"Average cycle stress: {group['stress_score_cycle'].mean():.3f}. "
            f"Average temperature: {group['temperature_mean'].mean():.3f} C. "
            f"Average humidity: {group['humidity_mean'].mean():.3f} percent."
        )
        assert all(pd.notna(first[column]) for column in api_first)
        records.append(
            {
                "text": text,
                "source": "state summary derived from femcare_final_cleaned.csv",
                "record_type": "fused_state_summary",
                "record_key": state,
            }
        )
    return records


def fusion_summary_documents(df: pd.DataFrame) -> list[dict]:
    weather_corr = df[
        ["temperature_mean", "humidity_mean", "precipitation", "wind_speed_mean", "pain_level"]
    ].corr()["pain_level"]
    state = df.groupby("state", as_index=False).agg(
        average_pain=("pain_level", "mean"),
        average_stress=("stress_score_cycle", "mean"),
        depression=("cdc_depression_prevalence", "first"),
        inactivity=("cdc_physical_inactivity_prevalence", "first"),
        obesity=("cdc_obesity_prevalence", "first"),
        income=("census_median_household_income", "first"),
    )
    return [
        {
            "text": (
                "Phase 2 fused dataset overview. The final cleaned fused dataset contains "
                f"{len(df):,} rows, {len(df.columns)} columns, {df['user_id'].nunique():,} users "
                f"and {df['state'].nunique()} states. It retains 34 original menstrual attributes, "
                "adds 7 Census attributes, 7 CDC PLACES attributes, 6 Open-Meteo attributes, "
                "and 2 cleaning flags. Fusion added state population, reproductive-age female "
                "population, median household income, obesity, physical inactivity, smoking, "
                "depression, temperature, humidity, precipitation and wind information."
            ),
            "source": "Phase 2 dataset profile",
            "record_type": "fusion_dataset_summary",
        },
        {
            "text": (
                "Phase 2 weather and pain findings. Pearson correlations with menstrual pain are "
                f"temperature {weather_corr['temperature_mean']:.4f}, "
                f"humidity {weather_corr['humidity_mean']:.4f}, "
                f"precipitation {weather_corr['precipitation']:.4f}, and "
                f"wind speed {weather_corr['wind_speed_mean']:.4f}. "
                "All four relationships are negligible in this dataset and do not support a causal claim."
            ),
            "source": "Phase 2 fused EDA",
            "record_type": "fusion_analysis_summary",
        },
        {
            "text": (
                "Phase 2 state-level findings. CDC depression prevalence versus average cycle stress "
                f"has Pearson correlation {state['depression'].corr(state['average_stress']):.4f}. "
                "CDC physical inactivity versus average menstrual pain has Pearson correlation "
                f"{state['inactivity'].corr(state['average_pain']):.4f}. "
                "CDC obesity and Census median household income have Pearson correlation "
                f"{state['obesity'].corr(state['income']):.4f}. These are ecological state-level "
                "relationships and are not individual clinical effects."
            ),
            "source": "Phase 2 fused EDA",
            "record_type": "fusion_analysis_summary",
        },
    ]


def build_index(documents: list[dict], output_path: Path) -> dict:
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        max_features=60000,
        sublinear_tf=True,
        norm="l2",
    )
    matrix = vectorizer.fit_transform(document["text"] for document in documents)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "vectorizer": vectorizer,
            "matrix": matrix,
            "documents": documents,
            "format": "FemCare Phase 2 TF-IDF vector knowledge base",
        },
        output_path,
        compress=3,
    )
    return {
        "path": str(output_path.relative_to(ROOT)),
        "documents": len(documents),
        "features": int(matrix.shape[1]),
        "non_zero_values": int(matrix.nnz),
    }


def main() -> None:
    original = pd.read_csv(ORIGINAL_DATASET)
    fused = pd.read_csv(FUSED_DATASET)

    shared = medical_documents()
    original_documents = shared + [original_summary_document(original)]
    fused_documents = (
        shared
        + [original_summary_document(original)]
        + fusion_summary_documents(fused)
        + state_summary_documents(fused)
        + cycle_documents(fused)
    )

    manifest = {
        "original_index": build_index(original_documents, ORIGINAL_INDEX),
        "fused_index": build_index(fused_documents, FUSED_INDEX),
        "document_counts": {
            "medical_knowledge": len(shared),
            "original_dataset_summary": 1,
            "fusion_analysis_summaries": 3,
            "state_summaries": fused["state"].nunique(),
            "fused_cycle_records": len(fused),
        },
        "excluded_from_text": [
            "user_id",
            "latitude",
            "longitude",
        ],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
