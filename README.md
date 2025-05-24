## 🔗 Bảng Quan Hệ Giữa Các Bảng

| Bảng chính         | Bảng liên quan         | Kiểu quan hệ        | Khóa chính             | Khóa ngoại                          | Mô tả                                                         |
|--------------------|------------------------|---------------------|-------------------------|--------------------------------------|---------------------------------------------------------------|
| `medicines`        | `medicine_batch_items` | 1 — N (one-to-many) | `medicines.id`          | `medicine_batch_items.medicine_id`  | Một loại thuốc có thể xuất hiện trong nhiều lô thuốc           |
| `medicine_batches` | `medicine_batch_items` | 1 — N (one-to-many) | `medicine_batches.id`   | `medicine_batch_items.batch_id`     | Một lô thuốc có thể chứa nhiều loại thuốc                      |
| `medicines`        | `inventory_logs`       | 1 — N (one-to-many) | `medicines.id`          | `inventory_logs.medicine_id`        | Lưu lịch sử nhập/xuất thuốc                                   |
| `medicine_batches` | `inventory_logs`       | 1 — N (one-to-many) | `medicine_batches.id`   | `inventory_logs.batch_id`           |                                                               |
| `users`            | `inventory_logs`       | 1 — N (one-to-many) | `users.id`              | `inventory_logs.performed_by`       | Ai thực hiện hành động nhập/xuất                              |
| `patients`         | `prescriptions`        | 1 — N (one-to-many) | `patients.id`           | `prescriptions.patient_id`          | Một bệnh nhân có nhiều đơn thuốc                              |
| `users`            | `prescriptions`        | 1 — N (one-to-many) | `users.id`              | `prescriptions.doctor_id`           | Bác sĩ kê đơn                                                 |
| `prescriptions`    | `prescription_items`   | 1 — N (one-to-many) | `prescriptions.id`      | `prescription_items.prescription_id`| Một đơn thuốc gồm nhiều dòng thuốc                            |
| `medicines`        | `prescription_items`   | 1 — N (one-to-many) | `medicines.id`          | `prescription_items.medicine_id`    | Mỗi dòng đơn thuốc chứa một loại thuốc                        |
| `medicine_batches` | `prescription_items`   | 1 — N (one-to-many) | `medicine_batches.id`   | `prescription_items.batch_id`       | Mỗi dòng đơn thuốc ghi rõ thuốc lấy từ lô nào                 |

### 💡 Ghi chú:
- `medicine_batch_items` là bảng trung gian giữa `medicines` và `medicine_batches` → quan hệ nhiều-nhiều.
- Các bảng `*_items`, `*_logs`, `*_batches` đều có khóa ngoại với `ondelete='CASCADE'` để hỗ trợ xóa dữ liệu liên quan khi cần.
