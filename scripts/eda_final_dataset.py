import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# FEMCARE - EXPLORATORY DATA ANALYSIS
# ============================================================

INPUT_FILE = (
    "data/api_fusion/final/"
    "femcare_final_cleaned.csv"
)

EDA_DIR = "data/api_fusion/eda"
FIGURE_DIR = os.path.join(EDA_DIR, "figures")

os.makedirs(EDA_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("FEMCARE - EXPLORATORY DATA ANALYSIS")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print("\nDataset loaded:")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# BASIC DATASET INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("1. DATASET OVERVIEW")
print("=" * 70)

overview = pd.DataFrame({
    "Metric": [
        "Rows",
        "Columns",
        "Unique Users",
        "Unique States",
        "Duplicate User-Cycle Records",
        "Total Missing Cells"
    ],
    "Value": [
        len(df),
        len(df.columns),
        df["user_id"].nunique(),
        df["state"].nunique(),
        df.duplicated(
            subset=["user_id", "cycle_number"]
        ).sum(),
        df.isna().sum().sum()
    ]
})

print(overview.to_string(index=False))

overview.to_csv(
    os.path.join(
        EDA_DIR,
        "dataset_overview.csv"
    ),
    index=False
)


# ============================================================
# DATA TYPES
# ============================================================

dtype_info = pd.DataFrame({
    "column": df.columns,
    "data_type": df.dtypes.astype(str).values,
    "missing_values": df.isna().sum().values,
    "missing_percentage": (
        df.isna().sum().values
        / len(df)
        * 100
    ).round(2)
})

dtype_info.to_csv(
    os.path.join(
        EDA_DIR,
        "column_information.csv"
    ),
    index=False
)


# ============================================================
# NUMERICAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("2. NUMERICAL SUMMARY")
print("=" * 70)

numeric_df = df.select_dtypes(
    include=np.number
)

numeric_summary = (
    numeric_df
    .describe()
    .T
)

numeric_summary[
    "median"
] = numeric_df.median()

numeric_summary[
    "missing"
] = numeric_df.isna().sum()

numeric_summary.to_csv(
    os.path.join(
        EDA_DIR,
        "numerical_summary.csv"
    )
)

print(
    numeric_summary.to_string()
)


# ============================================================
# CATEGORICAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("3. CATEGORICAL SUMMARY")
print("=" * 70)

categorical_columns = [
    "cycle_phase",
    "flow_level",
    "pms_symptoms",
    "ovulation_result",
    "diet_quality",
    "exercise_frequency",
    "alcohol_consumption",
    "smoking_status",
    "birth_control_use",
    "pcos_diagnosed"
]

categorical_results = []

for column in categorical_columns:

    if column not in df.columns:
        continue

    counts = (
        df[column]
        .value_counts(dropna=False)
    )

    for category, count in counts.items():

        categorical_results.append({
            "feature": column,
            "category": category,
            "count": count,
            "percentage": round(
                count / len(df) * 100,
                2
            )
        })

categorical_summary = pd.DataFrame(
    categorical_results
)

categorical_summary.to_csv(
    os.path.join(
        EDA_DIR,
        "categorical_summary.csv"
    ),
    index=False
)

print(
    categorical_summary.to_string(
        index=False
    )
)


# ============================================================
# HELPER FOR SAVING PLOTS
# ============================================================

def save_plot(filename):

    path = os.path.join(
        FIGURE_DIR,
        filename
    )

    plt.tight_layout()
    plt.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "Saved:",
        path
    )


# ============================================================
# 4. CYCLE LENGTH DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("4. CYCLE LENGTH DISTRIBUTION")
print("=" * 70)

plt.figure()

plt.hist(
    df["cycle_length_days"].dropna(),
    bins=20
)

plt.title(
    "Distribution of Menstrual Cycle Length"
)

plt.xlabel(
    "Cycle Length (days)"
)

plt.ylabel(
    "Number of Records"
)

save_plot(
    "01_cycle_length_distribution.png"
)


# ============================================================
# 5. PAIN LEVEL DISTRIBUTION
# ============================================================

plt.figure()

df["pain_level"].value_counts().sort_index().plot(
    kind="bar"
)

plt.title(
    "Distribution of Pain Levels"
)

plt.xlabel(
    "Pain Level"
)

plt.ylabel(
    "Number of Records"
)

save_plot(
    "02_pain_level_distribution.png"
)


# ============================================================
# 6. FLOW LEVEL DISTRIBUTION
# ============================================================

