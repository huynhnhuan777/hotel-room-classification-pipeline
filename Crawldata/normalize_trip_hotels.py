#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import csv
import argparse
import statistics
from typing import Any, Dict, List, Optional

def safe_get(obj: Any, *keys, default=None):
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key)
        elif isinstance(obj, list) and len(obj) > 0:
            obj = obj[0].get(key) if isinstance(obj[0], dict) else None
        else:
            return default
        if obj is None:
            return default
    return obj

def safe_str(value: Any, default='') -> str:
    """Convert value to string safely"""
    if value is None:
        return default
    if isinstance(value, list):
        return ', '.join(str(v) for v in value)
    return str(value)

def safe_int(value: Any, default=None):
    """Convert value to int safely"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            value = value.replace(',', '').replace(' ', '').replace('₫', '')
        return int(float(value))
    except:
        return default

def safe_float(value: Any, default=None):
    """Convert value to float safely"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            value = value.replace(',', '').replace(' ', '')
        return float(value)
    except:
        return default

def extract_all_fields(obj: Dict) -> Dict:
    """Extract all fields from hotel JSON object"""
    hotel_info = obj.get('hotelInfo', {})
    room_info = obj.get('roomInfo', [])
    
    # Extract from hotelInfo.summary
    summary = hotel_info.get('summary', {})
    hotel_id = safe_str(summary.get('hotelId'), '')
    
    # Extract from hotelInfo.nameInfo
    name_info = hotel_info.get('nameInfo', {})
    hotel_name = safe_str(name_info.get('name'), '')
    
    # Extract from hotelInfo.hotelStar
    hotel_star = hotel_info.get('hotelStar', {})
    star = safe_int(hotel_star.get('star'))
    star_type = safe_int(hotel_star.get('starType'))
    
    # Extract from hotelInfo.hotelCategory
    hotel_category = hotel_info.get('hotelCategory', {})
    category_name = safe_str(hotel_category.get('categoryName'), '')
    category_id = safe_int(hotel_category.get('categoryId'))
    
    # Extract from hotelInfo.commentInfo
    comment_info = hotel_info.get('commentInfo', {})
    comment_score = safe_str(comment_info.get('commentScore'), '')
    comment_description = safe_str(comment_info.get('commentDescription'), '')
    commenter_number = safe_str(comment_info.get('commenterNumber'), '')
    full_rating = safe_str(comment_info.get('fullRating'), '')
    
    # Extract sub scores
    sub_scores = comment_info.get('subScore', [])
    cleanliness_score = ''
    facilities_score = ''
    location_score = ''
    service_score = ''
    for sub in sub_scores:
        score_type = sub.get('scoreType')
        score_value = safe_str(sub.get('number'), '')
        if score_type == 3:  # Vệ sinh
            cleanliness_score = score_value
        elif score_type == 5:  # Trang thiết bị
            facilities_score = score_value
        elif score_type == 2:  # Vị trí
            location_score = score_value
        elif score_type == 4:  # Dịch vụ
            service_score = score_value
    
    # Extract from hotelInfo.positionInfo
    position_info = hotel_info.get('positionInfo', {})
    city_id = safe_int(position_info.get('cityId'))
    city_name = safe_str(position_info.get('cityName'), '')
    address = safe_str(position_info.get('address'), '')
    position_desc = safe_str(position_info.get('positionDesc'), '')
    
    # Extract coordinates
    map_coordinates = position_info.get('mapCoordinate', [])
    latitude = None
    longitude = None
    for coord in map_coordinates:
        if coord.get('coordinateType') == 1:  # WGS84
            latitude = safe_float(coord.get('latitude'))
            longitude = safe_float(coord.get('longitude'))
            break
    
    # Extract from hotelInfo.hotelImages
    hotel_images = hotel_info.get('hotelImages', {})
    image_url = safe_str(hotel_images.get('url'), '')
    multi_imgs = hotel_images.get('multiImgs', [])
    image_urls = ', '.join([safe_str(img.get('url'), '') for img in multi_imgs[:5]])
    
    # Extract from hotelInfo.statusInfo
    status_info = hotel_info.get('statusInfo', {})
    button_content = safe_str(status_info.get('buttonContent'), '')
    
    # Extract amenities from hotelInfo.amenities
    amenities_list = hotel_info.get('amenities', [])
    if isinstance(amenities_list, list):
        # Filter out empty strings
        amenities_list = [a for a in amenities_list if a and str(a).strip()]
        amenities_str = ', '.join(str(a) for a in amenities_list)
    else:
        amenities_str = safe_str(amenities_list, '')
    
    # Extract prices from roomInfo
    prices = []
    list_prices = []
    display_prices = []
    room_names = []
    check_in_dates = []
    check_out_dates = []
    
    if isinstance(room_info, list):
        for room in room_info:
            # Price info
            price_info = room.get('priceInfo', {})
            price = safe_int(price_info.get('price'))
            display_price = safe_str(price_info.get('displayPrice'), '')
            delete_price = safe_int(price_info.get('deletePrice'))
            
            if price is not None:
                prices.append(price)
            if delete_price is not None:
                list_prices.append(delete_price)
            if display_price:
                display_prices.append(display_price)
            
            # Room summary
            room_summary = room.get('summary', {})
            physics_name = safe_str(room_summary.get('physicsName'), '')
            if physics_name:
                room_names.append(physics_name)
            
            # Status info
            room_status = room.get('statusInfo', {})
            check_in = safe_str(room_status.get('checkIn'), '')
            check_out = safe_str(room_status.get('checkOut'), '')
            if check_in:
                check_in_dates.append(check_in)
            if check_out:
                check_out_dates.append(check_out)
    
    # Calculate min/avg/max price
    min_price = safe_int(min(prices)) if prices else None
    avg_price = safe_int(round(statistics.mean(prices))) if prices else None
    max_price = safe_int(max(list_prices)) if list_prices else (safe_int(max(prices)) if prices else None)
    
    return {
        'hotelId': hotel_id,
        'hotelName': hotel_name,
        'star': safe_str(star) if star is not None else '',
        'starType': safe_str(star_type) if star_type is not None else '',
        'categoryName': category_name,
        'categoryId': safe_str(category_id) if category_id is not None else '',
        'cityId': safe_str(city_id) if city_id is not None else '',
        'cityName': city_name,
        'address': address,
        'positionDesc': position_desc,
        'latitude': safe_str(latitude) if latitude is not None else '',
        'longitude': safe_str(longitude) if longitude is not None else '',
        'commentScore': comment_score,
        'commentDescription': comment_description,
        'commenterNumber': commenter_number,
        'fullRating': full_rating,
        'cleanlinessScore': cleanliness_score,
        'facilitiesScore': facilities_score,
        'locationScore': location_score,
        'serviceScore': service_score,
        'imageUrl': image_url,
        'imageUrls': image_urls,
        'buttonContent': button_content,
        'minPrice': safe_str(min_price) if min_price is not None else '',
        'avgPrice': safe_str(avg_price) if avg_price is not None else '',
        'maxPrice': safe_str(max_price) if max_price is not None else '',
        'displayPrices': ', '.join(display_prices[:3]),
        'roomNames': ', '.join(room_names[:3]),
        'checkInDates': ', '.join(list(set(check_in_dates))[:2]),
        'checkOutDates': ', '.join(list(set(check_out_dates))[:2]),
        'amenities': amenities_str,
    }

