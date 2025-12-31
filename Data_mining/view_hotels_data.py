"""
Script để xem và convert dữ liệu hotels từ JSONL sang JSON array
"""
import json
import os

OUTPUT_FILE = 'hotels_complete_hcm.jsonl'
JSON_OUTPUT_FILE = 'hotels_complete_hcm.json'

def view_jsonl_data():
    """Đọc và hiển thị dữ liệu từ file JSONL"""
    if not os.path.exists(OUTPUT_FILE):
        print(f"❌ File {OUTPUT_FILE} chưa tồn tại!")
        print("   Hãy chạy hotels_crawl_hcm.py trước để crawl dữ liệu.")
        return
    
    hotels = []
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                hotel = json.loads(line.strip())
                hotels.append(hotel)
            except json.JSONDecodeError as e:
                print(f"⚠️ Lỗi parse dòng {line_num}: {e}")
                continue
    
    print(f"\n{'='*60}")
    print(f"📊 THỐNG KÊ DỮ LIỆU")
    print(f"{'='*60}")
    print(f"Tổng số khách sạn: {len(hotels)}")
    
    if hotels:
        # Thống kê
        hotels_with_amenities = sum(1 for h in hotels if h.get('amenities'))
        hotels_with_rooms = sum(1 for h in hotels if h.get('roomTypes'))
        
        print(f"  - Có amenities: {hotels_with_amenities}")
        print(f"  - Có loại phòng: {hotels_with_rooms}")
        
        # Hiển thị mẫu
        print(f"\n{'='*60}")
        print(f"📋 MẪU DỮ LIỆU (Hotel đầu tiên):")
        print(f"{'='*60}")
        sample = hotels[0]
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        
        # Convert sang JSON array và lưu
        print(f"\n{'='*60}")
        print(f"💾 Đang lưu sang file JSON array...")
        with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(hotels, f, ensure_ascii=False, indent=2)
        print(f"✓ Đã lưu vào: {JSON_OUTPUT_FILE}")
        print(f"  (File này dễ đọc hơn trong editor)")
        
        # Hiển thị chi tiết từng hotel
        print(f"\n{'='*60}")
        print(f"📋 CHI TIẾT TỪNG KHÁCH SẠN:")
        print(f"{'='*60}")
        for idx, hotel in enumerate(hotels, 1):
            print(f"\n{idx}. {hotel.get('hotelName', 'N/A')}")
            print(f"   ID: {hotel.get('hotelId', 'N/A')}")
            print(f"   Giá: {hotel.get('minPrice', 'N/A')} {hotel.get('currency', '')}")
            amenities = hotel.get('amenities', [])
            rooms = hotel.get('roomTypes', [])
            print(f"   Tiện ích: {len(amenities)} items")
            if amenities:
                print(f"      - {', '.join(amenities[:5])}{'...' if len(amenities) > 5 else ''}")
            print(f"   Loại phòng: {len(rooms)} loại")
            if rooms:
                for room_idx, room in enumerate(rooms[:3], 1):
                    room_name = room.get('room_name', 'N/A')
                    price = room.get('price_per_night', 'N/A')
                    print(f"      {room_idx}. {room_name} - {price} VND")
    else:
        print("⚠️ Không có dữ liệu trong file!")

if __name__ == "__main__":
    view_jsonl_data()


