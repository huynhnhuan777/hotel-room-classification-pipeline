import pandas as pd
import numpy as np
import os
import re

# =====================================================
# CONFIG
# =====================================================
BASE_DIR = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline"
RAW_DIR = os.path.join(BASE_DIR, "integration", "raw")
OUT_DIR = os.path.join(BASE_DIR, "integration", "unified")

os.makedirs(OUT_DIR, exist_ok=True)

# =====================================================
# UTILS
# =====================================================
def clean_price(x):
    if pd.isna(x):
        return None
    x = re.sub(r"[^\d]", "", str(x))
    return int(x) if x else None

def clean_area(x):
    if pd.isna(x):
        return None
    m = re.search(r"(\d+)", str(x))
    return int(m.group(1)) if m else None

def yes_no(x):
    if pd.isna(x):
        return None
    return 1 if "có" in str(x).lower() else 0

# =====================================================
# HOANGVU
# =====================================================
df_hoangvu = pd.read_csv(os.path.join(RAW_DIR, "hoangvu_hotels.csv"))

hoangvu = pd.DataFrame({
    "source": "hoangvu",
    "hotel_id": None,
    "hotel_name": df_hoangvu["Hotel Name"],
    "hotel_url": df_hoangvu["Hotel Link"],
    "city": df_hoangvu["Search Location"],
    "address": df_hoangvu["Address"],
    "latitude": None,
    "longitude": None,
    "stars": df_hoangvu["Stars_Clean"],
    "rating": df_hoangvu["Rating_Clean"],
    "review_count": df_hoangvu["Review Count"],
    "room_name": df_hoangvu["Room Type"],
    "room_class": df_hoangvu["Room_Class"],
    "bed_type": df_hoangvu["Bed Type"],
    "area_m2": df_hoangvu["Area_m2_cleaned"].apply(clean_area),
    "max_occupancy": df_hoangvu["Total_Guests"],
    "price_original": df_hoangvu["Original Price"],
    "price_final": df_hoangvu["Final Price"],
    "discount_pct": df_hoangvu["Discount %"],
    "free_cancel": df_hoangvu["Free_Cancel_Bool"],
    "breakfast": df_hoangvu["Breakfast_Bool"],
    "amenities": df_hoangvu["Facilities_cleaned"],
    "checkin_date": df_hoangvu["Check-in"],
    "checkout_date": None
})

# =====================================================
# VANDUY
# =====================================================
df_vanduy = pd.read_excel(os.path.join(RAW_DIR, "vanduy_hotels.xlsx"))

vanduy = pd.DataFrame({
    "source": "vanduy",
    "hotel_id": df_vanduy["hotelId"],
    "hotel_name": df_vanduy["hotelName"],
    "hotel_url": df_vanduy["imageUrl"],
    "city": df_vanduy["cityName"],
    "address": df_vanduy["address"],
    "latitude": df_vanduy["latitude"],
    "longitude": df_vanduy["longitude"],
    "stars": df_vanduy["star"],
    "rating": df_vanduy["commentScore"],
    "review_count": df_vanduy["commenterNumber"],
    "room_name": df_vanduy["roomNames"],
    "room_class": None,
    "bed_type": None,
    "area_m2": None,
    "max_occupancy": None,
    "price_original": df_vanduy["maxPrice"],
    "price_final": df_vanduy["minPrice"],
    "discount_pct": None,
    "free_cancel": None,
    "breakfast": None,
    "amenities": None,
    "checkin_date": df_vanduy["checkInDates"],
    "checkout_date": df_vanduy["checkOutDates"]
})

# =====================================================
# HONGNHUAN (HOTEL + ROOM)
# =====================================================
df_hotel = pd.read_csv(os.path.join(RAW_DIR, "hongnhuan_hotels.csv"))
df_room = pd.read_csv(os.path.join(RAW_DIR, "hongnhuan_rooms.csv"))

hn = df_room.merge(df_hotel, on="hotel_id", how="left")

