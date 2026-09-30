import os
import requests
import pandas as pd

# ============================================================
# FEMCARE - USDA FOODDATA CENTRAL API
# Dynamic Nutrition API
# ============================================================

API_URL = (
    "https://api.nal.usda.gov/fdc/v1/foods/search"
)

API_KEY = os.getenv("USDA_API_KEY")

OUTPUT_FILE = (
    "data/api_fusion/dynamic/"
    "usda_fooddata_nutrition.csv"
)

# ------------------------------------------------------------
# Foods relevant to menstrual-health nutrition context
# ------------------------------------------------------------

FOODS = [
    "spinach",
    "lentils",
    "chickpeas",
    "pumpkin seeds",
    "salmon",
    "yogurt",
    "banana",
    "almonds",
    "broccoli",
    "egg"
]


# ============================================================
# SEARCH ONE FOOD
# ============================================================

def search_food(food_name):

    print(
        f"\nSearching USDA FoodData Central: {food_name}"
    )

    params = {
        "api_key": API_KEY,
        "query": food_name,

        # Prefer USDA Foundation Foods
        "dataType": "Foundation",

        # Get several candidates instead of blindly
        # accepting the first result
        "pageSize": 10
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )

        print(
            "HTTP status:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:

        print("\nUSDA API request failed:")
        print(e)

        return None

    foods = data.get(
        "foods",
        []
    )

    if not foods:

        print(
            "No Foundation Food found for:",
            food_name
        )

        return None

    # --------------------------------------------------------
    # Prefer an exact/close generic food name.
    # Avoid products with obvious brand information.
    # --------------------------------------------------------

    search_lower = food_name.lower()

    exact_matches = []

    for food in foods:

        description = food.get(
            "description",
            ""
        ).lower()

        brand_owner = food.get(
            "brandOwner"
        )

        # Prefer records whose description contains
        # the requested food and has no brand owner.
        if (
            search_lower in description
            and not brand_owner
        ):

            exact_matches.append(
                food
            )

    if exact_matches:

        selected = exact_matches[0]

    else:

        selected = foods[0]

    print(
        "Selected:",
        selected.get("description")
    )

    print(
        "Data type:",
        selected.get("dataType")
    )

    return selected


# ============================================================
# EXTRACT NUTRIENTS
# ============================================================

def extract_nutrients(food):

    nutrients = {}

    for nutrient in food.get(
        "foodNutrients",
        []
    ):

        name = nutrient.get(
            "nutrientName",
            ""
        ).lower()

        value = nutrient.get(
            "value"
        )

        if "energy" in name:

            nutrients[
                "energy_kcal_100g"
            ] = value

        elif name == "protein":

            nutrients[
                "protein_g_100g"
            ] = value

        elif (
            "carbohydrate" in name
            and "by difference" in name
        ):

            nutrients[
                "carbohydrates_g_100g"
            ] = value

        elif name == "total lipid (fat)":

            nutrients[
                "fat_g_100g"
            ] = value

        elif name == "fiber, total dietary":

            nutrients[
                "fiber_g_100g"
            ] = value

        elif name == "total sugars":

            nutrients[
                "sugars_g_100g"
            ] = value

        elif name == "calcium, ca":

            nutrients[
                "calcium_mg_100g"
            ] = value

        elif name == "iron, fe":

            nutrients[
                "iron_mg_100g"
            ] = value

        elif name == "magnesium, mg":

            nutrients[
                "magnesium_mg_100g"
            ] = value

        elif name == "vitamin b-6":

            nutrients[
                "vitamin_b6_mg_100g"
            ] = value

        elif name == "vitamin b-12":

            nutrients[
                "vitamin_b12_ug_100g"
            ] = value

    return nutrients


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("USDA FOODDATA CENTRAL")
    print("FEMCARE NUTRITION API")
    print("=" * 70)

    if not API_KEY:

        raise ValueError(
            "USDA_API_KEY is not set.\n\n"
            "Run this in PowerShell first:\n"
            '$env:USDA_API_KEY="YOUR_API_KEY"'
        )

    records = []

    for food_name in FOODS:

        food = search_food(
            food_name
        )

        if food is None:

            continue

        nutrients = extract_nutrients(
            food
        )

        record = {

            "search_food":
                food_name,

            "fdc_id":
                food.get("fdcId"),

            "food_name":
                food.get("description"),

            "data_type":
                food.get("dataType"),

            **nutrients
        }

        records.append(
            record
        )

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    df = pd.DataFrame(
        records
    )

    if df.empty:

        print(
            "\nNo nutrition records received."
        )

        return

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [

        "fdc_id",

        "energy_kcal_100g",

        "protein_g_100g",

        "carbohydrates_g_100g",

        "fat_g_100g",

        "fiber_g_100g",

        "sugars_g_100g",

        "calcium_mg_100g",

        "iron_mg_100g",

        "magnesium_mg_100g",

        "vitamin_b6_mg_100g",

        "vitamin_b12_ug_100g"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "USDA FOODDATA CENTRAL COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "\nRows:",
        len(df)
    )

    print(
        "Columns:",
        len(df.columns)
    )

    print(
        "\nColumns:"
    )

    for column in df.columns:

        print(
            "-",
            column
        )

    print(
        "\nMissing values:"
    )

    print(
        df.isna().sum()
    )

    print(
        "\nNutrition records:"
    )

    print(
        df.to_string(
            index=False
        )
    )

    print(
        "\nSaved to:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":

    main()