"""
Script merge dữ liệu hotels mới vào file chính
"""
import json
import os
import shutil
from datetime import datetime

# File paths
FULL_DATA_FILE = 'hotels_data_full.jsonl'
NEW_DATA_FILE = 'hotels_data_hcm.jsonl'
BACKUP_SUFFIX = '_backup.jsonl'

def load_hotel_ids(file_path):
    """Load hotel IDs từ file JSONL"""
    hotel_ids = set()
    hotels = []
    
    if not os.path.exists(file_path):
        return hotel_ids, hotels
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                hotel = json.loads(line)
                hotel_id = str(hotel.get('hotelId', ''))
                if hotel_id:
                    hotel_ids.add(hotel_id)
                    hotels.append((hotel_id, hotel))
            except:
                pass
    
    return hotel_ids, hotels

def merge_data():
    """Merge dữ liệu mới vào file chính"""
    print("="*60)
    print("MERGE HOTELS DATA")
    print("="*60)
    
    # Load existing data
    print(f"\nĐang load dữ liệu từ {FULL_DATA_FILE}...")
    existing_ids, existing_hotels = load_hotel_ids(FULL_DATA_FILE)
    print(f"✓ Đã load {len(existing_ids)} hotels từ file chính")
    
    # Load new data
    if not os.path.exists(NEW_DATA_FILE):
        print(f"\n❌ Không tìm thấy file {NEW_DATA_FILE}")
        return
    
    print(f"\nĐang load dữ liệu từ {NEW_DATA_FILE}...")
    new_ids, new_hotels = load_hotel_ids(NEW_DATA_FILE)
    print(f"✓ Đã load {len(new_ids)} hotels từ file mới")
    
    # Find new hotels
    new_hotel_dict = {hotel_id: hotel for hotel_id, hotel in new_hotels}
    existing_hotel_dict = {hotel_id: hotel for hotel_id, hotel in existing_hotels}
    
    # Filter chỉ lấy hotels chưa có
    hotels_to_add = []
    for hotel_id, hotel in new_hotel_dict.items():
        if hotel_id not in existing_ids:
            hotels_to_add.append(hotel)
    
    print(f"\nTìm thấy {len(hotels_to_add)} hotels mới cần thêm")
    
    if len(hotels_to_add) == 0:
        print("\n✓ Không có hotels mới để merge")
        return
    
    # Backup file cũ
    if os.path.exists(FULL_DATA_FILE):
        backup_file = FULL_DATA_FILE.replace('.jsonl', BACKUP_SUFFIX)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_file.replace('.jsonl', f'_{timestamp}.jsonl')
        
        print(f"\nĐang backup file cũ...")
        shutil.copy2(FULL_DATA_FILE, backup_file)
        print(f"✓ Đã backup vào {backup_file}")
    
    # Append new hotels
    print(f"\nĐang ghi {len(hotels_to_add)} hotels mới vào {FULL_DATA_FILE}...")
    
    # Nếu file chưa tồn tại, tạo mới
    mode = 'a' if os.path.exists(FULL_DATA_FILE) else 'w'
    
    with open(FULL_DATA_FILE, mode, encoding='utf-8') as f:
        for hotel in hotels_to_add:
            f.write(json.dumps(hotel, ensure_ascii=False) + '\n')
    
    # Verify
    final_ids, final_hotels = load_hotel_ids(FULL_DATA_FILE)
    
    print(f"\n{'='*60}")
    print(f"✓ HOÀN TẤT!")
    print(f"  - Hotels mới thêm: {len(hotels_to_add)}")
    print(f"  - Tổng hotels trong file chính: {len(final_ids)}")
    print(f"  - File: {FULL_DATA_FILE}")
    print(f"{'='*60}")
    
    # Option: Clear new data file
    response = input(f"\nBạn có muốn xóa file {NEW_DATA_FILE} sau khi merge? (y/n): ")
    if response.lower() == 'y':
        os.remove(NEW_DATA_FILE)
        print(f"✓ Đã xóa {NEW_DATA_FILE}")

if __name__ == "__main__":
    merge_data()






