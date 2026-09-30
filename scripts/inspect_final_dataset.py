import pandas as pd

# ============================================================
# FEMCARE - FINAL DATASET INSPECTION
# ============================================================

FILE = "data/api_fusion/final/femcare_final_fused_dataset.csv"


print("=" * 70)
print("FEMCARE - FINAL FUSED DATASET INSPECTION")
print("=" * 70)


# ------------------------------------------------------------
# LOAD DATASET
# ------------------------------------------------------------

df = pd.read_csv(FILE)

print("\nDataset shape:")
print(df.shape)

print("\nRows:", len(df))
print("Columns:", len(df.columns))

print("\nUnique users:", df["user_id"].nunique())
print("Unique states:", df["state"].nunique())


# ------------------------------------------------------------
# MISSING VALUE ANALYSIS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("MISSING VALUE ANALYSIS")
print("=" * 70)

missing = df.isna().sum()

missing = missing[missing > 0].sort_values(
    ascending=False
)

if missing.empty:

    print("\nNo missing values.")

else:

    print("\nMissing values:")
    print(missing)

    print("\nMissing percentage:")

    for column, count in missing.items():

        percentage = (
            count / len(df)
        ) * 100

        print(
            f"{column}: "
            f"{count} "
            f"({percentage:.2f}%)"
        )


# ------------------------------------------------------------
# PREV CYCLE LENGTH
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("1. PREVIOUS CYCLE LENGTH")
print("=" * 70)

if "prev_cycle_length" in df.columns:

    missing_prev = df[
        df["prev_cycle_length"].isna()
    ]

    print(
        "\nMissing prev_cycle_length:",
        len(missing_prev)
    )

    print(
        "Total:",
        len(df)
    )

    print(
        "Percentage:",
        round(
            len(missing_prev) / len(df) * 100,
            2
        ),
        "%"
    )

    print("\nCycle numbers of missing records:")

    print(
        missing_prev[
            "cycle_number"
        ]
        .value_counts()
        .sort_index()
        .head(20)
    )


# ------------------------------------------------------------
# EXERCISE FREQUENCY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("2. EXERCISE FREQUENCY")
print("=" * 70)

if "exercise_frequency" in df.columns:

    print(
        "\nMissing:",
        df["exercise_frequency"].isna().sum()
    )

    print(
        "Non-missing:",
        df["exercise_frequency"].notna().sum()
    )

    print("\nExisting values:")

    print(
        df["exercise_frequency"]
        .value_counts(dropna=False)
    )


# ------------------------------------------------------------
# LATITUDE / LONGITUDE
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("3. LATITUDE / LONGITUDE")
print("=" * 70)

for column in [
    "latitude",
    "longitude"
]:

    if column in df.columns:

        print(
            f"\n{column} missing:",
            df[column].isna().sum()
        )

        print(
            f"{column} non-missing:",
            df[column].notna().sum()
        )


# ------------------------------------------------------------
# STATES WITH MISSING COORDINATES
# ------------------------------------------------------------

print("\nStates with missing coordinates:")

coordinate_missing = df[
    df["latitude"].isna()
    |
    df["longitude"].isna()
]

print(
    coordinate_missing[
        [
            "state",
            "latitude",
            "longitude"
        ]
    ]
    .drop_duplicates()
    .to_string(index=False)
)


# ------------------------------------------------------------
# WEATHER COMPLETENESS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("4. WEATHER COMPLETENESS")
print("=" * 70)

weather_columns = [
    "temperature_mean",
    "humidity_mean",
    "precipitation",
    "wind_speed_mean"
]

for column in weather_columns:

    if column in df.columns:

        print(
            column,
            "missing:",
            df[column].isna().sum()
        )


# ------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

print("\nDataset:", FILE)
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Users:", df["user_id"].nunique())
print("States:", df["state"].nunique())

print(
    "\nTotal missing cells:",
    int(df.isna().sum().sum())
)

print("\nInspection complete.")