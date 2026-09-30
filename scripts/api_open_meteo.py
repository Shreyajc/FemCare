import os
import time
import requests
import pandas as pd

# ============================================================
# OPEN-METEO DYNAMIC API
# CORRECTED STATE-CAPITAL BASED ROW-LEVEL FUSION
# ============================================================

INPUT_FILE = "data/menstrual_dataset.csv"

OUTPUT_FILE = (
    "data/api_fusion/dynamic/"
    "open_meteo_row_level.csv"
)

COORDINATE_FILE = (
    "data/api_fusion/dynamic/"
    "us_state_capital_coordinates.csv"
)

GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)

WEATHER_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)


# ============================================================
# U.S. STATE -> CAPITAL MAPPING
# ============================================================
#
# We use state capitals because the menstrual dataset contains
# state information but does NOT contain the user's exact city.
#
# This gives us a consistent representative location for
# each state.
# ============================================================

STATE_CAPITALS = {

    "Alabama": "Montgomery",
    "Alaska": "Juneau",
    "Arizona": "Phoenix",
    "Arkansas": "Little Rock",
    "California": "Sacramento",
    "Colorado": "Denver",
    "Connecticut": "Hartford",
    "Delaware": "Dover",
    "Florida": "Tallahassee",
    "Georgia": "Atlanta",
    "Hawaii": "Honolulu",
    "Idaho": "Boise",
    "Illinois": "Springfield",
    "Indiana": "Indianapolis",
    "Iowa": "Des Moines",
    "Kansas": "Topeka",
    "Kentucky": "Frankfort",
    "Louisiana": "Baton Rouge",
    "Maine": "Augusta",
    "Maryland": "Annapolis",
    "Massachusetts": "Boston",
    "Michigan": "Lansing",
    "Minnesota": "Saint Paul",
    "Mississippi": "Jackson",
    "Missouri": "Jefferson City",
    "Montana": "Helena",
    "Nebraska": "Lincoln",
    "Nevada": "Carson City",
    "New Hampshire": "Concord",
    "New Jersey": "Trenton",
    "New Mexico": "Santa Fe",
    "New York": "Albany",
    "North Carolina": "Raleigh",
    "North Dakota": "Bismarck",
    "Ohio": "Columbus",
    "Oklahoma": "Oklahoma City",
    "Oregon": "Salem",
    "Pennsylvania": "Harrisburg",
    "Rhode Island": "Providence",
    "South Carolina": "Columbia",
    "South Dakota": "Pierre",
    "Tennessee": "Nashville",
    "Texas": "Austin",
    "Utah": "Salt Lake City",
    "Vermont": "Montpelier",
    "Virginia": "Richmond",
    "Washington": "Olympia",
    "West Virginia": "Charleston",
    "Wisconsin": "Madison",
    "Wyoming": "Cheyenne"
}


# ============================================================
# 1. LOAD MENSTRUAL DATA
# ============================================================

def load_menstrual_data():

    print("=" * 70)
    print("OPEN-METEO DYNAMIC API")
    print("CORRECTED STATE-CAPITAL ROW-LEVEL FUSION")
    print("=" * 70)

    print("\nLoading menstrual dataset...")

    df = pd.read_csv(INPUT_FILE)

    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    # Convert menstrual cycle start date

    df["start_date"] = pd.to_datetime(
        df["start_date"],
        dayfirst=True,
        errors="coerce"
    )

    invalid_dates = df["start_date"].isna().sum()

    print("Invalid dates:", invalid_dates)

    return df


# ============================================================
# 2. GEOCODE STATE CAPITAL
# ============================================================

