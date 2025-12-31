import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# ==========================================
# 1. CẤU HÌNH & LOAD DỮ LIỆU
# ==========================================
def load_and_clean_data(file_path):
    print("--- Đang xử lý dữ liệu ---")
    
    try:
        df = pd.read_csv(file_path) 
    except:
        # Tạo dữ liệu giả lập để test nếu bạn chưa gắn file thật
        print("⚠ Không tìm thấy file, đang dùng dữ liệu mẫu để demo...")
        data = {
            'District': ['Quận 1', 'Quận 3', 'Quận 1', 'Quận 7', 'Quận 3', 'Binh Thanh', 'Quận 1'],
            'Final Price': [1500000, 3500000, 5400000, 1200000, 1600000, 900000, 8000000],
            'Area_m2': ['25 m2', '13 m2', '30 m2', '20 m2', '15 m²', '18 m2', '45 m2'],
            'Total_Guest': [2, 4, 2, 2, 2, 1, 4],
            'Rating_Clean': [8.5, 9.0, 9.5, 7.8, 8.2, 7.5, 9.8]
        }
        df = pd.DataFrame(data)

    # --- LÀM SẠCH DỮ LIỆU (DATA CLEANING) ---
    
    # 1. Xử lý cột Diện tích (Area_m2): Bỏ chữ 'm2', 'm²', khoảng trắng
    if 'Area_m2' in df.columns:
        # Dùng Regex để chỉ giữ lại số và dấu chấm
        df['Area_Clean'] = df['Area_m2'].astype(str).apply(lambda x: re.sub(r'[^\d.]', '', x))
        df['Area_Clean'] = pd.to_numeric(df['Area_Clean'], errors='coerce')
    
    # 2. Xử lý cột Giá (Final Price)
    if 'Final Price' in df.columns:
        df['Price_Clean'] = pd.to_numeric(df['Final Price'], errors='coerce')

    # 3. Loại bỏ các dòng bị lỗi (NaN) sau khi convert
    df = df.dropna(subset=['Area_Clean', 'Price_Clean'])
    
    print(f"-> Đã xử lý xong. Số dòng dữ liệu sạch: {len(df)}")
    return df

# ==========================================
# 2. CÁC HÀM VẼ BIỂU ĐỒ (VISUALIZATION)
# ==========================================

def plot_price_distribution(df):
    """Biểu đồ 1: Phân phối giá phòng (Histogram)"""
    plt.figure(figsize=(10, 6))
    sns.histplot(df['Price_Clean'], kde=True, color='skyblue', bins=20)
    plt.title('Phân phối Giá phòng (Price Distribution)', fontsize=14)
    plt.xlabel('Giá (VNĐ)')
    plt.ylabel('Số lượng phòng')
    # Format trục X sang dạng tiền tệ cho dễ đọc
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    plt.show()

def plot_price_vs_district(df):
    """Biểu đồ 2: So sánh giá giữa các Quận (Boxplot)"""
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, x='District', y='Price_Clean', palette="Set2")
    plt.title('Mức giá theo từng Quận (Price by District)', fontsize=14)
    plt.xlabel('Khu vực')
    plt.ylabel('Giá (VNĐ)')
    plt.xticks(rotation=45)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    plt.show()

def plot_area_vs_price(df):
    """Biểu đồ 3: Tương quan Diện tích vs Giá tiền (Scatter Plot)"""
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='Area_Clean', y='Price_Clean', 
                    hue='District', size='Total_Guest', sizes=(20, 200), alpha=0.7)
    plt.title('Tương quan: Diện tích vs Giá phòng', fontsize=14)
    plt.xlabel('Diện tích (m2)')
    plt.ylabel('Giá (VNĐ)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    plt.show()

def plot_correlation_heatmap(df):
    """Biểu đồ 4: Ma trận tương quan (Heatmap)"""
    # Chỉ lấy các cột số
    numeric_df = df[['Price_Clean', 'Area_Clean', 'Total_Guest', 'Rating_Clean']]
    corr = numeric_df.corr()
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title('Ma trận tương quan (Correlation Matrix)', fontsize=14)
    plt.show()

# ==========================================
# 3. CHẠY CHƯƠNG TRÌNH
# ==========================================
if __name__ == "__main__":
    # Cấu hình font chữ để tránh lỗi tiếng Việt (nếu có)
    sns.set_theme(style="whitegrid")
    
    # 1. Load dữ liệu
    # Thay 'full_data_merged.csv' bằng đường dẫn file CSV thực tế của bạn
    file_name = 'full_data_merged.csv' 
    df_hotel = load_and_clean_data(file_name)

    # 2. Vẽ biểu đồ
    # Biểu đồ 1: Xem giá tập trung ở khoảng nào
    plot_price_distribution(df_hotel)
    
    # Biểu đồ 2: Xem quận nào đắt nhất
    plot_price_vs_district(df_hotel)
    
    # Biểu đồ 3: Xem diện tích lớn có đồng nghĩa giá cao không
    plot_area_vs_price(df_hotel)
    
    # Biểu đồ 4: Xem mối liên hệ tổng quan
    plot_correlation_heatmap(df_hotel)