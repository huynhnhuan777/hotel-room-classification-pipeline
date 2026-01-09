import pandas as pd

# Load the datasets
df_rooms = pd.read_csv("merged_hotels.csv")
df_hotels = pd.read_csv("merged_rooms.csv")

# Merge the dataframes on 'hotel_id'
merged_df = pd.merge(df_rooms, df_hotels, on='hotel_id', how='left')

# Save to a new file
output_filename = "merged_hotel_rooms.csv"
merged_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

# Display the result
print(merged_df.head())