import pandas as pd
import numpy as np


# ============================================================
# FEMCARE - EDA MODULE
# ============================================================

DATA_PATH = (
    "data/api_fusion/final/"
    "femcare_final_cleaned.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

#@staticmethod
def load_data():
    """
    Load the final cleaned fused dataset.
    """

    df = pd.read_csv(DATA_PATH)

    if "start_date" in df.columns:
        df["start_date"] = pd.to_datetime(
            df["start_date"],
            errors="coerce"
        )

    return df


# ============================================================
# DATASET OVERVIEW
# ============================================================

def get_dataset_overview(df):

    return {
        "records": len(df),

        "features": len(df.columns),

        "users": df["user_id"].nunique()
        if "user_id" in df.columns
        else 0,

        "states": df["state"].nunique()
        if "state" in df.columns
        else 0,

        "duplicates": df.duplicated(
            subset=["user_id", "cycle_number"]
        ).sum(),

        "missing_cells": df.isna().sum().sum()
    }


# ============================================================
# MISSING VALUE SUMMARY
# ============================================================

def get_missing_summary(df):

    result = (
        df.isna()
        .sum()
        .reset_index()
    )

    result.columns = [
        "feature",
        "missing"
    ]

    result["percentage"] = (
        result["missing"]
        / len(df)
        * 100
    ).round(2)

    return result[
        result["missing"] > 0
    ].sort_values(
        "missing",
        ascending=False
    )


# ============================================================
# NUMERICAL SUMMARY
# ============================================================

def get_numeric_summary(df):

    numeric = df.select_dtypes(
        include=np.number
    )

    summary = numeric.describe().T

    summary["median"] = numeric.median()

    summary["missing"] = (
        numeric.isna().sum()
    )

    return summary


# ============================================================
# CATEGORICAL DISTRIBUTION
# ============================================================

def get_category_distribution(
    df,
    column
):

    if column not in df.columns:
        return pd.DataFrame()

    result = (
        df[column]
        .value_counts(
            dropna=False
        )
        .reset_index()
    )

    result.columns = [
        "category",
        "count"
    ]

    result["percentage"] = (
        result["count"]
        / len(df)
        * 100
    ).round(2)

    return result


# ============================================================
# PAIN ANALYSIS
# ============================================================

def get_pain_analysis(df):

    features = [
        "pain_level",
        "stress_score_cycle",
        "sleep_hours_cycle",
        "mood_score",
        "energy_level",
        "concentration_score",
        "work_hours_lost",
        "overall_health_score"
    ]

    available = [
        column
        for column in features
        if column in df.columns
    ]

    return df[available]


# ============================================================
# PAIN VS FEATURE
# ============================================================

def get_pain_relationship(
    df,
    feature
):

    if (
        "pain_level" not in df.columns
        or feature not in df.columns
    ):
        return pd.DataFrame()

    result = (
        df.groupby("pain_level")[
            feature
        ]
        .mean()
        .reset_index()
    )

    result.columns = [
        "pain_level",
        f"average_{feature}"
    ]

    return result


# ============================================================
# LIFESTYLE ANALYSIS
# ============================================================

def get_lifestyle_analysis(df):

    if "exercise_frequency" not in df.columns:
        return pd.DataFrame()

    result = (
        df.groupby(
            "exercise_frequency",
            dropna=False
        )
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

    return result


# ============================================================
# WEATHER ANALYSIS
# ============================================================

def get_weather_correlation(df):

    weather_features = [
        "temperature_mean",
        "humidity_mean",
        "precipitation",
        "wind_speed_mean"
    ]

    results = []

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

        results.append({
            "feature": feature,
            "correlation_with_pain": round(
                correlation,
                4
            )
        })

    return pd.DataFrame(results)


# ============================================================
# STATE ANALYSIS
# ============================================================

def get_state_analysis(df):

    required = [
        "state",
        "pain_level",
        "cycle_length_days",
        "stress_score_cycle",
        "sleep_hours_cycle"
    ]

    available = [
        column
        for column in required
        if column in df.columns
    ]

    result = (
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
            )
        )
        .reset_index()
    )

    return result


# ============================================================
# CORRELATION MATRIX
# ============================================================

def get_correlation_matrix(df):

    features = [

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

    available = [
        column
        for column in features
        if column in df.columns
    ]

    return df[
        available
    ].corr()


# ============================================================
# PAIN CORRELATIONS
# ============================================================

def get_pain_correlations(df):

    matrix = get_correlation_matrix(df)

    if "pain_level" not in matrix.columns:
        return pd.Series(dtype=float)

    return (
        matrix["pain_level"]
        .sort_values(
            ascending=False
        )
    )


# ============================================================
# FUSION FEATURE GROUPS
# ============================================================

def get_fusion_feature_groups(df):

    groups = {

        "Original Menstrual Dataset": [
            "user_id",
            "cycle_number",
            "start_date",
            "cycle_length_days",
            "prev_cycle_length",
            "cycle_phase",
            "flow_level",
            "pain_level",
            "pms_symptoms",
            "mood_score",
            "stress_score_cycle",
            "sleep_hours_cycle",
            "energy_level",
            "concentration_score",
            "work_hours_lost",
            "estrogen_pgml",
            "progesterone_ngml",
            "ovulation_result",
            "overall_health_score",
            "log_consistency_score",
            "prepared_before_period",
            "state",
            "age",
            "bmi",
            "diet_quality",
            "exercise_frequency",
            "sleep_hours",
            "caffeine_intake",
            "water_intake_liters",
            "alcohol_consumption",
            "smoking_status",
            "birth_control_use",
            "pcos_diagnosed",
            "stress_score_baseline"
        ],

        "Census ACS": [
            "state_fips",
            "census_total_population",
            "census_female_population",
            "census_female_20_24",
            "census_female_25_29",
            "census_female_30_34",
            "census_median_household_income",
            "state_abbr"
        ],

        "CDC PLACES": [
            "cdc_total_population",
            "cdc_obesity_prevalence",
            "cdc_physical_inactivity_prevalence",
            "cdc_smoking_prevalence",
            "cdc_depression_prevalence",
            "cdc_imputation_flag"
        ],

        "Open-Meteo": [
            "latitude",
            "longitude",
            "temperature_mean",
            "humidity_mean",
            "precipitation",
            "wind_speed_mean"
        ]
    }

    # Keep only columns actually present
    for group in groups:

        groups[group] = [
            column
            for column in groups[group]
            if column in df.columns
        ]

    return groups