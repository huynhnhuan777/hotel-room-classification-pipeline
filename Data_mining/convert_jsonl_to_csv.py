import pandas as pd
import json

# Đường dẫn file JSONL (thay đổi nếu cần)
jsonl_file = 'hotels_complete_hcm.jsonl'
csv_file = 'hotels_complete_hcm.csv'

# Đọc file JSONL và chuyển thành list of dicts
data = []
with open(jsonl_file, 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line.strip()))

# Chuyển list of dicts thành DataFrame
df = pd.DataFrame(data)

# Xuất ra file CSV (với encoding UTF-8 để hỗ trợ tiếng Việt)
df.to_csv(csv_file, index=False, encoding='utf-8-sig')

print(f"Đã chuyển đổi thành công! File CSV: {csv_file}")