# Bike Picking Module

Module này cung cấp giải pháp tùy chỉnh quy trình Picking (lấy hàng) cho ngành bán lẻ xe đạp, được xây dựng theo tài liệu yêu cầu Case Study.

## Tính năng chính (Features)

1. **Quản lý trạng thái Custom Picking (`picking_status`)**
   - Hỗ trợ các trạng thái đặc thù của quy trình chuẩn bị xe đạp: *Waiting Picking -> Picking -> Picked -> Assembly -> PDI -> Ready Pickup*.
   - Trạng thái `picking_status` được hiển thị song song với trạng thái chuẩn (`state`) của Odoo để tiện theo dõi.

2. **Định danh Serial/Số khung bắt buộc**
   - Các sản phẩm được đánh dấu là Xe (`is_bike = True`) bắt buộc nhân viên kho phải quét/gán số Serial ở cấp chi tiết dòng hàng (`stock.move.line`) trước khi hoàn thành Picking.
   - Ngăn chặn lỗi khi nhấn "Complete Picking" mà chưa gán Serial.

3. **Phân luồng tự động (Auto-Routing)**
   - Nhận diện đơn hàng có chứa xe (`is_bike_order`).
   - Dựa vào thuộc tính `is_assembly_required` trên Product Template để tự động luân chuyển trạng thái sang **Assembly** (Cần lắp ráp) hoặc **PDI** (Không cần lắp ráp) sau khi lấy hàng xong.

## Hướng dẫn sử dụng (User Guide)

### 1. Cấu hình sản phẩm (Product Configuration)
- Truy cập form **Product Template** của một sản phẩm xe đạp.
- Trong tab **Inventory**, đánh dấu vào ô `Is Bike`.
- Nếu xe cần lắp ráp sau khi xuất kho, đánh dấu thêm vào ô `Is Assembly Required`.

### 2. Quy trình Picking cho Kho (Warehouse Workflow)
- Khi Sales Order được Confirm, một phiếu Picking mới tự động sinh ra với trạng thái ban đầu là `Waiting Picking`.
- Nhân viên kho mở phiếu Picking, nhấn **Start Picking** để chuyển sang trạng thái đang lấy hàng (`Picking`).
- Tiến hành xuất/gán số Serial Number cho các dòng sản phẩm Xe.
- Sau khi kiểm tra đủ hàng và số Serial, nhấn **Complete Picking**.
- Hệ thống tự động kiểm tra và chuyển tiếp Picking sang `Assembly`, `PDI` hoặc `Picked` tương ứng với sản phẩm bên trong.

## Thông tin kỹ thuật (Technical Info)
- **Models modified:** `product.template`, `stock.picking`.
- Tương thích với luồng chuẩn của Odoo (hoạt động phía trên lớp giữ chỗ - Reservation mặc định của hệ thống).
