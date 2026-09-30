import os
import pandas as pd


# ============================================================
# FEMCARE
# FINAL ANALYTICAL DATA FUSION
# ============================================================

MENSTRUAL_FILE = "data/menstrual_dataset.csv"

CENSUS_FILE = (
    "data/api_fusion/static/census_state.csv"
)

CDC_FILE = (
    "data/api_fusion/static/cdc_places_state.csv"
)

WEATHER_FILE = (
    "data/api_fusion/dynamic/open_meteo_row_level.csv"
)

OUTPUT_FILE = (
    "data/api_fusion/final/"
    "femcare_final_fused_dataset.csv"
)


# ============================================================
# LOAD DATASETS
# ============================================================

def load_datasets():

    print("=" * 70)
    print("FEMCARE - FINAL DATA FUSION")
    print("=" * 70)

    print("\nLoading datasets...")

    menstrual = pd.read_csv(
        MENSTRUAL_FILE
    )

    census = pd.read_csv(
        CENSUS_FILE
    )

    cdc = pd.read_csv(
        CDC_FILE
    )

    weather = pd.read_csv(
        WEATHER_FILE
    )

    print(
        "\nMenstrual:",
        menstrual.shape
    )

    print(
        "Census:",
        census.shape
    )

    print(
        "CDC PLACES:",
        cdc.shape
    )

    print(
        "Open-Meteo:",
        weather.shape
    )

    return (
        menstrual,
        census,
        cdc,
        weather
    )


# ============================================================
# CLEAN STATE NAMES
# ============================================================

def clean_state_columns(
    menstrual,
    census,
    cdc,
    weather
):

    datasets = [
        menstrual,
        census,
        cdc,
        weather
    ]

    for df in datasets:

        if "state" in df.columns:

            df["state"] = (
                df["state"]
                .astype(str)
                .str.strip()
            )

    return (
        menstrual,
        census,
        cdc,
        weather
    )


# ============================================================
# PREPARE DATES
# ============================================================

def prepare_dates(
    menstrual,
    weather
):

    menstrual["start_date"] = pd.to_datetime(
        menstrual["start_date"],
        dayfirst=True,
        errors="coerce"
    )

    weather["start_date"] = pd.to_datetime(
        weather["start_date"],
        errors="coerce"
    )

    return (
        menstrual,
        weather
    )

# ============================================================
# CHECK STATE-LEVEL DATA
# ============================================================

def check_state_duplicates(
    df,
    name
):

    duplicate_count = (
        df["state"]
        .duplicated()
        .sum()
    )

    print(
        f"\n{name} duplicate states:",
        duplicate_count
    )

    if duplicate_count > 0:

        print(
            f"WARNING: {name} contains "
            "duplicate state records."
        )


# ============================================================
# MERGE CENSUS
# ============================================================

def merge_census(
    menstrual,
    census
):

    print(
        "\n" + "-" * 70
    )

    print(
        "1. MERGING CENSUS ACS"
    )

    print(
        "-" * 70
    )

    census_features = [

        "state",

        "state_fips",

        "census_total_population",

        "census_female_population",

        "census_female_20_24",

        "census_female_25_29",

        "census_female_30_34",

        "census_median_household_income"
    ]

    available = [
        column
        for column in census_features
        if column in census.columns
    ]

    census_small = census[
        available
    ].copy()

    before_rows = len(
        menstrual
    )

    menstrual = menstrual.merge(
        census_small,
        on="state",
        how="left",
        validate="many_to_one"
    )

    after_rows = len(
        menstrual
    )

    print(
        "Rows before:",
        before_rows
    )

    print(
        "Rows after:",
        after_rows
    )

    print(
        "Census features added:",
        len(available) - 1
    )

    return menstrual


# ============================================================
# MERGE CDC
# ============================================================

def merge_cdc(
    menstrual,
    cdc
):

    print(
        "\n" + "-" * 70
    )

    print(
        "2. MERGING CDC PLACES"
    )

    print(
        "-" * 70
    )

    cdc_features = [

        "state",

        "state_abbr",

        "cdc_total_population",

        "cdc_obesity_prevalence",

        "cdc_physical_inactivity_prevalence",

        "cdc_smoking_prevalence",

        "cdc_depression_prevalence",

        "cdc_imputation_flag"
    ]

    available = [
        column
        for column in cdc_features
        if column in cdc.columns
    ]

    cdc_small = cdc[
        available
    ].copy()

    before_rows = len(
        menstrual
    )

    menstrual = menstrual.merge(
        cdc_small,
        on="state",
        how="left",
        validate="many_to_one"
    )

    after_rows = len(
        menstrual
    )

    print(
        "Rows before:",
        before_rows
    )

    print(
        "Rows after:",
        after_rows
    )

    print(
        "CDC features added:",
        len(available) - 1
    )

    return menstrual


# ============================================================
# MERGE OPEN-METEO
# ============================================================

