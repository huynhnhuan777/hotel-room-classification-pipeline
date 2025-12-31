import pandas as pd
from sqlalchemy import create_engine

# Cấu hình DB
engine = create_engine("postgresql+psycopg2://postgres:123456@localhost:5432/booking_data")

# Check dữ liệu trực tiếp từ bảng room_details_cleaned
print("--- KIỂM TRA DỮ LIỆU TRONG DB ---")
check_df = pd.read_sql("SELECT hotel_id, area_m2_cleaned FROM room_details_cleaned LIMIT 5", engine)
print(check_df)