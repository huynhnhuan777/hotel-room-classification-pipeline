# Hotel Room Data Cleaning Pipeline

Script này dùng để **làm sạch & chuẩn hoá dữ liệu phòng khách sạn** từ nhiều nguồn (Booking, Mytour, iVivu) phục vụ bài toán **phân loại hạng phòng**.

---

## Input

```
mergedata/merged_all_data.csv
```

---

## Output

```
preprocessing/cleaned_rooms.csv
```

---

## Các bước xử lý chính

### 1. Chuẩn hoá tên cột

- Chuyển về lowercase, thay dấu cách bằng `_`.

### 2. Đổi tên field về chuẩn

| Tên cũ          | Tên mới            |
| --------------- | ------------------ |
| room_type       | room_name_original |
| bed_type        | bed_desc           |
| area_m2_cleaned | area_m2            |
| total_guests    | max_people         |

---

### 3. Xác định nguồn dữ liệu

Sinh cột `source` dựa vào `hotel_link`:

| URL chứa    | source  |
| ----------- | ------- |
| booking.com | booking |
| mytour.vn   | mytour  |
| ivivu.com   | ivivu   |

---

### 4. Làm sạch dữ liệu số

| Cột         | Cách xử lý            |
| ----------- | --------------------- |
| area_m2     | Lấy số thực từ chuỗi  |
| max_people  | Ép kiểu numeric       |
| final_price | Xoá ký tự, chỉ giữ số |

---

### 5. Làm sạch tiện nghi

Chuẩn hoá chữ thường, xoá ký tự đặc biệt.

---

### 6. Suy ra `bed_class` từ `bed_desc` (chỉ khi bị thiếu)

Chỉ xử lý khi `bed_class` là NaN hoặc rỗng.

| bed_desc chứa          | bed_class |
| ---------------------- | --------- |
| bunk, family, 3 giường | family    |
| king                   | king      |
| queen                  | queen     |
| 2 giường đơn, twin     | twin      |
| giường đôi, double     | double    |
| giường đơn, single     | single    |
| còn lại                | unknown   |

---

### 7. Lọc dữ liệu hợp lệ

Xóa dòng thiếu:

- `room_name_original`
- `final_price`
- `area_m2`
- `max_people`

Chỉ giữ phòng có `final_price > 0`.
