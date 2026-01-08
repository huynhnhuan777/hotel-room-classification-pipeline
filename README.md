# hotel-room-classification-pipeline
Data pipeline thu thập và làm sạch dữ liệu phòng khách sạn TP HCM
# 🧹 Hotel Room Data Cleaning Pipeline

Pipeline tập trung vào:
- Chuẩn hóa tên cột
- Làm sạch dữ liệu số
- Làm sạch tiện nghi
- Lọc dữ liệu hợp lệ
- Loại trùng và nhiễu cơ bản

---

## 📂 Dữ liệu đầu vào
- **File**: `merged_all_data.csv`
- **Nguồn**: Booking, Mytour, iVIVU và các nguồn khác
- **Quy mô ban đầu**: ~15.000 dòng

---

## 🧱 Schema dữ liệu đầu ra

Dataset cuối cùng chỉ giữ **11 cột chuẩn**:

| Cột | Mô tả |
|---|---|
| `source` | Nguồn dữ liệu (booking / mytour / ivivu / other) |
| `hotel_link` | Link khách sạn |
| `hotel_name` | Tên khách sạn |
| `room_name_original` | Tên phòng gốc |
| `room_class` | Hạng phòng |
| `bed_desc` | Mô tả giường |
| `bed_class` | Loại giường |
| `area_m2` | Diện tích phòng (m²) |
| `max_people` | Số người tối đa |
| `final_price` | Giá phòng (VNĐ) |
| `facilities_cleaned` | Danh sách tiện nghi đã làm sạch |

---

## 🔄 Các bước xử lý 

### 1️⃣ Load dữ liệu
Đọc file CSV tổng hợp chứa dữ liệu crawl ban đầu.

---

### 2️⃣ Chuẩn hóa tên cột
- Chuyển toàn bộ tên cột về chữ thường
- Thay khoảng trắng bằng dấu `_`
- Loại bỏ các cột bị trùng tên

Mục đích: đảm bảo schema thống nhất trước khi xử lý.

---

### 3️⃣ Đổi tên cột về schema chuẩn
Một số cột crawl có tên khác nhau được đổi lại để thống nhất ý nghĩa:

| Tên cột gốc | Tên cột mới |
|---|---|
| `room_type` | `room_name_original` |
| `area_m2_cleaned` | `area_m2` |
| `total_guests` | `max_people` |
| `bed_type` | `bed_desc` |

---

### 4️⃣ Xác định nguồn dữ liệu (`source`)
Nguồn dữ liệu được suy ra từ `hotel_link`:
- Chứa `booking.com` → `booking`
- Chứa `mytour.vn` → `mytour`
- Chứa `ivivu.com` → `ivivu`
- Các trường hợp còn lại → `other`

---

### 5️⃣ Làm sạch dữ liệu số

#### 💰 Giá phòng (`final_price`)
- Xóa toàn bộ ký tự không phải số (ký hiệu tiền tệ, dấu chấm, dấu phẩy, chữ)
- Chuyển giá trị về kiểu số
#### 💰 Giá phòng (`final_price`)
- Xóa toàn bộ ký tự không phải số (ký hiệu tiền tệ, dấu chấm, dấu phẩy, chữ)
- Chuyển giá trị về kiểu số