plt.figure()

df["flow_level"].value_counts().plot(
    kind="bar"
)

plt.title(
    "Distribution of Flow Levels"
)

plt.xlabel(
    "Flow Level"
)

plt.ylabel(
    "Number of Records"
)

save_plot(
    "03_flow_level_distribution.png"
)


# ============================================================
# 7. CYCLE PHASE DISTRIBUTION
# ============================================================

plt.figure()

df["cycle_phase"].value_counts().plot(
    kind="bar"
)

plt.title(
    "Distribution of Cycle Phases"
)

plt.xlabel(
    "Cycle Phase"
)

plt.ylabel(
    "Number of Records"
)

save_plot(
    "04_cycle_phase_distribution.png"
)


# ============================================================
# 8. PAIN VS STRESS
# ============================================================

print("\nCreating pain vs stress analysis...")

pain_stress = (
    df.groupby("pain_level")
    ["stress_score_cycle"]
    .mean()
    .reset_index()
)

pain_stress.to_csv(
    os.path.join(
        EDA_DIR,
        "pain_vs_stress.csv"
    ),
    index=False
)

plt.figure()

plt.plot(
    pain_stress["pain_level"],
    pain_stress["stress_score_cycle"],
    marker="o"
)

plt.title(
    "Average Stress Score by Pain Level"
)

plt.xlabel(
    "Pain Level"
)

plt.ylabel(
    "Average Cycle Stress Score"
)

save_plot(
    "05_pain_vs_stress.png"
)


# ============================================================
# 9. PAIN VS SLEEP
# ============================================================

print("Creating pain vs sleep analysis...")

pain_sleep = (
    df.groupby("pain_level")
    ["sleep_hours_cycle"]
    .mean()
    .reset_index()
)

pain_sleep.to_csv(
    os.path.join(
        EDA_DIR,
        "pain_vs_sleep.csv"
    ),
    index=False
)

plt.figure()

plt.plot(
    pain_sleep["pain_level"],
    pain_sleep["sleep_hours_cycle"],
    marker="o"
)

plt.title(
    "Average Sleep Duration by Pain Level"
)

plt.xlabel(
    "Pain Level"
)

plt.ylabel(
    "Average Sleep Hours"
)

save_plot(
    "06_pain_vs_sleep.png"
)


# ============================================================
# 10. PAIN VS MOOD
# ============================================================

print("Creating pain vs mood analysis...")

pain_mood = (
    df.groupby("pain_level")
    ["mood_score"]
    .mean()
    .reset_index()
)

pain_mood.to_csv(
    os.path.join(
        EDA_DIR,
        "pain_vs_mood.csv"
    ),
    index=False
)

plt.figure()

plt.plot(
    pain_mood["pain_level"],
    pain_mood["mood_score"],
    marker="o"
)

plt.title(
    "Average Mood Score by Pain Level"
)

plt.xlabel(
    "Pain Level"
)

plt.ylabel(
    "Average Mood Score"
)

save_plot(
    "07_pain_vs_mood.png"
)


# ============================================================
# 11. PAIN VS ENERGY
# ============================================================

pain_energy = (
    df.groupby("pain_level")
    ["energy_level"]
    .mean()
    .reset_index()
)

pain_energy.to_csv(
    os.path.join(
        EDA_DIR,
        "pain_vs_energy.csv"
    ),
    index=False
)

plt.figure()

plt.plot(
    pain_energy["pain_level"],
    pain_energy["energy_level"],
    marker="o"
)

plt.title(
    "Average Energy Level by Pain Level"
)

plt.xlabel(
    "Pain Level"
)

plt.ylabel(
    "Average Energy Level"
)

save_plot(
    "08_pain_vs_energy.png"
)


# ============================================================
# 12. LIFESTYLE VS PAIN
# ============================================================

print("Creating lifestyle analysis...")

lifestyle = (
    df.groupby("exercise_frequency")
    .agg(
        average_pain=(
            "pain_level",
            "mean"
        ),
        average_stress=(
            "stress_score_cycle",
            "mean"
        ),
        average_sleep=(
            "sleep_hours_cycle",
            "mean"
        ),
        records=(
            "pain_level",
            "count"
        )
    )
    .reset_index()
)

lifestyle.to_csv(
    os.path.join(
        EDA_DIR,
        "lifestyle_analysis.csv"
    ),
    index=False
)


# ============================================================
# 13. WEATHER VS PAIN
# ============================================================

print("Creating weather analysis...")

