# Quan hệ giữa các bảng trong hệ thống quản lý thuốc

| Quan hệ                              | Kiểu | Diễn giải                                                  |
| ------------------------------------ | ---- | ---------------------------------------------------------- |
| `User` → `Prescription`              | 1:N  | Một bác sĩ có thể kê nhiều đơn thuốc                       |
| `User` → `InventoryLog`              | 1:N  | Một người dùng thực hiện nhiều thay đổi kho thuốc          |
| `Patient` → `Prescription`           | 1:N  | Một bệnh nhân có thể có nhiều đơn thuốc                    |
| `Medicine` → `PrescriptionItem`      | 1:N  | Một loại thuốc có thể xuất hiện nhiều lần trong đơn thuốc  |
| `Medicine` → `InventoryLog`          | 1:N  | Một thuốc có thể có nhiều lịch sử thay đổi kho             |
| `Prescription` → `PrescriptionItem`  | 1:N  | Một đơn thuốc có nhiều dòng kê thuốc cụ thể                |
