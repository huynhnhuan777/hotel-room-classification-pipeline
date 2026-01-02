import pandas as pd
import os

def merge_ivivu_data():
    """
    Gộp các file CSV hotels và rooms từ iVIVU
    Đánh lại ID mới cho khớp giữa hotels và rooms
    """
    
    # Đọc các file hotels
    print("Đang đọc các file hotels...")
    hotels_bd = pd.read_csv('ivivu_hotels_bd.csv')
    hotels_hcm = pd.read_csv('ivivu_hotels_hcm.csv')
    hotels_vt = pd.read_csv('ivivu_hotels_vt.csv')
    
    # Đọc các file rooms
    print("Đang đọc các file rooms...")
    rooms_bd = pd.read_csv('ivivu_rooms_bd.csv')
    rooms_hcm = pd.read_csv('ivivu_rooms_hcm.csv')
    rooms_vt = pd.read_csv('ivivu_rooms_vt.csv')
    
    # Gộp tất cả hotels
    print("\nGộp hotels...")
    all_hotels = pd.concat([hotels_bd, hotels_hcm, hotels_vt], ignore_index=True)
    
    # Tạo mapping từ hotel_id cũ sang hotel_id mới
    hotel_id_mapping = {}
    for idx, old_id in enumerate(all_hotels['hotel_id']):
        new_id = f"IVU_HOTEL_{str(idx + 1).zfill(6)}"
        hotel_id_mapping[old_id] = new_id
    
    # Đánh lại hotel_id mới
    all_hotels['hotel_id'] = all_hotels['hotel_id'].map(hotel_id_mapping)
    
    # Gộp tất cả rooms
    print("Gộp rooms...")
    all_rooms = pd.concat([rooms_bd, rooms_hcm, rooms_vt], ignore_index=True)
    
    # Cập nhật hotel_id trong rooms theo mapping
    all_rooms['hotel_id'] = all_rooms['hotel_id'].map(hotel_id_mapping)
    
    # Đánh lại room_id mới
    all_rooms['room_id'] = [f"IVU_ROOM_{str(i + 1).zfill(6)}" for i in range(len(all_rooms))]
    
    # Thống kê
    print("\n" + "="*60)
    print("THỐNG KÊ")
    print("="*60)
    print(f"Tổng số hotels: {len(all_hotels)}")
    print(f"  - Bình Dương: {len(hotels_bd)}")
    print(f"  - TP.HCM: {len(hotels_hcm)}")
    print(f"  - Vũng Tàu: {len(hotels_vt)}")
    print(f"\nTổng số rooms: {len(all_rooms)}")
    print(f"  - Bình Dương: {len(rooms_bd)}")
    print(f"  - TP.HCM: {len(rooms_hcm)}")
    print(f"  - Vũng Tàu: {len(rooms_vt)}")
    print("="*60)
    
    # Lưu file kết quả
    print("\nĐang lưu files...")
    all_hotels.to_csv('merged_hotels.csv', index=False, encoding='utf-8-sig')
    all_rooms.to_csv('merged_rooms.csv', index=False, encoding='utf-8-sig')
    
    print("✓ Đã lưu: merged_hotels.csv")
    print("✓ Đã lưu: merged_rooms.csv")
    
    # Preview kết quả
    print("\n" + "="*60)
    print("PREVIEW HOTELS (5 dòng đầu)")
    print("="*60)
    print(all_hotels[['hotel_id', 'city', 'hotel_name']].head())
    
    print("\n" + "="*60)
    print("PREVIEW ROOMS (5 dòng đầu)")
    print("="*60)
    print(all_rooms[['room_id', 'hotel_id', 'room_name', 'price']].head())
    
    # Kiểm tra mapping
    print("\n" + "="*60)
    print("KIỂM TRA MAPPING")
    print("="*60)
    missing_hotels = all_rooms[~all_rooms['hotel_id'].isin(all_hotels['hotel_id'])]
    if len(missing_hotels) == 0:
        print("✓ Tất cả rooms đều có hotel_id hợp lệ")
    else:
        print(f"⚠ Có {len(missing_hotels)} rooms không khớp với hotel_id")
    
    return all_hotels, all_rooms


if __name__ == "__main__":
    try:
        # Kiểm tra các file có tồn tại không
        required_files = [
            'ivivu_hotels_bd.csv',
            'ivivu_hotels_hcm.csv',
            'ivivu_hotels_vt.csv',
            'ivivu_rooms_bd.csv',
            'ivivu_rooms_hcm.csv',
            'ivivu_rooms_vt.csv'
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            print("❌ THIẾU CÁC FILE SAU:")
            for f in missing_files:
                print(f"  - {f}")
            print("\nVui lòng đảm bảo tất cả files ở cùng thư mục với script!")
        else:
            hotels, rooms = merge_ivivu_data()
            print("\n✅ HOÀN THÀNH!")
            
    except Exception as e:
        print(f"\n❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()