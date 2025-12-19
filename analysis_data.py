import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Cấu hình hiển thị đẹp
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

def visualize_data(input_file):
    try:
        df = pd.read_csv(input_file)
    except:
        print(" Không tìm thấy file dữ liệu sạch!")
        return

    print(f" Đang phân tích dữ liệu từ {len(df)} dòng...")

    # --- BIỂU ĐỒ 1: PHÂN BỐ GIÁ THEO HẠNG PHÒNG ---
    # Mục đích: Kiểm tra xem phân loại phòng của bạn có tách biệt được mức giá không.
    plt.figure(figsize=(14, 7))
    
    # Sắp xếp thứ tự hạng phòng để dễ nhìn
    order = ['Dormitory', 'Standard/Superior', 'Apartment/Studio', 
             'Deluxe', 'Family/Large', 'Premium/Luxury', 'Presidential/Suite']
    
    sns.boxplot(data=df, x='Room_Class', y='Final Price', order=order, palette="viridis")
    plt.title('Phân bố giá phòng theo Hạng phòng (Room Class)', fontsize=16)
    plt.xlabel('Hạng phòng')
    plt.ylabel('Giá cuối (VND)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # --- BIỂU ĐỒ 2: GIÁ TRUNG BÌNH THEO QUẬN ---
    # Mục đích: Xem khu vực nào đắt đỏ nhất.
    plt.figure(figsize=(12, 6))
    
    # Tính giá trung bình và sắp xếp giảm dần
    dist_price = df.groupby('District')['Final Price'].mean().sort_values(ascending=False).reset_index()
    
    sns.barplot(data=dist_price, x='Final Price', y='District', palette="magma")
    plt.title('Giá trung bình khách sạn theo Quận/Huyện', fontsize=16)
    plt.xlabel('Giá trung bình (VND)')
    plt.ylabel('Khu vực')
    plt.tight_layout()
    plt.show()

    # --- BIỂU ĐỒ 3: TƯƠNG QUAN GIỮA ĐIỂM ĐÁNH GIÁ VÀ GIÁ TIỀN ---
    # Mục đích: "Tiền nào của nấy" hay "Ngon bổ rẻ"?
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='Rating_Clean', y='Final Price', 
                    hue='Room_Class', size='Stars_Clean', sizes=(20, 200), alpha=0.7)
    plt.title('Tương quan: Điểm đánh giá (Rating) vs Giá tiền', fontsize=16)
    plt.xlabel('Điểm đánh giá (Thang 10)')
    plt.ylabel('Giá tiền')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

    # --- THỐNG KÊ NHANH ---
    print("\n---  INSIGHT NHANH ---")
    print(f" Khách sạn đắt nhất: {df.loc[df['Final Price'].idxmax()]['Hotel Name']} ({df['Final Price'].max():,.0f} VND)")
    print(f" Khách sạn rẻ nhất: {df.loc[df['Final Price'].idxmin()]['Hotel Name']} ({df['Final Price'].min():,.0f} VND)")
    print(f" Điểm đánh giá trung bình toàn TP: {df['Rating_Clean'].mean():.1f}/10")

if __name__ == "__main__":
    INPUT_CSV = "booking_data_cleaned.csv"
    visualize_data(INPUT_CSV)