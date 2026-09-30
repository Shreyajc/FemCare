import requests
import time

# FEMCARE - LIVE U.S. HEALTHCARE SEARCH
# OpenStreetMap / Nominatim / Overpass

GEOCODING_URL = "https://nominatim.openstreetmap.org/search"

# If one public Overpass instance is slow/down, automatically try another.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

USER_AGENT = (
    "FemCare-MenstrualHealth-Research/1.0 "
    "(academic project)"
)


# 1. GEOCODE U.S. LOCATION\

def geocode_us_location(city, state):

    query = f"{city}, {state}, United States"

    params = {
        "q": query,
        "format": "json",
        "limit": 5,
        "countrycodes": "us",
        "addressdetails": 1,
    }

    headers = {
        "User-Agent": USER_AGENT,
    }

    try:
        response = requests.get(
            GEOCODING_URL,
            params=params,
            headers=headers,
            timeout=15,
        )

        response.raise_for_status()

        results = response.json()

        if not results:
            return None

        for result in results:

            address = result.get("address", {})

            country_code = (
                address.get("country_code", "").lower()
            )

            if country_code == "us":

                return {
                    "latitude": float(result["lat"]),
                    "longitude": float(result["lon"]),
                    "display_name": result.get(
                        "display_name",
                        query,
                    ),
                }

        return None

    except requests.exceptions.RequestException as error:

        print("Geocoding error:", error)

        return None


# 2. BUILD HEALTHCARE QUERY

def build_healthcare_query(
    latitude,
    longitude,
    radius_meters,
):

    return f"""
[out:json][timeout:25];

(
    /* General healthcare facilities */

    nwr["amenity"~"hospital|clinic|doctors|pharmacy",i]
        (around:{radius_meters},{latitude},{longitude});

    nwr["healthcare"~"hospital|clinic|doctor|pharmacy|specialist",i]
        (around:{radius_meters},{latitude},{longitude});


    /* Gynecology / Obstetrics */

    nwr["healthcare:speciality"~"gynaecology|gynecology|obstetrics|obstetric",i]
        (around:{radius_meters},{latitude},{longitude});

    nwr["healthcare:specialty"~"gynaecology|gynecology|obstetrics|obstetric",i]
        (around:{radius_meters},{latitude},{longitude});

    nwr["speciality"~"gynaecology|gynecology|obstetrics|obstetric",i]
        (around:{radius_meters},{latitude},{longitude});
);

out center tags;
"""
# 3. CLASSIFY FACILITY

def classify_facility(element):

    tags = element.get("tags", {})

    amenity = tags.get(
        "amenity",
        ""
    ).lower()

    healthcare = tags.get(
        "healthcare",
        ""
    ).lower()

    speciality = (
        tags.get("healthcare:speciality", "")
        or tags.get("healthcare:specialty", "")
        or tags.get("speciality", "")
    ).lower()

    searchable_text = " ".join([
        tags.get("name", ""),
        tags.get("healthcare:speciality", ""),
        tags.get("healthcare:specialty", ""),
        tags.get("speciality", ""),
        tags.get("description", ""),
    ]).lower()

    # --------------------------------------------------------
    # GYNECOLOGY / OBSTETRICS
    # --------------------------------------------------------

    gynecology_terms = [
        "gynecology",
        "gynaecology",
        "gynecologist",
        "gynaecologist",
        "ob-gyn",
        "obgyn",
        "ob gyn",
        "obstetrics",
        "obstetric",
    ]

    if any(
        term in speciality
        for term in gynecology_terms
    ):
        return "Gynecologist / OB-GYN"

    if any(
        term in searchable_text
        for term in gynecology_terms
    ):
        return "Gynecologist / OB-GYN"

    # --------------------------------------------------------
    # GENERAL FACILITY TYPES
    # --------------------------------------------------------

    if (
        amenity == "hospital"
        or healthcare == "hospital"
    ):
        return "Hospital"

    if (
        amenity == "pharmacy"
        or healthcare == "pharmacy"
    ):
        return "Pharmacy"

    if (
        amenity == "clinic"
        or healthcare == "clinic"
    ):
        return "Clinic"

    if (
        amenity == "doctors"
        or healthcare == "doctor"
    ):
        return "Doctor"

    if healthcare == "specialist":
        return "Specialist"

    return "Healthcare Facility"

# 4. EXTRACT COORDINATES

def get_element_coordinates(element):

    if (
        element.get("lat") is not None
        and element.get("lon") is not None
    ):
        return (
            element["lat"],
            element["lon"],
        )

    center = element.get("center")

    if center:
        return (
            center.get("lat"),
            center.get("lon"),
        )

    return None, None


