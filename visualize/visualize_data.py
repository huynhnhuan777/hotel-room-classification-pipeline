import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import font_manager
import warnings
import unicodedata
import re
import sys
import os
warnings.filterwarnings('ignore')

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 12

# Create output directory
output_dir = 'visualizations'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Tao thu muc: {output_dir}")

# Load data
print("Dang tai du lieu...")
df = pd.read_csv('merged_all_data.csv')
def normalize_location(text):
    if pd.isna(text):
        return text
    # chuyển về string
    text = str(text)
    # lowercase
    text = text.lower()
    # bỏ dấu tiếng Việt
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    # thay - , _ bằng space
    text = re.sub(r'[-_]', ' ', text)
    # bỏ ký tự đặc biệt
    text = re.sub(r'[^a-z\s]', '', text)
    # bỏ space dư
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['Search_Location_Clean'] = df['Search Location'].apply(normalize_location)

# Clean data
df['Final Price'] = pd.to_numeric(df['Final Price'], errors='coerce')
df['Original Price'] = pd.to_numeric(df['Original Price'], errors='coerce')
df['Rating_Clean'] = pd.to_numeric(df['Rating_Clean'], errors='coerce')
df['Stars_Clean'] = pd.to_numeric(df['Stars_Clean'], errors='coerce')
df['Review Count'] = pd.to_numeric(df['Review Count'], errors='coerce')
df['Distance_KM'] = pd.to_numeric(df['Distance_KM'], errors='coerce')
df['Area_m2_cleaned'] = pd.to_numeric(df['Area_m2_cleaned'], errors='coerce')
df['Total_Guests_Clean'] = (df['Total_Guests'].astype(str).str.extract(r'(\d+)').astype(float))

# Remove outliers for price (keep prices between 0 and 100 million)
df = df[(df['Final Price'] > 0) & (df['Final Price'] < 100000000)]

print(f"Tong so dong du lieu: {len(df)}")
print(f"So khach san duy nhat: {df['Hotel Name'].nunique()}")

# Function to save individual plot
def save_plot(fig, filename, title):
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    filepath = os.path.join(output_dir, filename)
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  -> Da luu: {filename}")

location_map = {
    'ho chi minh': 'Ho Chi Minh',
    'hcm': 'Ho Chi Minh',
    'ho chi minh city': 'Ho Chi Minh',
    'binh duong': 'Binh Duong',
    'vung tau': 'Vung Tau'
}

df['Search_Location_Clean'] = df['Search_Location_Clean'].replace(location_map)


