import os
import requests
import pandas as pd

# ============================================================
# CENSUS ACS STATIC API COLLECTION
# ============================================================

API_URL = "https://api.census.gov/data/2024/acs/acs5"

OUTPUT_FILE = "data/api_fusion/static/census_state.csv"

# ------------------------------------------------------------
# Read the Census API key from an environment variable.
# Never commit an actual key to the repository.
# ------------------------------------------------------------

API_KEY = os.getenv("CENSUS_API_KEY", "")


# ------------------------------------------------------------
# Census variables
# ------------------------------------------------------------

VARIABLES = [
    "NAME",
    "B01001_001E",   # Total population
    "B01001_026E",   # Female population

    # Female age groups
    "B01001_032E",   # Female 20 years
    "B01001_033E",   # Female 21 years
    "B01001_034E",   # Female 22-24 years
    "B01001_035E",   # Female 25-29 years
    "B01001_036E",   # Female 30-34 years

    "B19013_001E"    # Median household income
]


def main():

    print("=" * 70)
    print("CENSUS ACS STATIC API")
    print("=" * 70)

    if not API_KEY:
        print("\nERROR: Census API key has not been configured.")
        print("Set the CENSUS_API_KEY environment variable and run this script again.")
        return

    params = {
        "get": ",".join(VARIABLES),
        "for": "state:*",
        "key": API_KEY
    }

    print("\nFetching Census ACS state data...")

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )

        print("HTTP status:", response.status_code)

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:
        print("\nAPI REQUEST FAILED")
        print(e)
        return

    # --------------------------------------------------------
    # Convert API response to DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(
        data[1:],
        columns=data[0]
    )

    # --------------------------------------------------------
    # Rename columns into readable project names
    # --------------------------------------------------------

    df = df.rename(columns={
        "NAME": "state",

        "B01001_001E":
            "census_total_population",

        "B01001_026E":
            "census_female_population",

        "B01001_032E":
            "female_age_20",

        "B01001_033E":
            "female_age_21",

        "B01001_034E":
            "female_age_22_24",

        "B01001_035E":
            "census_female_25_29",

        "B01001_036E":
            "census_female_30_34",

        "B19013_001E":
            "census_median_household_income",

        "state":
            "state_fips"
    })

    # --------------------------------------------------------
    # Convert numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "census_total_population",
        "census_female_population",
        "female_age_20",
        "female_age_21",
        "female_age_22_24",
        "census_female_25_29",
        "census_female_30_34",
        "census_median_household_income"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Create combined female 20-24 feature
    # --------------------------------------------------------

    df["census_female_20_24"] = (
        df["female_age_20"]
        + df["female_age_21"]
        + df["female_age_22_24"]
    )

    # --------------------------------------------------------
    # Keep only useful project features
    # --------------------------------------------------------

    df = df[
        [
            "state",
            "state_fips",
            "census_total_population",
            "census_female_population",
            "census_female_20_24",
            "census_female_25_29",
            "census_female_30_34",
            "census_median_household_income"
        ]
    ]

    # --------------------------------------------------------
    # Sort by state
    # --------------------------------------------------------

    df = df.sort_values("state").reset_index(drop=True)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CENSUS API COLLECTION COMPLETE")
    print("=" * 70)

    print("\nRows:", len(df))
    print("Columns:", len(df.columns))

    print("\nColumns:")
    for column in df.columns:
        print("-", column)

    print("\nMissing values:")
    print(df.isna().sum().sum())

    print("\nFirst 5 records:")
    print(df.head().to_string(index=False))

    print("\nSaved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
