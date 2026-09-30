from analytics.eda import (
    load_data,
    get_dataset_overview,
    get_missing_summary,
    get_weather_correlation,
    get_pain_correlations,
    get_fusion_feature_groups
)


print("=" * 70)
print("TESTING FEMCARE EDA MODULE")
print("=" * 70)


df = load_data()

print("\nDataset:")
print(df.shape)


print("\nOverview:")
print(
    get_dataset_overview(df)
)


print("\nMissing values:")
print(
    get_missing_summary(df)
)


print("\nWeather correlations:")
print(
    get_weather_correlation(df)
)


print("\nPain correlations:")
print(
    get_pain_correlations(df)
)


print("\nFusion groups:")

groups = get_fusion_feature_groups(df)

for group, columns in groups.items():

    print(
        f"{group}: {len(columns)} features"
    )


print("\nEDA MODULE TEST COMPLETE")