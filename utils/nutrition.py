import json
from pathlib import Path

import pandas as pd


# =============================================================================
# PATHS
# =============================================================================

RECIPE_PATH = Path("data/nutrition/recipes.json")

USDA_PATH = Path(
    "data/api_fusion/dynamic/usda_fooddata_nutrition.csv"
)


# =============================================================================
# RECIPES
# =============================================================================

def load_recipes():
    """Load the local FemCare recipe database."""

    if not RECIPE_PATH.exists():
        return []

    try:
        with open(RECIPE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []


def filter_recipes(
    recipes,
    nutrition_focus="All",
):
    """Filter recipes according to nutrition focus."""

    if nutrition_focus == "All":
        return recipes

    return [
        recipe
        for recipe in recipes
        if nutrition_focus in recipe.get("nutrition_focus", [])
    ]


# =============================================================================
# USDA FOODDATA CENTRAL
# =============================================================================

def load_usda_foods():
    """
    Load the locally stored USDA FoodData Central nutrition dataset.
    """

    if not USDA_PATH.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(USDA_PATH)
    except Exception:
        return pd.DataFrame()


def get_usda_food_names(df):
    """
    Return unique food names from the USDA dataset.
    """

    if df.empty or "food_name" not in df.columns:
        return []

    return sorted(
        df["food_name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def get_food_record(df, food_name):
    """
    Return the selected food record.
    """

    if df.empty or "food_name" not in df.columns:
        return None

    matches = df[
        df["food_name"].astype(str) == str(food_name)
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def format_nutrient(value, unit):
    """
    Format nutrient values safely.
    Missing values are displayed as 'Not available'
    instead of being converted to zero.
    """

    if pd.isna(value):
        return "Not available"

    try:
        return f"{float(value):.2f} {unit}"
    except (ValueError, TypeError):
        return "Not available"