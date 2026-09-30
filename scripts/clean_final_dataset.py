import os
import pandas as pd


# ============================================================
# FEMCARE - FINAL DATASET CLEANING
# ============================================================

INPUT_FILE = (
    "data/api_fusion/final/"
    "femcare_final_fused_dataset.csv"
)

OUTPUT_FILE = (
    "data/api_fusion/final/"
    "femcare_final_cleaned.csv"
)


print("=" * 70)
print("FEMCARE - FINAL DATASET CLEANING")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("\nOriginal dataset:")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# 1. PREVIOUS CYCLE LENGTH
# ============================================================

print("\n" + "=" * 70)
print("1. HANDLING PREVIOUS CYCLE LENGTH")
print("=" * 70)

# Cycle 1 has no previous cycle by definition.

df["has_previous_cycle"] = (
    df["prev_cycle_length"]
    .notna()
    .astype(int)
)

print(
    "\nRecords without previous cycle:",
    (df["has_previous_cycle"] == 0).sum()
)

print(
    "Records with previous cycle:",
    (df["has_previous_cycle"] == 1).sum()
)

print(
    "\nprev_cycle_length missing values retained:",
    df["prev_cycle_length"].isna().sum()
)


# ============================================================
# 2. EXERCISE FREQUENCY
# ============================================================

print("\n" + "=" * 70)
print("2. HANDLING EXERCISE FREQUENCY")
print("=" * 70)

missing_exercise = (
    df["exercise_frequency"].isna()
)

print(
    "\nMissing exercise records:",
    missing_exercise.sum()
)

# Missing does NOT mean "No exercise".
# Therefore explicitly label it as Not reported.

df["exercise_frequency"] = (
    df["exercise_frequency"]
    .fillna("Not reported")
)

print(
    "After handling missing values:",
    df["exercise_frequency"].isna().sum()
)

print("\nExercise distribution:")

print(
    df["exercise_frequency"]
    .value_counts()
)


# ============================================================
# 3. LATITUDE / LONGITUDE
# ============================================================

print("\n" + "=" * 70)
print("3. HANDLING COORDINATES")
print("=" * 70)

df["coordinates_available"] = (
    df["latitude"].notna()
    &
    df["longitude"].notna()
).astype(int)

print(
    "\nRecords with coordinates:",
    df["coordinates_available"].sum()
)

print(
    "Records without coordinates:",
    (
        df["coordinates_available"] == 0
    ).sum()
)

print("\nStates without coordinates:")

print(
    df.loc[
        df["coordinates_available"] == 0,
        "state"
    ]
    .value_counts()
)


# ============================================================
# 4. WEATHER VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("4. WEATHER VALIDATION")
print("=" * 70)

weather_columns = [
    "temperature_mean",
    "humidity_mean",
    "precipitation",
    "wind_speed_mean"
]

for column in weather_columns:

    missing = df[column].isna().sum()

    print(
        f"{column}: {missing} missing"
    )


# ============================================================
# 5. DATA QUALITY CHECK
# ============================================================

print("\n" + "=" * 70)
print("5. DATA QUALITY CHECK")
print("=" * 70)

print(
    "\nDuplicate user-cycle records:"
)

duplicates = df.duplicated(
    subset=[
        "user_id",
        "cycle_number"
    ]
).sum()

print(duplicates)


print(
    "\nUnique users:",
    df["user_id"].nunique()
)

print(
    "Unique states:",
    df["state"].nunique()
)


# ============================================================
# 6. SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("FINAL CLEANED DATASET")
print("=" * 70)

print(
    "\nRows:",
    len(df)
)

print(
    "Columns:",
    len(df.columns)
)

print(
    "\nTotal missing cells:",
    df.isna().sum().sum()
)

print("\nRemaining missing values:")

remaining = (
    df.isna()
    .sum()
)

remaining = remaining[
    remaining > 0
]

if remaining.empty:

    print("None")

else:

    print(remaining)


print("\nSaved to:")

print(OUTPUT_FILE)

print("\nCleaning complete.")