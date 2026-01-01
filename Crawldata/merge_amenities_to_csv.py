#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để merge amenities vào file CSV hiện có
"""
import csv
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# File paths
AMENITIES_JSON = "hotels_amenities.json"
CSV_INPUT = "trip_hotels_normalized.csv"  # File CSV hiện có
CSV_OUTPUT = "trip_hotels_normalized_with_amenities.csv"  # File mới với amenities

def load_amenities():
    """Load amenities từ file JSON"""
    if not os.path.exists(AMENITIES_JSON):
        print(f"File {AMENITIES_JSON} not found!")
        print("Please run crawl_amenities.py first to crawl amenities.")
        return {}
    
    with open(AMENITIES_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def merge_amenities_to_csv():
    """Merge amenities vào CSV"""
    # Load amenities
    amenities_dict = load_amenities()
    
    if not amenities_dict:
        print("No amenities data found!")
        return
    
    print(f"Loaded amenities for {len(amenities_dict)} hotels")
    
    # Check if input CSV exists
    if not os.path.exists(CSV_INPUT):
        print(f"File {CSV_INPUT} not found!")
        return
    
    # Read CSV
    rows = []
    with open(CSV_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        # Add amenities column if not exists
        if 'amenities' not in fieldnames:
            fieldnames = list(fieldnames) + ['amenities']
        
        for row in reader:
            # Try different possible column names for hotel ID
            hotel_id = row.get('hotelId', '') or row.get('hotellId', '') or row.get('hotel_id', '')
            
            # Get amenities for this hotel
            if hotel_id and hotel_id in amenities_dict:
                amenities = amenities_dict[hotel_id]
                if isinstance(amenities, list):
                    amenities_str = ', '.join(str(a) for a in amenities if a)
                else:
                    amenities_str = str(amenities) if amenities else ''
            else:
                amenities_str = ''
            
            row['amenities'] = amenities_str
            rows.append(row)
    
    # Write updated CSV
    with open(CSV_OUTPUT, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # Statistics
    hotels_with_amenities = sum(1 for r in rows if r.get('amenities', '').strip())
    print(f"\n{'='*80}")
    print("MERGE COMPLETED!")
    print(f"{'='*80}")
    print(f"Total hotels in CSV: {len(rows)}")
    print(f"Hotels with amenities: {hotels_with_amenities}")
    print(f"Hotels without amenities: {len(rows) - hotels_with_amenities}")
    print(f"\nUpdated file: {CSV_OUTPUT}")

if __name__ == '__main__':
    merge_amenities_to_csv()