weather_features = [
    "temperature_mean",
    "humidity_mean",
    "precipitation",
    "wind_speed_mean"
]

weather_results = []

for feature in weather_features:

    if feature not in df.columns:
        continue

    correlation = (
        df[
            [
                feature,
                "pain_level"
            ]
        ]
        .corr()
        .iloc[0, 1]
    )

    weather_results.append({
        "weather_feature": feature,
        "pain_correlation": round(
            correlation,
            4
        )
    })

weather_correlation = pd.DataFrame(
    weather_results
)

weather_correlation.to_csv(
    os.path.join(
        EDA_DIR,
        "weather_pain_correlation.csv"
    ),
    index=False
)

print(
    weather_correlation.to_string(
        index=False
    )
)


# ============================================================
# 14. STATE-WISE ANALYSIS
# ============================================================

print("\nCreating state-wise analysis...")

state_analysis = (
    df.groupby("state")
    .agg(
        records=(
            "user_id",
            "count"
        ),
        average_pain=(
            "pain_level",
            "mean"
        ),
        average_cycle_length=(
            "cycle_length_days",
            "mean"
        ),
        average_stress=(
            "stress_score_cycle",
            "mean"
        ),
        average_sleep=(
            "sleep_hours_cycle",
            "mean"
        ),
        average_temperature=(
            "temperature_mean",
            "mean"
        ),
        average_humidity=(
            "humidity_mean",
            "mean"
        ),
        cdc_obesity=(
            "cdc_obesity_prevalence",
            "first"
        ),
        cdc_physical_inactivity=(
            "cdc_physical_inactivity_prevalence",
            "first"
        ),
        cdc_depression=(
            "cdc_depression_prevalence",
            "first"
        ),
        median_household_income=(
            "census_median_household_income",
            "first"
        )
    )
    .reset_index()
)

state_analysis.to_csv(
    os.path.join(
        EDA_DIR,
        "state_analysis.csv"
    ),
    index=False
)


# ============================================================
# 15. CORRELATION MATRIX
# ============================================================

print("\nCreating correlation matrix...")

correlation_features = [

    "cycle_length_days",

    "prev_cycle_length",

    "pain_level",

    "mood_score",

    "stress_score_cycle",

    "sleep_hours_cycle",

    "energy_level",

    "concentration_score",

    "work_hours_lost",

    "estrogen_pgml",

    "progesterone_ngml",

    "overall_health_score",

    "age",

    "bmi",

    "sleep_hours",

    "caffeine_intake",

    "water_intake_liters",

    "stress_score_baseline",

    "temperature_mean",

    "humidity_mean",

    "precipitation",

    "wind_speed_mean",

    "cdc_obesity_prevalence",

    "cdc_physical_inactivity_prevalence",

    "cdc_smoking_prevalence",

    "cdc_depression_prevalence",

    "census_median_household_income"
]

available_features = [
    column
    for column in correlation_features
    if column in df.columns
]

correlation_matrix = (
    df[available_features]
    .corr()
)

correlation_matrix.to_csv(
    os.path.join(
        EDA_DIR,
        "correlation_matrix.csv"
    )
)


# ============================================================
# 16. PAIN CORRELATIONS
# ============================================================

pain_correlations = (
    correlation_matrix[
        "pain_level"
    ]
    .sort_values(
        ascending=False
    )
)

pain_correlations.to_csv(
    os.path.join(
        EDA_DIR,
        "pain_correlations.csv"
    ),
    header=["correlation"]
)

print("\nCorrelations with pain:")

print(
    pain_correlations
)


# ============================================================
# 17. TOP PAIN CORRELATIONS PLOT
# ============================================================

top_correlations = (
    pain_correlations
    .drop(
        labels=["pain_level"],
        errors="ignore"
    )
    .abs()
    .sort_values(
        ascending=False
    )
    .head(10)
)

top_features = (
    top_correlations
    .index
)

top_values = (
    pain_correlations[
        top_features
    ]
)

plt.figure()

top_values.sort_values().plot(
    kind="barh"
)

plt.title(
    "Top 10 Feature Correlations with Pain Level"
)

plt.xlabel(
    "Correlation"
)

plt.ylabel(
    "Feature"
)

save_plot(
    "09_top_pain_correlations.png"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("EDA COMPLETE")
print("=" * 70)

print("\nEDA results saved to:")

print(
    EDA_DIR
)

print("\nFigures saved to:")

print(
    FIGURE_DIR
)