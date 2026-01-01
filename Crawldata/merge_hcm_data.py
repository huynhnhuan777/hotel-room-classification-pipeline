#!/usr/bin/env python3
"""
Merge dữ liệu mới từ trip_hotels_hcm_more.jsonl vào trip_hotels_full.jsonl
và tạo lại file CSV normalized.
"""
import json
import os

EXISTING_JSONL = "trip_hotels_full.jsonl"
NEW_JSONL = "trip_hotels_hcm_more.jsonl"
MERGED_JSONL = "trip_hotels_full.jsonl"
BACKUP_JSONL = "trip_hotels_full_backup.jsonl"

def load_hotel_ids(filepath):
    """Load hotel IDs from JSONL file"""
    ids = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    hotel_id = None
                    if 'hotelInfo' in obj:
                        summary = obj['hotelInfo'].get('summary', {})
                        hotel_id = summary.get('hotelId')
                    elif 'hotelId' in obj:
                        hotel_id = obj['hotelId']
                    if hotel_id:
                        ids.add(str(hotel_id))
                except:
                    continue
    return ids

def merge_files():
    """Merge new hotels into existing file"""
    if not os.path.exists(NEW_JSONL):
        print(f"File {NEW_JSONL} not found!")
        return
    
    # Load existing IDs
    existing_ids = load_hotel_ids(EXISTING_JSONL)
    print(f"Existing hotels: {len(existing_ids)}")
    
    # Load new hotels
    new_hotels = []
    new_ids = set()
    with open(NEW_JSONL, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                hotel_id = None
                if 'hotelInfo' in obj:
                    summary = obj['hotelInfo'].get('summary', {})
                    hotel_id = summary.get('hotelId')
                elif 'hotelId' in obj:
                    hotel_id = obj['hotelId']
                
                if hotel_id:
                    hid = str(hotel_id)
                    if hid not in existing_ids and hid not in new_ids:
                        new_ids.add(hid)
                        new_hotels.append(obj)
            except Exception as e:
                print(f"Error parsing line: {e}")
                continue
    
    print(f"New unique hotels to add: {len(new_hotels)}")
    
    if len(new_hotels) == 0:
        print("No new hotels to add!")
        return
    
    # Backup existing file
    if os.path.exists(EXISTING_JSONL):
        import shutil
        shutil.copy2(EXISTING_JSONL, BACKUP_JSONL)
        print(f"Backed up existing file to {BACKUP_JSONL}")
    
    # Append new hotels to existing file
    with open(EXISTING_JSONL, 'a', encoding='utf-8') as f:
        for hotel in new_hotels:
            f.write(json.dumps(hotel, ensure_ascii=False) + '\n')
    
    print(f"Successfully merged {len(new_hotels)} new hotels into {EXISTING_JSONL}")
    print(f"Total hotels now: {len(existing_ids) + len(new_hotels)}")

if __name__ == '__main__':
    merge_files()







