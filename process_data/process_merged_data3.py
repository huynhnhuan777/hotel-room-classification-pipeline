import pandas as pd

# --- CẤU HÌNH ---
INPUT_FILE = "merged_data_cleaned_updated.csv"
OUTPUT_CLEAN_FILE = "merged_data_cleaned_updated1.csv"    # File dữ liệu chuẩn để dùng
OUTPUT_REMOVED_FILE = "removed_rows.csv"         # File chứa các dòng bị lọc bỏ (để check lại)

def filter_data():
    print(f"-> Đang đọc file: {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print("❌ Không tìm thấy file csv.")
        return

    # 1. Đảm bảo cột diện tích là số
    df['area_m2'] = pd.to_numeric(df['area_m2'], errors='coerce')

    # 2. Định nghĩa các điều kiện lọc
    # - Điều kiện 1: Location là 'Unknown'
    cond_unknown_loc = df['location'] == 'Unknown'
    
    # - Điều kiện 2: Diện tích > 120m2
    cond_large_area = df['area_m2'] > 120

    # 3. Tách dữ liệu
    # Dữ liệu BỊ LOẠI (Thỏa mãn 1 trong 2 điều kiện trên)
    df_removed = df[cond_unknown_loc | cond_large_area]

    # Dữ liệu SẠCH (Không thỏa mãn cả 2 điều kiện)
    df_clean = df[~(cond_unknown_loc | cond_large_area)]

    # 4. In thống kê
    print("-" * 30)
    print(f"Tổng số dòng ban đầu: {len(df)}")
    print(f"Số dòng bị loại bỏ:   {len(df_removed)}")
    print(f"   - Do Unknown Location: {cond_unknown_loc.sum()}")
    print(f"   - Do Diện tích > 120m2: {cond_large_area.sum()}")
    print(f"Số dòng giữ lại:      {len(df_clean)}")
    print("-" * 30)

    # 5. Xuất file
    # Lưu các dòng bị loại ra file riêng 
    if len(df_removed) > 0:
        df_removed.to_csv(OUTPUT_REMOVED_FILE, index=False, encoding='utf-8-sig')
        print(f"✅ Đã lưu các dòng bị loại vào: {OUTPUT_REMOVED_FILE}")

    # Lưu dữ liệu sạch
    if len(df_clean) > 0:
        df_clean.to_csv(OUTPUT_CLEAN_FILE, index=False, encoding='utf-8-sig')
        print(f"✅ Đã lưu dữ liệu sạch vào: {OUTPUT_CLEAN_FILE}")
    else:
        print("⚠️ Không còn dòng dữ liệu nào sau khi lọc!")

if __name__ == "__main__":
    filter_data()