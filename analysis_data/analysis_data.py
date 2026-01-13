import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Đọc dữ liệu
file_path = '../data_booking.com/full_data_merged.csv' 
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Không tìm thấy file tại {file_path}. Vui lòng kiểm tra lại đường dẫn.")
    exit()

# 2. Chuẩn bị dữ liệu
df['Final Price (Million)'] = df['Final Price'] / 1_000_000
df['Original Price (Million)'] = df['Original Price'] / 1_000_000

# Thiết lập giao diện
sns.set_theme(style="whitegrid")
plt.figure(figsize=(18, 12))

# --- Biểu đồ 1: Số lượng khách sạn/phòng theo Quận ---
plt.subplot(2, 2, 1)
district_counts = df['District'].value_counts()
sns.barplot(
    x=district_counts.values, 
    y=district_counts.index, 
    hue=district_counts.index, 
    legend=False, 
    palette="viridis"
)
plt.title('Số lượng Khách sạn/Phòng theo Quận')
plt.xlabel('Số lượng')
plt.ylabel('Quận')

# --- Biểu đồ 2: Mối quan hệ giữa Giá (Triệu) và Diện tích (m2) ---
plt.subplot(2, 2, 2)
df_area = df.dropna(subset=['Area_m2_cleaned'])
sns.scatterplot(
    data=df_area, 
    x='Area_m2_cleaned', 
    y='Final Price (Million)', 
    hue='Stars_Clean', 
    size='Stars_Clean', 
    sizes=(50, 200), 
    palette="deep"
)
plt.title('Tương quan giữa Giá phòng và Diện tích')
plt.xlabel('Diện tích (m2)')
plt.ylabel('Giá cuối cùng (Triệu VNĐ)')
plt.legend(title='Số Sao', bbox_to_anchor=(1.05, 1), loc='upper left')

# --- Biểu đồ 3: Phân bố Giá theo Xếp hạng Sao ---
plt.subplot(2, 2, 3)
sns.boxplot(
    data=df, 
    x='Stars_Clean', 
    y='Final Price (Million)', 
    hue='Stars_Clean', 
    legend=False, 
    palette="Set2"
)
plt.title('Phân bố Giá phòng theo Số Sao')
plt.xlabel('Số Sao')
plt.ylabel('Giá cuối cùng (Triệu VNĐ)')

# --- Biểu đồ 4: Ma trận tương quan ---
plt.subplot(2, 2, 4)
cols_corr = ['Final Price', 'Original Price', 'Discount %', 'Rating_Clean', 
             'Review Count', 'Distance_KM', 'Area_m2_cleaned', 'Stars_Clean']
corr_matrix = df[cols_corr].corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
plt.title('Ma trận tương quan giữa các biến số')

plt.tight_layout()

# --- LƯU ẢNH ---
# Lưu file vào thư mục exports với độ phân giải cao (dpi=300)
output_img_path = '../data_booking.com/hotel_analysis_report.png'
plt.savefig(output_img_path, dpi=300, bbox_inches='tight')
print(f"-> Đã lưu ảnh phân tích tại: {output_img_path}")

plt.show()