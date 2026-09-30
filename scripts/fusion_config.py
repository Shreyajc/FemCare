# State coordinates will be generated through Nominatim
# and cached locally.

START_DATE = "2024-01-01"
END_DATE = "2025-01-31"

# Keep API requests small and controlled.
REQUEST_DELAY = 1.1

# Healthcare search radius in meters.
HEALTHCARE_RADIUS = 10000

# Open Food Facts products to use for the nutrition reference dataset.
FOOD_PRODUCTS = [
    "spinach",
    "lentils",
    "banana",
    "almonds",
    "yogurt",
    "oats",
    "broccoli",
    "chickpeas",
    "egg",
    "salmon"
]