def normalize(input_path, output_path):
    seen = set()
    rows = []
    with open(input_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Extract all fields
            fields = extract_all_fields(obj)
            
            # Use hotelId as key for deduplication
            hotel_id = fields.get('hotelId', '')
            key = hotel_id if hotel_id else f"{fields.get('hotelName', '')}::{fields.get('cityId', '')}"
            
            if key in seen:
                continue
            seen.add(key)
            
            rows.append(fields)

    # Define fieldnames (30 fields + amenities = 31 fields)
    fieldnames = [
        'hotelId', 'hotelName',
        'star', 'starType', 'categoryName', 'categoryId',
        'cityId', 'cityName', 'address', 'positionDesc', 
        'latitude', 'longitude',
        'commentScore', 'commentDescription', 'commenterNumber', 'fullRating',
        'cleanlinessScore', 'facilitiesScore', 'locationScore', 'serviceScore',
        'imageUrl', 'imageUrls', 'buttonContent',
        'minPrice', 'avgPrice', 'maxPrice', 'displayPrices',
        'roomNames', 'checkInDates', 'checkOutDates',
        'amenities'  # Added amenities field
    ]
    
    # Filter rows to only include fields in fieldnames
    filtered_rows = []
    for r in rows:
        filtered_row = {k: v for k, v in r.items() if k in fieldnames}
        filtered_rows.append(filtered_row)
    
    # write CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as ofh:
        writer = csv.DictWriter(ofh, fieldnames=fieldnames)
        writer.writeheader()
        for r in filtered_rows:
            writer.writerow(r)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Normalize trip JSONL -> CSV with all fields + amenities')
    p.add_argument('--input', '-i', default='trip_hotels_full.jsonl')
    p.add_argument('--output', '-o', default='trip_hotels_normalized.csv')
    args = p.parse_args()
    normalize(args.input, args.output)
    print(f'Done -> {args.output}')
