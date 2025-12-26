import pandas as pd
import re

INPUT_FILE = "hotels_detail_output.csv"
OUTPUT_FILE = "hotels_detail_output_clean.csv"

df = pd.read_csv(INPUT_FILE)


def is_hcm(address):
    if pd.isna(address):
        return False

    addr = address.lower()

    keywords = [
        "hồ chí minh",
        "ho chi minh",
        "tp. hồ chí minh",
        "thành phố hồ chí minh",
        "district",
        "quận 1",
        "quận 2",
        "quận 3",
        "quận 4",
        "quận 5",
        "quận 6",
        "quận 7",
        "quận 8",
        "quận 9",
        "quận 10",
        "quận 11",
        "quận 12",
        "bình thạnh",
        "phú nhuận",
        "tân bình",
        "tân phú",
        "gò vấp",
        "thủ đức"
    ]

    return any(k in addr for k in keywords)

# Giữ lại đúng khách sạn ở HCM
df_hcm = df[df["address"].apply(is_hcm)]

print(f" Đã loại bỏ: {len(df) - len(df_hcm)} khách sạn ngoài HCM")
print(f" Còn lại: {len(df_hcm)} khách sạn HCM")

# Xóa trùng theo URL
df_hcm = df_hcm.drop_duplicates(subset=["detail_url"])

# Sắp xếp lại theo rating
df_hcm = df_hcm.sort_values(by="ratingValue", ascending=False)

df_hcm.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("Đã tạo file sạch:", OUTPUT_FILE)
