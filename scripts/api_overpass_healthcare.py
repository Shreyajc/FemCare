import os
import time
import requests
import pandas as pd

# ============================================================
# OPENSTREETMAP / OVERPASS
# U.S. HEALTHCARE ACCESSIBILITY DATA
# ============================================================

COORDINATE_FILE = (
    "data/api_fusion/dynamic/"
    "us_state_capital_coordinates.csv"
)

OUTPUT_FILE = (
    "data/api_fusion/dynamic/"
    "overpass_us_healthcare.csv"
)

OVERPASS_URL = "https://overpass.private.coffee/api/interpreter"

# Search radius around each state capital.
# 50 km gives useful coverage while keeping requests small.
RADIUS_METERS = 10000


# ============================================================
# BUILD OVERPASS QUERY
# ============================================================

def build_query(latitude, longitude):

    # ========================================================
    # LIGHTWEIGHT U.S. HEALTHCARE QUERY
    # ========================================================
    #
    # We use a 10 km radius around each U.S. state capital.
    # This is deliberately smaller than the previous 50 km
    # query to reduce server load and response time.
    #
    # ========================================================

    radius = 10000

    return f"""
    [out:json][timeout:60];

    (
      nwr["amenity"="hospital"]
        (around:{radius},{latitude},{longitude});

      nwr["amenity"="clinic"]
        (around:{radius},{latitude},{longitude});

      nwr["amenity"="doctors"]
        (around:{radius},{latitude},{longitude});

      nwr["amenity"="pharmacy"]
        (around:{radius},{latitude},{longitude});

      nwr["healthcare"="hospital"]
        (around:{radius},{latitude},{longitude});

      nwr["healthcare"="clinic"]
        (around:{radius},{latitude},{longitude});

      nwr["healthcare"="doctor"]
        (around:{radius},{latitude},{longitude});

      nwr["healthcare"="pharmacy"]
        (around:{radius},{latitude},{longitude});
    );

    out center tags;
    """

# ============================================================
# CLASSIFY OSM ELEMENT
# ============================================================

def classify_element(element):

    tags = element.get("tags", {})

    amenity = tags.get("amenity", "").lower()

    healthcare = tags.get(
        "healthcare",
        ""
    ).lower()

    speciality = tags.get(
        "healthcare:speciality",
        ""
    ).lower()

    # --------------------------------------------------------
    # Hospital
    # --------------------------------------------------------

    if (
        amenity == "hospital"
        or healthcare == "hospital"
    ):
        return "hospital"

    # --------------------------------------------------------
    # Pharmacy
    # --------------------------------------------------------

    if (
        amenity == "pharmacy"
        or healthcare == "pharmacy"
    ):
        return "pharmacy"

    # --------------------------------------------------------
    # Gynecologist
    # --------------------------------------------------------

    gynecology_terms = [
        "gynaecology",
        "gynecology",
        "obstetrics",
        "obstetric",
        "gynecologist",
        "gynaecologist"
    ]

    if any(
        term in speciality
        for term in gynecology_terms
    ):
        return "gynecologist"

    # Also check common doctor specialities

    doctor_speciality = tags.get(
        "speciality",
        ""
    ).lower()

    if any(
        term in doctor_speciality
        for term in gynecology_terms
    ):
        return "gynecologist"

    # --------------------------------------------------------
    # Clinic
    # --------------------------------------------------------

    if (
        amenity == "clinic"
        or healthcare == "clinic"
    ):
        return "clinic"

    # --------------------------------------------------------
    # Doctor
    # --------------------------------------------------------

    if (
        amenity == "doctors"
        or healthcare == "doctor"
    ):
        return "doctor"

    return None



# ============================================================
# QUERY ONE LOCATION
# ============================================================

