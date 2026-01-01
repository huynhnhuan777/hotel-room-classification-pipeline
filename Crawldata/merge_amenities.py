#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để merge amenities vào file JSONL chính
"""
import json
import os

INPUT_JSONL = "trip_hotels_full.jsonl"
AMENITIES_JSON = "hotels_amenities.json"
OUTPUT_JSONL = "trip_hotels_full.jsonl"  # Ghi đè file gốc

def load_amenities():
    """Load amenities từ file"""
    if os.path.exists(AMENITIES_JSON):
        with open(AMENITIES_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def merge_amenities():
    """Merge amenities vào hotel data"""
    amenities_dict = load_amenities()
    
    if not amenities_dict:
        print("No amenities file found!")
        return
    
    print(f"Loaded amenities for {len(amenities_dict)} hotels")
    
    updated_count = 0
    hotels_updated = []
    
    # Đọc và merge
    with open(INPUT_JSONL, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                obj = json.loads(line)
                hotel_info = obj.get('hotelInfo', {})
                summary = hotel_info.get('summary', {})
                hotel_id = str(summary.get('hotelId', ''))
                
                # Thêm amenities vào hotelInfo
                if hotel_id in amenities_dict:
                    amenities = amenities_dict[hotel_id]
                    if amenities:
                        # Thêm vào hotelInfo
                        if 'amenities' not in hotel_info:
                            hotel_info['amenities'] = amenities
                            updated_count += 1
                
                hotels_updated.append(obj)
                
            except Exception as e:
                print(f"Error processing line: {e}")
                continue
    
    # Ghi lại file
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        for hotel in hotels_updated:
            f.write(json.dumps(hotel, ensure_ascii=False) + '\n')
    
    print(f"\nMerged amenities into {updated_count} hotels")
    print(f"Updated file: {OUTPUT_JSONL}")

if __name__ == '__main__':
    merge_amenities()