def geocode_capital(state_name, capital_name):

    # --------------------------------------------------------
    # The query explicitly contains:
    #
    # capital + state + United States
    #
    # This prevents the previous problem where a generic state
    # search returned an unrelated U.S. location.
    # --------------------------------------------------------

    query = (
        f"{capital_name}, "
        f"{state_name}, "
        f"United States"
    )

    params = {
        "name": query,
        "count": 10,
        "language": "en",
        "format": "json"
    }

    try:

        response = requests.get(
            GEOCODING_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        # ----------------------------------------------------
        # Verify BOTH:
        #
        # 1. country = United States
        # 2. admin1 = requested state
        #
        # We will NOT accept a result if these don't match.
        # ----------------------------------------------------

        for result in results:

            country_code = (
                result.get("country_code", "")
                .lower()
            )

            returned_state = (
                result.get("admin1", "")
                .strip()
                .lower()
            )

            expected_state = (
                state_name
                .strip()
                .lower()
            )

            if (
                country_code == "us"
                and
                returned_state == expected_state
            ):

                return {
                    "state": state_name,
                    "capital": capital_name,
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude"),
                    "country": result.get("country"),
                    "admin1": result.get("admin1")
                }

        print(
            f"ERROR: Could not verify "
            f"{capital_name}, {state_name}"
        )

    except requests.exceptions.RequestException as e:

        print(
            f"Geocoding failed for "
            f"{capital_name}, {state_name}: {e}"
        )

    return {
        "state": state_name,
        "capital": capital_name,
        "latitude": None,
        "longitude": None,
        "country": None,
        "admin1": None
    }


# ============================================================
# 3. BUILD VERIFIED STATE COORDINATES
# ============================================================

def build_coordinates(df):

    print("\n" + "=" * 70)
    print("BUILDING VERIFIED U.S. STATE CAPITAL COORDINATES")
    print("=" * 70)

    states = (
        df["state"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    print("Unique states in menstrual dataset:", len(states))

    locations = []

    for index, state in enumerate(
        states,
        start=1
    ):

        if state not in STATE_CAPITALS:

            print(
                f"[{index}/{len(states)}] "
                f"ERROR: No capital mapping for {state}"
            )

            locations.append({
                "state": state,
                "capital": None,
                "latitude": None,
                "longitude": None,
                "country": None,
                "admin1": None
            })

            continue

        capital = STATE_CAPITALS[state]

        print(
            f"[{index}/{len(states)}] "
            f"{state} -> {capital}"
        )

        result = geocode_capital(
            state,
            capital
        )

        locations.append(result)

        time.sleep(0.2)

    location_df = pd.DataFrame(locations)

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    valid = location_df[
        location_df["latitude"].notna()
        &
        location_df["longitude"].notna()
    ]

    print(
        "\nVerified locations:",
        len(valid),
        "/",
        len(location_df)
    )

    # --------------------------------------------------------
    # Save coordinate table
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(COORDINATE_FILE),
        exist_ok=True
    )

    location_df.to_csv(
        COORDINATE_FILE,
        index=False
    )

    print(
        "\nCoordinates saved to:"
    )

    print(COORDINATE_FILE)

    return location_df


# ============================================================
# 4. FETCH HISTORICAL WEATHER
# ============================================================

def fetch_weather_for_state(
    state,
    latitude,
    longitude,
    start_date,
    end_date
):

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "start_date":
            start_date.strftime("%Y-%m-%d"),

        "end_date":
            end_date.strftime("%Y-%m-%d"),

        "daily": ",".join([
            "temperature_2m_mean",
            "relative_humidity_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_mean"
        ]),

        "timezone": "auto"
    }

    try:

        response = requests.get(
            WEATHER_URL,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        daily = data.get("daily")

        if not daily:

            print(
                f"WARNING: No weather data for {state}"
            )

            return pd.DataFrame()

        weather_df = pd.DataFrame({

            "date": daily["time"],

            "temperature_mean":
                daily["temperature_2m_mean"],

            "humidity_mean":
                daily[
                    "relative_humidity_2m_mean"
                ],

            "precipitation":
                daily["precipitation_sum"],

            "wind_speed_mean":
                daily["wind_speed_10m_mean"]
        })

        weather_df["state"] = state

        weather_df["latitude"] = latitude

        weather_df["longitude"] = longitude

        return weather_df

    except requests.exceptions.RequestException as e:

        print(
            f"Weather request failed for "
            f"{state}: {e}"
        )

        return pd.DataFrame()


# ============================================================
# 5. FETCH WEATHER FOR REQUIRED STATE DATE RANGES
# ============================================================

def build_weather_dataset(
    df,
    locations
):

    print("\n" + "=" * 70)
    print("FETCHING HISTORICAL WEATHER")
    print("=" * 70)

    weather_results = []

    for _, location in locations.iterrows():

        state = location["state"]

        latitude = location["latitude"]

        longitude = location["longitude"]

        # ----------------------------------------------------
        # Skip states where coordinates couldn't be verified
        # ----------------------------------------------------

        if (
            pd.isna(latitude)
            or
            pd.isna(longitude)
        ):

            print(
                f"Skipping {state}: "
                f"verified coordinates unavailable"
            )

            continue

        state_records = df[
            df["state"] == state
        ]

        if state_records.empty:

            continue

        min_date = (
            state_records["start_date"].min()
        )

        max_date = (
            state_records["start_date"].max()
        )

        print(
            f"\nFetching {state} "
            f"({location['capital']}): "
            f"{min_date.date()} -> "
            f"{max_date.date()}"
        )

        weather = fetch_weather_for_state(
            state,
            latitude,
            longitude,
            min_date,
            max_date
        )

        if not weather.empty:

            weather_results.append(weather)

        time.sleep(0.5)

    if not weather_results:

        return pd.DataFrame()

    return pd.concat(
        weather_results,
        ignore_index=True
    )


# ============================================================
# 6. ROW-LEVEL FUSION
# ============================================================

def fuse_weather_with_menstrual(
    df,
    weather_df
):

    print("\n" + "=" * 70)
    print("ROW-LEVEL FUSION")
    print("=" * 70)

    # --------------------------------------------------------
    # Create date key
    # --------------------------------------------------------

    df["weather_date"] = (
        df["start_date"]
        .dt.strftime("%Y-%m-%d")
    )

    weather_df["date"] = pd.to_datetime(
        weather_df["date"],
        errors="coerce"
    )

    weather_df["weather_date"] = (
        weather_df["date"]
        .dt.strftime("%Y-%m-%d")
    )

    # --------------------------------------------------------
    # Join:
    #
    # state + exact cycle start date
    #
    # This is our row-level contextual fusion.
    # --------------------------------------------------------

    fused = df.merge(

        weather_df[
            [
                "state",
                "weather_date",
                "latitude",
                "longitude",
                "temperature_mean",
                "humidity_mean",
                "precipitation",
                "wind_speed_mean"
            ]
        ],

        on=[
            "state",
            "weather_date"
        ],

        how="left"
    )

    fused = fused.drop(
        columns=["weather_date"]
    )

    return fused


# ============================================================
# 7. MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_menstrual_data()

    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    locations = build_coordinates(df)

    print("\nVerified location results:")

    print(
        locations.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    weather_df = build_weather_dataset(
        df,
        locations
    )

    if weather_df.empty:

        print(
            "\nERROR: No weather data was retrieved."
        )

        return

    print(
        "\nWeather records retrieved:",
        len(weather_df)
    )

    # --------------------------------------------------------
    # Fusion
    # --------------------------------------------------------

    fused_df = fuse_weather_with_menstrual(
        df,
        weather_df
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    fused_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    weather_columns = [
        "temperature_mean",
        "humidity_mean",
        "precipitation",
        "wind_speed_mean"
    ]

    print("\n" + "=" * 70)
    print("OPEN-METEO ROW-LEVEL FUSION COMPLETE")
    print("=" * 70)

    print(
        "\nRows:",
        len(fused_df)
    )

    print(
        "Columns:",
        len(fused_df.columns)
    )

    print(
        "\nWeather features added:"
    )

    for column in weather_columns:

        print("-", column)

    print(
        "\nWeather missing values:"
    )

    print(
        fused_df[
            weather_columns
        ].isna().sum()
    )

    complete_weather = (
        fused_df[
            weather_columns
        ]
        .notna()
        .all(axis=1)
    )

    coverage = (
        complete_weather.mean()
        * 100
    )

    print(
        "\nWeather coverage:"
    )

    print(
        f"{coverage:.2f}% of menstrual "
        f"records have complete weather data"
    )

    # --------------------------------------------------------
    # Verify geographical correctness
    # --------------------------------------------------------

    print(
        "\nGeographical verification:"
    )

    verification = locations[
        [
            "state",
            "capital",
            "latitude",
            "longitude",
            "country",
            "admin1"
        ]
    ]

    print(
        verification.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Show first fused records
    # --------------------------------------------------------

    print(
        "\nFirst 5 fused records:"
    )

    print(
        fused_df[
            [
                "user_id",
                "start_date",
                "state",
                "pain_level",
                "latitude",
                "longitude",
                "temperature_mean",
                "humidity_mean",
                "precipitation",
                "wind_speed_mean"
            ]
        ]
        .head()
        .to_string(index=False)
    )

    print(
        "\nSaved to:"
    )

    print(OUTPUT_FILE)


if __name__ == "__main__":

    main()