
import pandas as pd

df = pd.read_csv("data/course-catalog.csv")

print("Total rows:", len(df))
print("\nAll column names:")

for i, column in enumerate(df.columns):
    print(i, ":", column)

print("\nFirst 5 complete records:")
print(df.head().to_string(index=False))

print("\nPossible course-related columns:")
for column in df.columns:
    if any(word in column.lower() for word in
           ["subject", "course", "title", "description",
            "credit", "catalog", "prerequisite"]):
        print("-", column)