hongnhuan = pd.DataFrame({
    "source": "hongnhuan",
    "hotel_id": hn["hotel_id"],
    "hotel_name": hn["hotel_name"],
    "hotel_url": hn["hotel_link"],
    "city": hn["city"],
    "address": None,
    "latitude": None,
    "longitude": None,
    "stars": None,
    "rating": None,
    "review_count": None,
    "room_name": hn["room_name"],
    "room_class": None,
    "bed_type": hn["bed_type"],
    "area_m2": hn["area_m2"].apply(clean_area),
    "max_occupancy": hn["max_occupancy"],
    "price_original": hn["price"],
    "price_final": hn["price"],
    "discount_pct": 0,
    "free_cancel": None,
    "breakfast": None,
    "amenities": hn["amenities"],
    "checkin_date": None,
    "checkout_date": None
})

# =====================================================
# TRONGVU
# =====================================================
df_trongvu = pd.read_csv(os.path.join(RAW_DIR, "trongvu_hotels.csv"))

trongvu = pd.DataFrame({
    "source": "trongvu",
    "hotel_id": None,
    "hotel_name": df_trongvu["hotel_name"],
    "hotel_url": df_trongvu["hotel_url"],
    "city": None,
    "address": df_trongvu["address"],
    "latitude": None,
    "longitude": None,
    "stars": None,
    "rating": df_trongvu["ratingValue"],
    "review_count": df_trongvu["reviewCount"],
    "room_name": df_trongvu["room_types"],
    "room_class": None,
    "bed_type": None,
    "area_m2": None,
    "max_occupancy": None,
    "price_original": df_trongvu["priceRange"],
    "price_final": df_trongvu["priceRange"],
    "discount_pct": None,
    "free_cancel": None,
    "breakfast": None,
    "amenities": df_trongvu["amenities"],
    "checkin_date": None,
    "checkout_date": None
})

# =====================================================
# VANSÂU (FIXED ERROR HERE)
# =====================================================
def load_vansau(hotel_file, room_file):
    h = pd.read_excel(os.path.join(RAW_DIR, hotel_file))
    r = pd.read_excel(os.path.join(RAW_DIR, room_file))

    df = r.merge(h, left_on="hotel_link", right_on="link", how="left")

    return pd.DataFrame({
        "source": "vansau",
        "hotel_id": None,
        "hotel_name": df["hotel_name"],
        "hotel_url": df["hotel_link"],
        "city": None,
        "address": df["dia_chi"],
        "latitude": None,
        "longitude": None,
        "stars": None,
        "rating": df["diem_danh_gia"],
        "review_count": df["so_luong_danh_gia"],
        "room_name": df["room_name"],
        "room_class": None,
        "bed_type": df["bed"],
        "area_m2": df["area"].apply(clean_area),

        # 🔥 FIX LỖI ValueError: 2
        "max_occupancy": df["people"].str.extract(r"(\d+)", expand=False),

        "price_original": df["list_price"].apply(clean_price),
        "price_final": df["final_price"].apply(clean_price),
        "discount_pct": df["discount_pct"],
        "free_cancel": df["cancel_policy"].apply(yes_no),
        "breakfast": df["breakfast"].apply(yes_no),
        "amenities": df["room_amenities"],
        "checkin_date": None,
        "checkout_date": None
    })

vansau_1 = load_vansau("vansau_hotels_1.xlsx", "vansau_rooms_1.xlsx")
vansau_2 = load_vansau("vansau_hotels_2.xlsx", "vansau_rooms_2.xlsx")

# =====================================================
# CONCAT & SAVE
# =====================================================
final_df = pd.concat(
    [hoangvu, vanduy, hongnhuan, trongvu, vansau_1, vansau_2],
    ignore_index=True
)

out_path = os.path.join(OUT_DIR, "unified_hotels_rooms.csv")
final_df.to_csv(out_path, index=False, encoding="utf-8-sig")

print("✅ TRANSFORM SUCCESS")
print("Saved to:", out_path)
print("Shape:", final_df.shape)
print(final_df.info())
