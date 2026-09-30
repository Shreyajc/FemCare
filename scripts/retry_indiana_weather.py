import requests
import pandas as pd

# ============================================================
# RETRY INDIANA WEATHER DATA
# ============================================================

INPUT_FILE = "data/api_fusion/dynamic/open_meteo_row_level.csv"

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"

# Indianapolis coordinates
LATITUDE = 39.76838
LONGITUDE = -86.15804

STATE = "Indiana"


# ============================================================
# 1. LOAD CURRENT FUSED DATA
# ============================================================

print("=" * 70)
print("RETRYING INDIANA WEATHER DATA")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print("\nCurrent dataset rows:", len(df))

# ------------------------------------------------------------
# Find Indiana records
# ------------------------------------------------------------

indiana_mask = df["state"] == STATE

indiana = df[indiana_mask].copy()

print("Indiana records:", len(indiana))

# ------------------------------------------------------------
# Check missing weather values
# ------------------------------------------------------------

weather_columns = [
    "temperature_mean",
    "humidity_mean",
    "precipitation",
    "wind_speed_mean"
]

print("\nMissing Indiana weather values BEFORE retry:")

print(
    indiana[weather_columns].isna().sum()
)


# ============================================================
# 2. DETERMINE REQUIRED DATE RANGE
# ============================================================

indiana["start_date"] = pd.to_datetime(
    indiana["start_date"],
    errors="coerce"
)

min_date = indiana["start_date"].min()
max_date = indiana["start_date"].max()

print(
    "\nRequired Indiana date range:"
)

print(
    min_date.strftime("%Y-%m-%d"),
    "->",
    max_date.strftime("%Y-%m-%d")
)


# ============================================================
# 3. RETRY OPEN-METEO
# ============================================================

params = {

    "latitude": LATITUDE,

    "longitude": LONGITUDE,

    "start_date":
        min_date.strftime("%Y-%m-%d"),

    "end_date":
        max_date.strftime("%Y-%m-%d"),

    "daily": ",".join([
        "temperature_2m_mean",
        "relative_humidity_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_mean"
    ]),

    "timezone": "auto"
}

print("\nRequesting Indiana weather again...")

try:

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=120
    )

    print(
        "HTTP status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

except requests.exceptions.RequestException as e:

    print("\nRETRY FAILED:")
    print(e)
    raise SystemExit


# ============================================================
# 4. CREATE WEATHER DATAFRAME
# ============================================================

daily = data.get("daily")

if not daily:

    print(
        "\nERROR: Open-Meteo returned no daily data."
    )

    raise SystemExit

weather = pd.DataFrame({

    "start_date": daily["time"],

    "temperature_mean":
        daily["temperature_2m_mean"],

    "humidity_mean":
        daily["relative_humidity_2m_mean"],

    "precipitation":
        daily["precipitation_sum"],

    "wind_speed_mean":
        daily["wind_speed_10m_mean"]
})

weather["start_date"] = pd.to_datetime(
    weather["start_date"]
)

print(
    "\nWeather records retrieved:",
    len(weather)
)


# ============================================================
# 5. UPDATE ONLY INDIANA ROWS
# ============================================================

# Convert existing dates

df["start_date"] = pd.to_datetime(
    df["start_date"],
    errors="coerce"
)

# ------------------------------------------------------------
# Create lookup table
# ------------------------------------------------------------

weather_lookup = weather.set_index(
    "start_date"
)


# ------------------------------------------------------------
# Update only missing Indiana values
# ------------------------------------------------------------

for column in weather_columns:

    values = df.loc[
        indiana_mask,
        "start_date"
    ].map(
        weather_lookup[column]
    )

    missing_mask = (
        indiana_mask
        &
        df[column].isna()
    )

    df.loc[
        missing_mask,
        column
    ] = values[missing_mask]


# ============================================================
# 6. SAVE UPDATED DATASET
# ============================================================

df.to_csv(
    INPUT_FILE,
    index=False
)


# ============================================================
# 7. VERIFY
# ============================================================

updated_indiana = df[
    df["state"] == STATE
]

print(
    "\nMissing Indiana weather values AFTER retry:"
)

print(
    updated_indiana[
        weather_columns
    ].isna().sum()
)

print(
    "\nOverall weather missing values:"
)

print(
    df[
        weather_columns
    ].isna().sum()
)

complete = (
    df[
        weather_columns
    ]
    .notna()
    .all(axis=1)
)

coverage = (
    complete.mean() * 100
)

print(
    f"\nOverall weather coverage: "
    f"{coverage:.2f}%"
)

print(
    "\nUpdated file:"
)

print(INPUT_FILE)

print(
    "\n" + "=" * 70
)

print(
    "INDIANA WEATHER RETRY COMPLETE"
)

print(
    "=" * 70
)