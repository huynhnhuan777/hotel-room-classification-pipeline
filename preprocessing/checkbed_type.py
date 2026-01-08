import pandas as pd

df = pd.read_csv("preprocessing/cleaned_rooms.csv")
print(df["bed_class"].dropna().unique())