# 5. QUERY OVERPASS WITH AUTOMATIC FALLBACK

def query_overpass(query):

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    for index, url in enumerate(OVERPASS_URLS, start=1):

        print(
            f"Trying Overpass server "
            f"{index}/{len(OVERPASS_URLS)}:"
        )
        print(url)

        try:

            response = requests.post(
                url,
                data={"data": query},
                headers=headers,
                timeout=(10, 35),
            )

            print(
                "HTTP status:",
                response.status_code,
            )

            response.raise_for_status()

            data = response.json()

            print("Overpass server succeeded.")

            return data

        except (
            requests.exceptions.RequestException,
            ValueError,
        ) as error:

            print(
                "Server failed:",
                error,
            )

            # Small pause before switching mirrors
            if index < len(OVERPASS_URLS):
                print("Trying next Overpass server...")
                time.sleep(1)

    print("All Overpass servers failed.")

    return None


# 6. SEARCH HEALTHCARE

def find_healthcare(
    city,
    state,
    radius_km=12,
):

    print("=" * 70)
    print("FEMCARE HEALTHCARE FINDER")
    print("=" * 70)

    print(
        f"\nSearching: {city}, {state}, USA"
    )

    print(
        f"Radius: {radius_km} km"
    )

    # --------------------------------------------------------
    # GEOCODE
    # --------------------------------------------------------

    location = geocode_us_location(
        city,
        state,
    )

    if location is None:

        print(
            "\nCould not verify the U.S. location."
        )

        return {
            "success": False,
            "error": "location",
            "facilities": [],
        }

    latitude = location["latitude"]
    longitude = location["longitude"]

    print("\nVerified location:")
    print(location["display_name"])

    print(
        f"Coordinates: "
        f"{latitude}, {longitude}"
    )

    # --------------------------------------------------------
    # BUILD QUERY
    # --------------------------------------------------------

    radius_meters = int(radius_km * 1000)

    query = build_healthcare_query(
        latitude,
        longitude,
        radius_meters,
    )

    # --------------------------------------------------------
    # QUERY OVERPASS
    # --------------------------------------------------------

    print("\nQuerying OpenStreetMap...")

    data = query_overpass(query)

    if data is None:

        return {
            "success": False,
            "error": "overpass",
            "facilities": [],
        }

    elements = data.get(
        "elements",
        [],
    )

    print(
        "OSM elements received:",
        len(elements),
    )

    facilities = []
    seen = set()

    # --------------------------------------------------------
    # PROCESS RESULTS
    # --------------------------------------------------------

    for element in elements:

        unique_id = (
            element.get("type"),
            element.get("id"),
        )

        if unique_id in seen:
            continue

        seen.add(unique_id)

        tags = element.get(
            "tags",
            {},
        )

        category = classify_facility(
            element
        )

        latitude_facility, longitude_facility = (
            get_element_coordinates(element)
        )

        name = tags.get(
            "name",
            "Unnamed facility",
        )

        address_parts = []

        for key in [
            "addr:housenumber",
            "addr:street",
            "addr:city",
            "addr:state",
        ]:

            value = tags.get(key)

            if value:
                address_parts.append(value)

        address = ", ".join(
            address_parts
        )

        # Support common OSM contact tags
        phone = (
            tags.get("phone")
            or tags.get("contact:phone")
            or ""
        )

        website = (
            tags.get("website")
            or tags.get("contact:website")
            or ""
        )

        facilities.append({
            "name": name,
            "type": category,
            "latitude": latitude_facility,
            "longitude": longitude_facility,
            "address": address,
            "phone": phone,
            "website": website,
        })

    # Put named facilities before unnamed facilities
    facilities.sort(
        key=lambda item: (
            item["name"] == "Unnamed facility",
            item["type"],
            item["name"],
        )
    )

    print(
        "\nFacilities found:",
        len(facilities),
    )

    return {
        "success": True,
        "error": None,
        "facilities": facilities,
    }


# 7. OPTIONAL TERMINAL TEST

def main():

    result = find_healthcare(
        city="Los Angeles",
        state="California",
    )

    if not result["success"]:

        print(
            "\nHealthcare search failed:",
            result["error"],
        )

        return

    facilities = result["facilities"]

    print("\n" + "=" * 70)
    print("HEALTHCARE SEARCH RESULTS")
    print("=" * 70)

    for index, facility in enumerate(
        facilities[:20],
        start=1,
    ):

        print(
            f"\n{index}. {facility['name']}"
        )

        print(
            f"   Type: {facility['type']}"
        )

        print(
            f"   Address: "
            f"{facility['address']}"
        )


if __name__ == "__main__":
    main()