def merge_weather(
    menstrual,
    weather
):

    print(
        "\n" + "-" * 70
    )

    print(
        "3. MERGING OPEN-METEO"
    )

    print(
        "-" * 70
    )

    # --------------------------------------------------------
    # Select weather features
    # --------------------------------------------------------

    weather_features = [

        "state",

        "start_date",

        "latitude",

        "longitude",

        "temperature_mean",

        "humidity_mean",

        "precipitation",

        "wind_speed_mean"
    ]

    available = [
        column
        for column in weather_features
        if column in weather.columns
    ]

    weather_small = weather[
        available
    ].copy()

    # --------------------------------------------------------
    # Ensure dates are in the same format
    # --------------------------------------------------------

    weather_small["start_date"] = pd.to_datetime(
        weather_small["start_date"],
        errors="coerce"
    )

    menstrual["start_date"] = pd.to_datetime(
        menstrual["start_date"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Ensure one weather record per state/date
    # --------------------------------------------------------

    duplicate_weather = (
        weather_small
        .duplicated(
            subset=[
                "state",
                "start_date"
            ]
        )
        .sum()
    )

    print(
        "Duplicate state-date weather records:",
        duplicate_weather
    )

    if duplicate_weather > 0:

        print(
            "Removing duplicate weather records..."
        )

        weather_small = (
            weather_small
            .drop_duplicates(
                subset=[
                    "state",
                    "start_date"
                ],
                keep="first"
            )
        )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    before_rows = len(
        menstrual
    )

    menstrual = menstrual.merge(
        weather_small,
        on=[
            "state",
            "start_date"
        ],
        how="left",
        validate="many_to_one"
    )

    after_rows = len(
        menstrual
    )

    print(
        "Rows before:",
        before_rows
    )

    print(
        "Rows after:",
        after_rows
    )

    print(
        "Weather features added:",
        len(available) - 2
    )

    # --------------------------------------------------------
    # Weather coverage
    # --------------------------------------------------------

    weather_columns = [
        "temperature_mean",
        "humidity_mean",
        "precipitation",
        "wind_speed_mean"
    ]

    existing_weather_columns = [
        column
        for column in weather_columns
        if column in menstrual.columns
    ]

    if existing_weather_columns:

        complete_weather = (
            menstrual[
                existing_weather_columns
            ]
            .notna()
            .all(axis=1)
            .mean()
            * 100
        )

        print(
            f"Complete weather coverage: "
            f"{complete_weather:.2f}%"
        )

    return menstrual

# ============================================================
# VALIDATE FUSION
# ============================================================

def validate_dataset(
    df,
    original_rows
):

    print(
        "\n" + "=" * 70
    )

    print(
        "FINAL FUSION VALIDATION"
    )

    print(
        "=" * 70
    )

    print(
        "\nOriginal menstrual rows:",
        original_rows
    )

    print(
        "Final rows:",
        len(df)
    )

    if len(df) == original_rows:

        print(
            "✓ Row count preserved"
        )

    else:

        print(
            "✗ WARNING: Row count changed"
        )

    # --------------------------------------------------------
    # Duplicate cycle records
    # --------------------------------------------------------

    duplicate_cycles = (
        df.duplicated(
            subset=[
                "user_id",
                "cycle_number"
            ]
        )
        .sum()
    )

    print(
        "\nDuplicate user-cycle records:",
        duplicate_cycles
    )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    print(
        "\nMissing values:"
    )

    missing = (
        df.isna()
        .sum()
    )

    missing = (
        missing[
            missing > 0
        ]
        .sort_values(
            ascending=False
        )
    )

    if missing.empty:

        print(
            "✓ No missing values"
        )

    else:

        print(
            missing
        )

    # --------------------------------------------------------
    # State coverage
    # --------------------------------------------------------

    print(
        "\nUnique states in final dataset:",
        df["state"].nunique()
    )

    # --------------------------------------------------------
    # Date coverage
    # --------------------------------------------------------

    print(
        "\nDate range:"
    )

    print(
        df["start_date"].min(),
        "→",
        df["start_date"].max()
    )

    return df


# ============================================================
# SAVE DATASET
# ============================================================

def save_dataset(df):

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "\nSaved to:"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# MAIN
# ============================================================

def main():

    (
        menstrual,
        census,
        cdc,
        weather
    ) = load_datasets()

    original_rows = len(
        menstrual
    )

    # --------------------------------------------------------
    # Clean
    # --------------------------------------------------------

    (
        menstrual,
        census,
        cdc,
        weather
    ) = clean_state_columns(
        menstrual,
        census,
        cdc,
        weather
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    (
        menstrual,
        weather
    ) = prepare_dates(
        menstrual,
        weather
    )

    # --------------------------------------------------------
    # Duplicate checks
    # --------------------------------------------------------

    check_state_duplicates(
        census,
        "Census"
    )

    check_state_duplicates(
        cdc,
        "CDC PLACES"
    )

    # --------------------------------------------------------
    # Fusion
    # --------------------------------------------------------

    fused = merge_census(
        menstrual,
        census
    )

    fused = merge_cdc(
        fused,
        cdc
    )

    fused = merge_weather(
        fused,
        weather
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    fused = fused.sort_values(
        [
            "user_id",
            "cycle_number"
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    fused = validate_dataset(
        fused,
        original_rows
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_dataset(
        fused
    )

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "FINAL ANALYTICAL DATASET CREATED"
    )

    print(
        "=" * 70
    )

    print(
        "\nRows:",
        len(fused)
    )

    print(
        "Columns:",
        len(fused.columns)
    )

    print(
        "\nColumn names:"
    )

    for column in fused.columns:

        print(
            "-",
            column
        )

    print(
        "\nFirst 5 records:"
    )

    print(
        fused.head(5).to_string(
            index=False
        )
    )


if __name__ == "__main__":

    main()