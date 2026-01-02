import pandas as pd
import re

all_df = pd.read_csv("merged_all_data.csv")

trip = pd.read_csv('./crawl/data_raw/hotels_detail_output_clean.csv')
# Chuẩn hoá giá 
def split_price(p):
    if pd.isna(p):
        return None, None
    nums = re.findall(r"\d+", str(p).replace(".", ""))
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    if len(nums) == 1:
        return float(nums[0]), None
    return None, None

trip[["Final Price","Original Price"]] = trip["priceRange"].apply(
    lambda x: pd.Series(split_price(x))
)

#  Lấy schema chuẩn 
schema_cols = list(all_df.columns)

rows = []

#  Chuyển Tripadvisor sang schema Booking 
for _, row in trip.iterrows():
    r = {col: '' for col in schema_cols}

    r["Hotel Name"] = row.get("hotel_name","")
    r["Hotel Link"] = row.get("hotel_url","")
    r["Address"] = row.get("address","")
    r["Rating_Clean"] = row.get("ratingValue","")
    r["Review Count"] = row.get("reviewCount","")
    r["Facilities_cleaned"] = row.get("amenities","")
    r["Room Type"] = row.get("room_types","")
    r["Final Price"] = row.get("Final Price","")
    r["Original Price"] = row.get("Original Price","")
    r["Search Location"] = "Ho Chi Minh"
    r["Scenario"] = "Tripadvisor"

    rows.append(r)

trip_std = pd.DataFrame(rows, columns=schema_cols)

# Append thêm hàng 
final_df = pd.concat([all_df, trip_std], ignore_index=True)

#Lưu file 
final_df.to_csv("merged_all_with_tripadvisor.csv", index=False, encoding="utf-8-sig")

print("Đã merge thêm Tripadvisor!")
print("Tổng dòng mới:", len(final_df))
print("Số dòng Tripadvisor thêm:", len(trip_std))
