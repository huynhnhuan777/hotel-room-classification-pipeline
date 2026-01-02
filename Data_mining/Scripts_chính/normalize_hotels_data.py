"""
Script chuyển đổi dữ liệu hotels từ JSONL sang CSV
"""
import json
import csv
import argparse
import os
from typing import Dict, Any

def extract_field(hotel: Dict[str, Any], *keys, default=None):
    """Extract field từ nested dict"""
    for key in keys:
        if isinstance(hotel, dict):
            hotel = hotel.get(key)
        else:
            return default
        if hotel is None:
            return default
    return hotel

def normalize_hotel(hotel: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize hotel data từ raw format sang standard format"""
    normalized = {}
    
    # Hotel ID
    normalized['hotelId'] = str(extract_field(hotel, 'hotelId', default=''))
    if not normalized['hotelId']:
        normalized['hotelId'] = str(extract_field(hotel, 'id', default=''))
    
    # Hotel Name
    normalized['hotelName'] = extract_field(hotel, 'hotelName', default='')
    if not normalized['hotelName']:
        normalized['hotelName'] = extract_field(hotel, 'name', default='')
    
    # Star rating
    normalized['star'] = extract_field(hotel, 'star', default=0)
    if not normalized['star']:
        normalized['star'] = extract_field(hotel, 'starRating', default=0)
    
    # Review Score
    normalized['reviewScore'] = extract_field(hotel, 'reviewScore', default='')
    if not normalized['reviewScore']:
        reviews = extract_field(hotel, 'reviews', default={})
        if isinstance(reviews, dict):
            normalized['reviewScore'] = reviews.get('score', '')
    
    # Review Score Text
    normalized['reviewScoreText'] = extract_field(hotel, 'reviewScoreText', default='')
    
    # Review Count
    normalized['reviewCount'] = extract_field(hotel, 'reviewCount', default='')
    if not normalized['reviewCount']:
        reviews = extract_field(hotel, 'reviews', default={})
        if isinstance(reviews, dict):
            normalized['reviewCount'] = reviews.get('total', '')
    
    # City ID
    normalized['cityId'] = extract_field(hotel, 'cityId', default='')
    
    # City Name
    normalized['cityName'] = extract_field(hotel, 'cityName', default='')
    if not normalized['cityName']:
        location = extract_field(hotel, 'location', default={})
        if isinstance(location, dict):
            normalized['cityName'] = location.get('city', '')
    
    # District ID
    normalized['districtId'] = extract_field(hotel, 'districtId', default='')
    
    # District Name
    normalized['districtName'] = extract_field(hotel, 'districtName', default='')
    
    # Latitude
    normalized['latitude'] = extract_field(hotel, 'latitude', default='')
    if not normalized['latitude']:
        location = extract_field(hotel, 'location', default={})
        if isinstance(location, dict):
            coords = location.get('coordinates', {})
            if isinstance(coords, dict):
                normalized['latitude'] = coords.get('latitude', '')
    
    # Longitude
    normalized['longitude'] = extract_field(hotel, 'longitude', default='')
    if not normalized['longitude']:
        location = extract_field(hotel, 'location', default={})
        if isinstance(location, dict):
            coords = location.get('coordinates', {})
            if isinstance(coords, dict):
                normalized['longitude'] = coords.get('longitude', '')
    
    # Nearby Landmark
    normalized['nearbyLandmark'] = extract_field(hotel, 'nearbyLandmark', default='')
    
    # Min Price
    normalized['minPrice'] = extract_field(hotel, 'minPrice', default='')
    if not normalized['minPrice']:
        price = extract_field(hotel, 'price', default={})
        if isinstance(price, dict):
            lead = price.get('lead', {})
            if isinstance(lead, dict):
                normalized['minPrice'] = lead.get('amount', '')
    
    # Avg Price
    normalized['avgPrice'] = extract_field(hotel, 'avgPrice', default='')
    
    # Original Price
    normalized['originalPrice'] = extract_field(hotel, 'originalPrice', default='')
    
    # Currency
    normalized['currency'] = extract_field(hotel, 'currency', default='USD')
    if normalized['currency'] == 'USD' and not extract_field(hotel, 'currency'):
        price = extract_field(hotel, 'price', default={})
        if isinstance(price, dict):
            lead = price.get('lead', {})
            if isinstance(lead, dict):
                normalized['currency'] = lead.get('currency', 'USD')
    
    # Rooms Left
    normalized['roomsLeft'] = extract_field(hotel, 'roomsLeft', default='')
    
    # Last Booked Text
    normalized['lastBookedText'] = extract_field(hotel, 'lastBookedText', default='')
    
    # Button Content
    normalized['buttonContent'] = extract_field(hotel, 'buttonContent', default='')
    
    # Is Sold Out
    normalized['isSoldOut'] = extract_field(hotel, 'isSoldOut', default='')
    
    # Hotel Type
    normalized['hotelType'] = extract_field(hotel, 'hotelType', default='')
    
    # Additional fields from enrichment
    normalized['description'] = extract_field(hotel, 'description', default='')
    normalized['amenities'] = extract_field(hotel, 'amenities', default='')
    if isinstance(normalized['amenities'], list):
        normalized['amenities'] = ', '.join(normalized['amenities'])
    normalized['roomTypes'] = extract_field(hotel, 'roomTypes', default='')
    if isinstance(normalized['roomTypes'], list):
        normalized['roomTypes'] = ', '.join(normalized['roomTypes'])
    normalized['fullAddress'] = extract_field(hotel, 'fullAddress', default='')
    
    return normalized

def jsonl_to_csv(input_file: str, output_file: str):
    """Convert JSONL file to CSV"""
    if not os.path.exists(input_file):
        print(f"❌ File không tồn tại: {input_file}")
        return
    
    # Field names
    fieldnames = [
        'hotelId', 'hotelName', 'star', 'reviewScore', 'reviewScoreText', 'reviewCount',
        'cityId', 'cityName', 'districtId', 'districtName', 'latitude', 'longitude',
        'nearbyLandmark', 'minPrice', 'avgPrice', 'originalPrice', 'currency',
        'roomsLeft', 'lastBookedText', 'buttonContent', 'isSoldOut', 'hotelType',
        'description', 'amenities', 'roomTypes', 'fullAddress'
    ]
    
    hotels_processed = 0
    hotels_skipped = 0
    
    print(f"Đang đọc từ {input_file}...")
    print(f"Đang ghi vào {output_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                hotel = json.loads(line)
                normalized = normalize_hotel(hotel)
                
                # Chỉ ghi nếu có hotelId
                if normalized.get('hotelId'):
                    writer.writerow(normalized)
                    hotels_processed += 1
                else:
                    hotels_skipped += 1
                    if hotels_skipped <= 5:
                        print(f"  ⚠ Bỏ qua hotel không có ID ở dòng {line_num}")
                
            except json.JSONDecodeError as e:
                hotels_skipped += 1
                if hotels_skipped <= 5:
                    print(f"  ⚠ Lỗi parse JSON ở dòng {line_num}: {e}")
            except Exception as e:
                hotels_skipped += 1
                if hotels_skipped <= 5:
                    print(f"  ⚠ Lỗi xử lý dòng {line_num}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✓ HOÀN TẤT!")
    print(f"  - Hotels đã xử lý: {hotels_processed}")
    print(f"  - Hotels bỏ qua: {hotels_skipped}")
    print(f"  - File output: {output_file}")
    print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(description='Chuyển đổi dữ liệu hotels từ JSONL sang CSV')
    parser.add_argument('--input', '-i', default='hotels_data_full.jsonl',
                        help='File JSONL input (default: hotels_data_full.jsonl)')
    parser.add_argument('--output', '-o', default='hotels_data_complete.csv',
                        help='File CSV output (default: hotels_data_complete.csv)')
    
    args = parser.parse_args()
    
    jsonl_to_csv(args.input, args.output)

if __name__ == "__main__":
    main()