# 1. Phân bố giá (Final Price)
print("\n1. Tao bieu do phan bo gia...")
fig, ax = plt.subplots(figsize=(10, 6))
price_data = df['Final Price'].dropna() / 1000000  # Convert to millions
ax.hist(price_data, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
ax.set_xlabel('Giá (triệu VNĐ)', fontsize=12)
ax.set_ylabel('Số lượng', fontsize=12)
ax.set_title('Phân bố Giá Phòng', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
save_plot(fig, '01_phan_bo_gia.png', 'Phân bố Giá Phòng')

# 2. Phân bố đánh giá (Rating)
print("2. Tao bieu do phan bo danh gia...")
fig, ax = plt.subplots(figsize=(10, 6))
rating_data = df['Rating_Clean'].dropna()
ax.hist(rating_data, bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
ax.set_xlabel('Điểm đánh giá', fontsize=12)
ax.set_ylabel('Số lượng', fontsize=12)
ax.set_title('Phân bố Điểm Đánh giá Khách sạn', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
save_plot(fig, '02_phan_bo_danh_gia.png', 'Phân bố Điểm Đánh giá Khách sạn')

# 3. Phân bố số sao
print("3. Tao bieu do phan bo hang sao...")
fig, ax = plt.subplots(figsize=(10, 6))
stars_data = df['Stars_Clean'].dropna()
stars_counts = stars_data.value_counts().sort_index()
ax.bar(stars_counts.index, stars_counts.values, color='gold', edgecolor='black', alpha=0.7)
ax.set_xlabel('Số sao', fontsize=12)
ax.set_ylabel('Số lượng', fontsize=12)
ax.set_title('Phân bố Hạng Sao Khách sạn', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
save_plot(fig, '03_phan_bo_hang_sao.png', 'Phân bố Hạng Sao Khách sạn')

# 4. Phân bố theo địa điểm (Search Location)
print("4. Tao bieu do top dia diem...")
fig, ax = plt.subplots(figsize=(10, 6))
location_counts = df['Search_Location_Clean'].value_counts().head(10)
ax.barh(range(len(location_counts)), location_counts.values, color='coral', edgecolor='black', alpha=0.7)
ax.set_yticks(range(len(location_counts)))
ax.set_yticklabels(location_counts.index, fontsize=10)
ax.set_xlabel('Số lượng', fontsize=12)
ax.set_title('Top 10 Địa điểm Tìm kiếm', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
save_plot(fig, '04_top_10_dia_diem.png', 'Top 10 Địa điểm Tìm kiếm')

# 5. Phân bố theo Quận (District) - Top 10
print("5. Tao bieu do top quan huyen...")
fig, ax = plt.subplots(figsize=(10, 6))
district_counts = df['District'].value_counts().head(10)
ax.barh(range(len(district_counts)), district_counts.values, color='mediumpurple', edgecolor='black', alpha=0.7)
ax.set_yticks(range(len(district_counts)))
ax.set_yticklabels(district_counts.index, fontsize=10)
ax.set_xlabel('Số lượng', fontsize=12)
ax.set_title('Top 10 Quận/Huyện', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
save_plot(fig, '05_top_10_quan_huyen.png', 'Top 10 Quận/Huyện')

# 6. Phân bố loại phòng (Room Type)
print("6. Tao bieu do loai phong...")
fig, ax = plt.subplots(figsize=(10, 6))
room_type_counts = df['Room Type'].value_counts().head(10)
ax.barh(range(len(room_type_counts)), room_type_counts.values, color='lightblue', edgecolor='black', alpha=0.7)
ax.set_yticks(range(len(room_type_counts)))
ax.set_yticklabels(room_type_counts.index, fontsize=9)
ax.set_xlabel('Số lượng', fontsize=12)
ax.set_title('Top 10 Loại Phòng', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
save_plot(fig, '06_top_10_loai_phong.png', 'Top 10 Loại Phòng')

# 7. Mối quan hệ Giá vs Đánh giá
print("7. Tao bieu do gia vs danh gia...")
fig, ax = plt.subplots(figsize=(10, 6))
price_rating = df[['Final Price', 'Rating_Clean']].dropna()
price_rating['Final Price'] = price_rating['Final Price'] / 1000000  # Convert to millions
ax.scatter(price_rating['Rating_Clean'], price_rating['Final Price'], 
           alpha=0.5, s=20, color='steelblue')
ax.set_xlabel('Điểm đánh giá', fontsize=12)
ax.set_ylabel('Giá (triệu VNĐ)', fontsize=12)
ax.set_title('Mối quan hệ Giá và Đánh giá', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
save_plot(fig, '07_gia_vs_danh_gia.png', 'Mối quan hệ Giá và Đánh giá')

# 8. Phân tích giảm giá
print("8. Tao bieu do giam gia...")
fig, ax = plt.subplots(figsize=(10, 6))
discount_data = df['Discount %'].dropna()
discount_data = discount_data[discount_data > 0]  # Only show actual discounts
if len(discount_data) > 0:
    ax.hist(discount_data, bins=30, color='orange', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Phần trăm giảm giá (%)', fontsize=12)
    ax.set_ylabel('Số lượng', fontsize=12)
    ax.set_title('Phân bố Giảm giá', fontsize=14, fontweight='bold')
else:
    ax.text(0.5, 0.5, 'Không có dữ liệu giảm giá', 
            ha='center', va='center', fontsize=14, transform=ax.transAxes)
    ax.set_title('Phân bố Giảm giá', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
save_plot(fig, '08_phan_bo_giam_gia.png', 'Phân bố Giảm giá')

# 9. Free Cancellation và Breakfast
print("9. Tao bieu do mien phi huy va bua sang...")
fig, ax = plt.subplots(figsize=(10, 6))
free_cancel = df['Free_Cancel_Bool'].value_counts()
breakfast = df['Breakfast_Bool'].value_counts()
x = np.arange(2)
width = 0.35
ax.bar(x - width/2, [free_cancel.get(1, 0), free_cancel.get(0, 0)], 
        width, label='Miễn phí hủy', color='lightgreen', edgecolor='black', alpha=0.7)
ax.bar(x + width/2, [breakfast.get(1, 0), breakfast.get(0, 0)], 
        width, label='Bao gồm bữa sáng', color='lightcoral', edgecolor='black', alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels(['Có', 'Không'])
ax.set_ylabel('Số lượng', fontsize=12)
ax.set_title('Miễn phí Hủy và Bữa sáng', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
save_plot(fig, '09_mien_phi_huy_bua_sang.png', 'Miễn phí Hủy và Bữa sáng')

# 10. Giá trung bình theo địa điểm
print("10. Tao bieu do gia trung binh theo dia diem...")
fig, ax = plt.subplots(figsize=(10, 6))
location_price = (df.groupby('Search_Location_Clean')['Final Price'].mean().sort_values(ascending=False).head(10))
location_price = location_price / 1_000_000
ax.barh(range(len(location_price)), location_price.values, color='teal', edgecolor='black', alpha=0.7)
ax.set_yticks(range(len(location_price)))
ax.set_yticklabels(location_price.index, fontsize=10)
ax.set_xlabel('Giá trung bình (triệu VNĐ)', fontsize=12)
ax.set_title('Giá trung bình theo Địa điểm (Top 10)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
save_plot(fig, '10_gia_trung_binh_dia_diem.png', 'Giá trung bình theo Địa điểm')

# 11. Đánh giá trung bình theo địa điểm
print("11. Tao bieu do danh gia trung binh theo dia diem...")
fig, ax = plt.subplots(figsize=(10, 6))
location_rating = (df.groupby('Search_Location_Clean')['Rating_Clean'].mean().sort_values(ascending=False).head(10))
ax.barh(range(len(location_rating)), location_rating.values, color='salmon', edgecolor='black', alpha=0.7)
ax.set_yticks(range(len(location_rating)))
ax.set_yticklabels(location_rating.index, fontsize=10)
ax.set_xlabel('Điểm đánh giá trung bình', fontsize=12)
ax.set_title('Đánh giá trung bình theo Địa điểm (Top 10)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
save_plot(fig, '11_danh_gia_trung_binh_dia_diem.png', 'Đánh giá trung bình theo Địa điểm')

# 12. Phân bố số phòng
print("12. Tao bieu do phan bo so phong...")
fig, ax = plt.subplots(figsize=(10, 6))
rooms_data = df['Rooms'].dropna()
rooms_counts = rooms_data.value_counts().sort_index().head(10)
ax.bar(rooms_counts.index, rooms_counts.values, color='plum', edgecolor='black', alpha=0.7)
ax.set_xlabel('Số phòng', fontsize=12)
ax.set_ylabel('Số lượng', fontsize=12)
ax.set_title('Phân bố Số Phòng', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
save_plot(fig, '12_phan_bo_so_phong.png', 'Phân bố Số Phòng')

# 13. Phân bố diện tích
print("13. Tao bieu do phan bo dien tich...")
fig, ax = plt.subplots(figsize=(10, 6))
area_data = df['Area_m2_cleaned'].dropna()
area_data = area_data[(area_data > 0) & (area_data < 500)]  # Remove outliers
if len(area_data) > 0:
    ax.hist(area_data, bins=30, color='khaki', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Diện tích (m²)', fontsize=12)
    ax.set_ylabel('Số lượng', fontsize=12)
    ax.set_title('Phân bố Diện tích Phòng', fontsize=14, fontweight='bold')
else:
    ax.text(0.5, 0.5, 'Không có dữ liệu diện tích', 
            ha='center', va='center', fontsize=14, transform=ax.transAxes)
    ax.set_title('Phân bố Diện tích Phòng', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
save_plot(fig, '13_phan_bo_dien_tich.png', 'Phân bố Diện tích Phòng')

# 14. Giá theo số sao
print("14. Tao bieu do gia theo hang sao...")
fig, ax = plt.subplots(figsize=(10, 6))
stars_price = df.groupby('Stars_Clean')['Final Price'].mean()
stars_price = stars_price / 1000000  # Convert to millions
ax.bar(stars_price.index, stars_price.values, color='gold', edgecolor='black', alpha=0.7)
ax.set_xlabel('Số sao', fontsize=12)
ax.set_ylabel('Giá trung bình (triệu VNĐ)', fontsize=12)
ax.set_title('Giá trung bình theo Hạng Sao', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
save_plot(fig, '14_gia_theo_hang_sao.png', 'Giá trung bình theo Hạng Sao')

# 15. Phân bố số lượng khách
print("15. Tao bieu do phan bo so luong khach...")
fig, ax = plt.subplots(figsize=(10, 6))
guests_data = df['Total_Guests_Clean'].dropna()
guests_counts = guests_data.value_counts().sort_index()

ax.bar(guests_counts.index, guests_counts.values,
       color='lightseagreen', edgecolor='black', alpha=0.7)
ax.set_xlabel('Tổng số khách', fontsize=12)
ax.set_ylabel('Số lượng', fontsize=12)
ax.set_title('Phân bố Số lượng Khách (Đã chuẩn hóa)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
save_plot(fig, '15_phan_bo_so_luong_khach.png','Phân bố Số lượng Khách (Đã chuẩn hóa)')

# 16. Heatmap tương quan
print("16. Tao bieu do ma tran tuong quan...")
fig, ax = plt.subplots(figsize=(12, 10))
numeric_cols = ['Final Price', 'Original Price', 'Rating_Clean', 'Stars_Clean', 
                'Review Count', 'Distance_KM', 'Area_m2_cleaned', 'Rooms', 'Total_Guests_Clean']
# Only use columns that are actually numeric
numeric_df = df[numeric_cols].select_dtypes(include=[np.number])
corr_data = numeric_df.corr()
mask = np.triu(np.ones_like(corr_data, dtype=bool))
sns.heatmap(corr_data, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', 
            center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title('Ma trận Tương quan giữa các Biến', fontsize=14, fontweight='bold', pad=20)
save_plot(fig, '16_ma_tran_tuong_quan.png', 'Ma trận Tương quan giữa các Biến')

# Print summary statistics
print("\n" + "="*60)
print("THONG KE TONG QUAN")
print("="*60)
print(f"Tong so ban ghi: {len(df):,}")
print(f"So khach san duy nhat: {df['Hotel Name'].nunique():,}")
print(f"So dia diem tim kiem: {df['Search Location'].nunique()}")
print(f"\nGia phong:")
print(f"  - Trung binh: {df['Final Price'].mean()/1000000:.2f} trieu VND")
print(f"  - Trung vi: {df['Final Price'].median()/1000000:.2f} trieu VND")
print(f"  - Min: {df['Final Price'].min()/1000000:.2f} trieu VND")
print(f"  - Max: {df['Final Price'].max()/1000000:.2f} trieu VND")
print(f"\nDanh gia:")
print(f"  - Trung binh: {df['Rating_Clean'].mean():.2f}/10")
print(f"  - Trung vi: {df['Rating_Clean'].median():.2f}/10")
print(f"\nHang sao:")
print(f"  - Trung binh: {df['Stars_Clean'].mean():.1f} sao")
print(f"  - Phan bo: {df['Stars_Clean'].value_counts().sort_index().to_dict()}")

print(f"\n\nHoan thanh! Tat ca cac bieu do da duoc luu trong thu muc: {output_dir}/")
