import pandas as pd
import numpy as np
import re
import ast
INP = "hotels_detail_output.csv"
OUT = "hotels_hcm_recovered.csv"

def extract_price(price_str):
    if pd.isna(price_str): return None, None
    matches = re.findall(r'[\d\.]+', str(price_str))
    valid = []
    for m in matches:
        clean = m.replace('.', '')
        if clean.isdigit() and len(clean) > 4: 
            valid.append(int(clean))
    if not valid: return None, None
    return min(valid), max(valid)

def clean_country(country_str):
    if pd.isna(country_str): return "Việt Nam"
    try:
        return ast.literal_eval(country_str).get('name', 'Việt Nam')
    except:
        return str(country_str)

def main():
    print(f"⏳ Reading {INP}...")
    try:
        df = pd.read_csv(INP, on_bad_lines='skip', engine='python')
    except FileNotFoundError:
        print(" File not found!"); return

    print(f" Total raw rows: {len(df)}")
    
    is_numeric_status = pd.to_numeric(df['_fetch_status'], errors='coerce').notna()
    
    df_ok = df[is_numeric_status].copy()
    df_shifted = df[~is_numeric_status].copy()
    


    if not df_shifted.empty:
        temp = df_shifted.copy()
        
        df_shifted['name_detail'] = temp['_fetch_status']
        df_shifted['ratingValue'] = temp['_parse_status']
        df_shifted['reviewCount'] = temp['phone']
        df_shifted['priceRange']  = temp['name_detail']
        df_shifted['streetAddress'] = temp['ratingValue']
        df_shifted['_parse_status'] = temp['priceRange']
        

        df_shifted['_fetch_status'] = 200
        df_shifted['addressCountry'] = 'Việt Nam' 

        df_shifted['phone'] = np.nan
        df_shifted['postalCode'] = np.nan

    df_final = pd.concat([df_ok, df_shifted], ignore_index=True)
    
    print(f"🔄 Combined dataset: {len(df_final)} rows")

    

    df_final[['price_min', 'price_max']] = df_final['priceRange'].apply(
        lambda x: pd.Series(extract_price(x))
    )
    df_final['price_avg'] = (df_final['price_min'] + df_final['price_max']) / 2
    

    df_final['final_name'] = df_final['name_detail'].fillna(df_final['hotel_name'])
    

    df_final['addressCountry'] = df_final['addressCountry'].apply(clean_country)


    for col in ['ratingValue', 'reviewCount', 'lat', 'lng']:
        df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

    keep_cols = [
        'final_name', 'detail_url', '_parse_status',
        'ratingValue', 'reviewCount', 
        'price_min', 'price_max', 'price_avg',
        'streetAddress', 'addressLocality', 'addressCountry',
        'lat', 'lng', 'amenities'
    ]
    
    # Only keep columns that exist
    final_cols = [c for c in keep_cols if c in df_final.columns]
    df_export = df_final[final_cols]
    
    df_export = df_export.drop_duplicates(subset=['detail_url'])
    
    df_export.to_csv(OUT, index=False, encoding='utf-8-sig')
    print(df_export[['final_name', 'price_avg', 'ratingValue']].head())

if __name__ == "__main__":
    main()