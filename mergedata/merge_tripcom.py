import pandas as pd

all_df = pd.read_csv("mergedata/merged_all_with_tripadvisor.csv")
trip = pd.read_csv("mergedata/datatrip.csv")

# Chuẩn hóa tên cột Trip.com
trip = trip.rename(columns={
    "hotelName": "Hotel Name",
    "cityName": "Search Location",
    "star": "Stars_Clean",
    "address": "Address",
    "positionDesc": "Location_Clean",
    "commentScore": "Rating_Clean",
    "commenterNumber": "Review Count",
    "amenities": "Facilities_cleaned",
    "minPrice": "Final Price",
    "maxPrice": "Original Price",
    "roomNames": "Room Type",
    "checkInDates": "Check-in"
})

trip["Scenario"] = "Tripcom"
trip["Hotel Link"] = ""
trip["Distance_KM"] = ""

# Giữ TOÀN BỘ cột Trip.com
final_df = pd.concat([all_df, trip], ignore_index=True, sort=False)

final_df.to_csv("merged_all_with_tripadvisor_tripcom.csv", index=False, encoding="utf-8-sig")

print("Merge Trip.com hoàn tất!")
print("Tổng số dòng:", len(final_df))
print("Số cột:", len(final_df.columns))
