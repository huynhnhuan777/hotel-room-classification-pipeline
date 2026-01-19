import pandas as pd
from sklearn.model_selection import train_test_split

# 1. Đường dẫn file dữ liệu
DATA_PATH = r"C:\Users\Nhuan\OneDrive - ut.edu.vn\Desktop\SEMESTER_7\DATA MINING\hotel-room-classification-pipeline\splitdata\hotel_data_final.csv"

# 2. Load dữ liệu
df = pd.read_csv(DATA_PATH)

print("Tổng số mẫu:", len(df))
print("Phân bố nhãn room_class:")
print(df['room_class'].value_counts())

# 3. Tách feature và label
X = df.drop(columns=['room_class'])
y = df['room_class']

# 4. Chia Train (70%) và Temp (30%)
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y,
    test_size=0.30,
    random_state=42,
    stratify=y
)

# 5. Chia Validation (15%) và Test (15%)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp,
    test_size=0.50,
    random_state=42,
    stratify=y_temp
)

# 6. Gộp lại thành DataFrame
train_df = pd.concat([X_train, y_train], axis=1)
val_df   = pd.concat([X_val, y_val], axis=1)
test_df  = pd.concat([X_test, y_test], axis=1)

# 7. Lưu file
train_df.to_csv("train.csv", index=False)
val_df.to_csv("val.csv", index=False)
test_df.to_csv("test.csv", index=False)

# 8. Thống kê sau khi chia
print("\n--- KẾT QUẢ CHIA TẬP ---")
print("Train:", train_df.shape)
print("Validation:", val_df.shape)
print("Test:", test_df.shape)

print("\nPhân bố nhãn Train:")
print(train_df['room_class'].value_counts(normalize=True))

print("\nPhân bố nhãn Validation:")
print(val_df['room_class'].value_counts(normalize=True))

print("\nPhân bố nhãn Test:")
print(test_df['room_class'].value_counts(normalize=True))
