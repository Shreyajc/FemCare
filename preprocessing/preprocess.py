import pandas as pd

# -----------------------------
# Load dataset
# -----------------------------

df = pd.read_csv("data/menstrual_dataset.csv")

print("Original Shape :", df.shape)

# -----------------------------
# Remove duplicate rows
# -----------------------------

duplicates = df.duplicated().sum()

print("Duplicate Rows :", duplicates)

df = df.drop_duplicates()

# -----------------------------
# Separate numeric/categorical
# -----------------------------

numeric_columns = df.select_dtypes(include=["number"]).columns

categorical_columns = df.select_dtypes(exclude=["number"]).columns

# -----------------------------
# Fill numeric missing values
# -----------------------------

for col in numeric_columns:
    df[col] = df[col].fillna(df[col].median())

# -----------------------------
# Fill categorical missing values
# -----------------------------

for col in categorical_columns:
    df[col] = df[col].fillna("Unknown")

# -----------------------------
# Save cleaned dataset
# -----------------------------

df.to_csv(
    "data/cleaned_dataset.csv",
    index=False
)

print("\nCleaning Completed!")

print("Final Shape :", df.shape)

print("Remaining Missing Values :")

print(df.isnull().sum().sum())