
import pandas as pd
import matplotlib.pyplot as plt
import re
# Đọc dữ liệu đã làm sạch
df = pd.read_csv("hotels_detail_output_clean.csv")

# Làm sạch giá phòng
def extract_price(price):
    try:
        nums = re.findall(r"\d+", str(price).replace(".", ""))
        if nums:
            return int(nums[0])
    except:
        return None
    return None

df["price_num"] = df["priceRange"].apply(extract_price)

# Ép kiểu dữ liệu từ string sang số nguyên
df["ratingValue"] = pd.to_numeric(df["ratingValue"], errors="coerce")
df["reviewCount"] = pd.to_numeric(df["reviewCount"], errors="coerce")

# Chuẩn hóa hạng phòng
def classify_room(room):
    if pd.isna(room):
        return "Unknown"
    r = room.lower()
    if "family" in r or "gia đình" in r:
        return "Family"
    if "suite" in r or "premium" in r or "executive" in r:
        return "Premium"
    if "deluxe" in r:
        return "Deluxe"
    return "Standard"

df["room_class"] = df["room_types"].apply(classify_room)

# Phân bố hạng phòng
class_count = df["room_class"].value_counts()

plt.figure()
plt.bar(class_count.index, class_count.values)
plt.title("Phân bố hạng phòng khách sạn TP.HCM")
plt.xlabel("Hạng phòng")
plt.ylabel("Số lượng")
plt.show()

# Giá trung bình theo hạng
avg_price = df.groupby("room_class")["price_num"].mean()

plt.figure()
plt.plot(avg_price.index, avg_price.values, marker="o")
plt.title("Giá trung bình theo hạng phòng")
plt.xlabel("Hạng phòng")
plt.ylabel("Giá trung bình (VND)")
plt.show()

# Rating theo hạng
avg_rating = df.groupby("room_class")["ratingValue"].mean()

plt.figure()
plt.bar(avg_rating.index, avg_rating.values)
plt.title("Rating trung bình theo hạng phòng")
plt.xlabel("Hạng phòng")
plt.ylabel("Rating")
plt.show()


# Giá vs Review
plt.figure()
for c in df["room_class"].unique():
    sub = df[df["room_class"] == c]
    plt.scatter(sub["price_num"], sub["reviewCount"], label=c)

plt.xlabel("Giá phòng")
plt.ylabel("Số lượt đánh giá")
plt.title("Giá vs Review theo hạng phòng")
plt.legend()
plt.show()


# Tiện nghi trung bình
df["amenity_count"] = df["amenities"].fillna("").apply(lambda x: len(str(x).split(",")))
amenity_avg = df.groupby("room_class")["amenity_count"].mean()

plt.figure()
plt.bar(amenity_avg.index, amenity_avg.values)
plt.title("Số tiện nghi trung bình theo hạng phòng")
plt.xlabel("Hạng phòng")
plt.ylabel("Số tiện nghi")
plt.show()
