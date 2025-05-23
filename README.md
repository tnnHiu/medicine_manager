# Quan hệ giữa các bảng trong hệ thống quản lý thuốc

| Quan hệ                              | Kiểu | Diễn giải                                                  |
| ------------------------------------ | ---- | ---------------------------------------------------------- |
| `User` → `Prescription`              | 1:N  | Một bác sĩ có thể kê nhiều đơn thuốc                       |
| `User` → `InventoryLog`              | 1:N  | Một người dùng thực hiện nhiều thay đổi kho thuốc          |
| `Patient` → `Prescription`           | 1:N  | Một bệnh nhân có thể có nhiều đơn thuốc                    |
| `Medicine` → `PrescriptionItem`      | 1:N  | Một loại thuốc có thể xuất hiện nhiều lần trong đơn thuốc  |
| `Medicine` → `InventoryLog`          | 1:N  | Một thuốc có thể có nhiều lịch sử thay đổi kho             |
| `Prescription` → `PrescriptionItem`  | 1:N  | Một đơn thuốc có nhiều dòng kê thuốc cụ thể                |

## 🔹 1. User (Bác sĩ, Quản trị, Dược sĩ)

**Quan hệ 1-N với `prescriptions`:**

- Một bác sĩ (`users.role = 'doctor'`) có thể kê nhiều đơn thuốc.  
- Mỗi đơn thuốc chỉ thuộc về một bác sĩ.  
→ `prescriptions.doctor_id → users.id`

**Quan hệ 1-N với `inventory_logs`:**

- Một dược sĩ/quản trị viên có thể ghi nhiều lịch sử kho thuốc.  
→ `inventory_logs.performed_by → users.id`

---

## 🔹 2. Patient (Bệnh nhân)

**Quan hệ 1-N với `prescriptions`:**

- Một bệnh nhân có thể có nhiều đơn thuốc.  
- Mỗi đơn thuốc chỉ gắn với một bệnh nhân.  
→ `prescriptions.patient_id → patients.id`

---

## 🔹 3. Medicine (Thuốc)

**Quan hệ 1-N với `prescription_items`:**

- Một loại thuốc có thể xuất hiện trong nhiều dòng đơn thuốc.  
- Mỗi dòng kê thuốc chỉ tham chiếu đến 1 loại thuốc.  
→ `prescription_items.medicine_id → medicines.id`

**Quan hệ 1-N với `inventory_logs`:**

- Mỗi loại thuốc có thể có nhiều lần thay đổi kho (nhập, cấp phát…).  
→ `inventory_logs.medicine_id → medicines.id`

---

## 🔹 4. Prescription (Đơn thuốc)

**Quan hệ N-1 với `users` và `patients`:**

- Mỗi đơn thuốc gắn với 1 bệnh nhân và 1 bác sĩ.

**Quan hệ 1-N với `prescription_items`:**

- Một đơn thuốc có nhiều dòng kê thuốc.  
→ `prescription_items.prescription_id → prescriptions.id`

---

## 🔹 5. PrescriptionItem (Chi tiết đơn thuốc)

- **N-1 với `prescriptions`**: thuộc về một đơn thuốc.  
- **N-1 với `medicines`**: kê 1 loại thuốc.

---

## 🔹 6. InventoryLog (Nhật ký kho thuốc)

- **N-1 với `medicines`**: thay đổi kho của 1 loại thuốc.  
- **N-1 với `users`**: do một người dùng thực hiện (thường là dược sĩ hoặc quản trị viên).