def query_location(
    state,
    capital,
    latitude,
    longitude
):

    query = build_query(
        latitude,
        longitude
    )

    headers = {
        "User-Agent": (
            "FemCare-MenstrualHealth-Research/1.0 "
            "(academic research project)"
        ),
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:

        response = requests.post(
            OVERPASS_URL,
            data={
                "data": query
            },
            headers=headers,
            timeout=180
        )

        print(
            "HTTP status:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

        elements = data.get(
            "elements",
            []
        )

        counts = {
            "hospitals": 0,
            "clinics": 0,
            "doctors": 0,
            "gynecologists": 0,
            "pharmacies": 0
        }

        unique_elements = set()

        for element in elements:

            element_type = element.get(
                "type"
            )

            element_id = element.get(
                "id"
            )

            unique_id = (
                element_type,
                element_id
            )

            if unique_id in unique_elements:
                continue

            unique_elements.add(
                unique_id
            )

            category = classify_element(
                element
            )

            if category == "hospital":
                counts["hospitals"] += 1

            elif category == "clinic":
                counts["clinics"] += 1

            elif category == "doctor":
                counts["doctors"] += 1

            elif category == "gynecologist":
                counts["gynecologists"] += 1

            elif category == "pharmacy":
                counts["pharmacies"] += 1

        counts["healthcare_facilities"] = (
            counts["hospitals"]
            + counts["clinics"]
            + counts["doctors"]
            + counts["gynecologists"]
            + counts["pharmacies"]
        )

        return counts

    except requests.exceptions.RequestException as e:

        print(
            f"Overpass request failed for "
            f"{state}: {e}"
        )

        return {
            "hospitals": None,
            "clinics": None,
            "doctors": None,
            "gynecologists": None,
            "pharmacies": None,
            "healthcare_facilities": None
        }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("OPENSTREETMAP / OVERPASS")
    print("U.S. HEALTHCARE ACCESSIBILITY")
    print("=" * 70)

    # --------------------------------------------------------
    # Load verified coordinates
    # --------------------------------------------------------

    locations = pd.read_csv(
        COORDINATE_FILE
    )

    print(
        "\nLocations loaded:",
        len(locations)
    )

    # --------------------------------------------------------
    # Safety check:
    # ONLY United States
    # --------------------------------------------------------

    locations = locations[
        locations["country"]
        .astype(str)
        .str.lower()
        .eq("united states")
    ].copy()

    locations = locations.head(1)

    print(
        "Verified U.S. locations:",
        len(locations)
    )

    # --------------------------------------------------------
    # Process each state
    # --------------------------------------------------------

    results = []

    for index, row in locations.iterrows():

        state = row["state"]
        capital = row["capital"]
        latitude = row["latitude"]
        longitude = row["longitude"]

        print(
            f"\n[{len(results) + 1}/"
            f"{len(locations)}] "
            f"{state} -> {capital}"
        )

        print(
            f"Coordinates: "
            f"{latitude}, {longitude}"
        )

        counts = query_location(
            state,
            capital,
            latitude,
            longitude
        )

        result = {

            "state": state,

            "capital": capital,

            "latitude": latitude,

            "longitude": longitude,

            "search_radius_km":
                RADIUS_METERS / 1000,

            **counts
        }

        results.append(result)

        print(
            "Hospitals:",
            counts["hospitals"]
        )

        print(
            "Clinics:",
            counts["clinics"]
        )

        print(
            "Doctors:",
            counts["doctors"]
        )

        print(
            "Gynecologists:",
            counts["gynecologists"]
        )

        print(
            "Pharmacies:",
            counts["pharmacies"]
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Don't hammer the public Overpass server.
        # ----------------------------------------------------

        time.sleep(8)

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    result_df = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "OVERPASS U.S. HEALTHCARE DATA COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "\nRows:",
        len(result_df)
    )

    print(
        "Columns:",
        len(result_df.columns)
    )

    print(
        "\nColumns:"
    )

    for column in result_df.columns:

        print("-", column)

    print(
        "\nMissing values:"
    )

    print(
        result_df.isna().sum()
    )

    print(
        "\nFirst 10 records:"
    )

    print(
        result_df.head(10)
        .to_string(index=False)
    )

    print(
        "\nSaved to:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()
