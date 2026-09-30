import os
import requests
import pandas as pd

# ============================================================
# CDC PLACES - STATIC HEALTH CONTEXT API
# ============================================================

API_URL = "https://data.cdc.gov/resource/i46a-9kgh.json"

OUTPUT_FILE = "data/api_fusion/static/cdc_places_state.csv"

# Only request the fields we need.
# This keeps the dataset small and RAM-friendly.
SELECT_FIELDS = [
    "stateabbr",
    "statedesc",
    "countyname",
    "totalpopulation",
    "obesity_crudeprev",
    "lpa_crudeprev",
    "csmoking_crudeprev",
    "depression_crudeprev"
]


def fetch_cdc_data():

    print("=" * 70)
    print("CDC PLACES STATIC API")
    print("=" * 70)

    print("\nFetching CDC PLACES county data...")

    params = {
        "$select": ",".join(SELECT_FIELDS),
        "$limit": 5000
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=60
        )

        print("HTTP status:", response.status_code)

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:

        print("\nCDC API REQUEST FAILED")
        print(e)

        return None

    df = pd.DataFrame(data)

    return df


def main():

    df = fetch_cdc_data()

    if df is None or df.empty:

        print("\nNo data received from CDC.")
        return

    print("\nCounty records received:", len(df))

    # --------------------------------------------------------
    # Convert numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "totalpopulation",
        "obesity_crudeprev",
        "lpa_crudeprev",
        "csmoking_crudeprev",
        "depression_crudeprev"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Create population-weighted state averages
    # --------------------------------------------------------

    def weighted_average(group, value_column):

        valid = group[
            [value_column, "totalpopulation"]
        ].dropna()

        if valid.empty:
            return None

        population = valid["totalpopulation"]

        if population.sum() == 0:
            return valid[value_column].mean()

        return (
            (valid[value_column] * population).sum()
            / population.sum()
        )

    states = []

    for state, group in df.groupby(
        ["stateabbr", "statedesc"],
        dropna=False
    ):

        state_abbr = state[0]
        state_name = state[1]

        result = {

            "state": state_name,

            "state_abbr": state_abbr,

            "cdc_total_population":
                group["totalpopulation"].sum(),

            "cdc_obesity_prevalence":
                weighted_average(
                    group,
                    "obesity_crudeprev"
                ),

            "cdc_physical_inactivity_prevalence":
                weighted_average(
                    group,
                    "lpa_crudeprev"
                ),

            "cdc_smoking_prevalence":
                weighted_average(
                    group,
                    "csmoking_crudeprev"
                ),

            "cdc_depression_prevalence":
                weighted_average(
                    group,
                    "depression_crudeprev"
                )
        }

        states.append(result)

    state_df = pd.DataFrame(states)

    # --------------------------------------------------------
    # Round values
    # --------------------------------------------------------

    numeric_output = [
        "cdc_total_population",
        "cdc_obesity_prevalence",
        "cdc_physical_inactivity_prevalence",
        "cdc_smoking_prevalence",
        "cdc_depression_prevalence"
    ]

    for column in numeric_output:

        state_df[column] = state_df[column].round(3)

    # --------------------------------------------------------
    # Handle missing CDC indicators
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Missing health estimates are NOT treated as zero.
    #
    # We use median imputation across available states.
    #
    # We also retain an imputation flag so the preprocessing
    # remains transparent.
    # --------------------------------------------------------

    cdc_features = [
        "cdc_obesity_prevalence",
        "cdc_physical_inactivity_prevalence",
        "cdc_smoking_prevalence",
        "cdc_depression_prevalence"
    ]

    state_df["cdc_imputation_flag"] = 0

    for column in cdc_features:

        missing_mask = state_df[column].isna()

        if missing_mask.any():

            median_value = state_df[column].median()

            state_df.loc[
                missing_mask,
                column
            ] = median_value

            state_df.loc[
                missing_mask,
                "cdc_imputation_flag"
            ] = 1

            print(
                f"Imputed {missing_mask.sum()} values "
                f"in {column} "
                f"using median = {median_value:.3f}"
            )

    # --------------------------------------------------------
    # Round after imputation
    # --------------------------------------------------------

    for column in cdc_features:

        state_df[column] = state_df[column].round(3)

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    state_df = state_df.sort_values(
        "state"
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    state_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CDC PLACES DATASET CREATED")
    print("=" * 70)

    print("\nRows:", len(state_df))

    print("Columns:", len(state_df.columns))

    print("\nColumns:")

    for column in state_df.columns:

        print("-", column)

    print("\nMissing values:")

    print(
        state_df.isna().sum()
    )

    print("\nFirst 5 records:")

    print(
        state_df.head().to_string(
            index=False
        )
    )

    print("\nSaved to:")

    print(OUTPUT_FILE)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()