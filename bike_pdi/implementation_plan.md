# Kế hoạch triển khai Module Lắp ráp xe đạp (Bike Workshop - Assembly)

Mục tiêu: Xây dựng module `bike_workshop` để quản lý quá trình lắp ráp xe đạp sau khi lấy hàng (Picking) hoàn tất, đảm bảo Technician thực hiện đúng checklist kỹ thuật.

## User Review Required

- **Tự động sinh Assembly Task**: Một đơn hàng (Picking) có thể có nhiều xe. Hệ thống sẽ quét các dòng chi tiết `stock.move.line` của xe đạp trong phiếu Picking sau khi hoàn thành. Với mỗi chiếc xe (mỗi Serial number), hệ thống sẽ tạo một phiếu Assembly Task độc lập (1 xe/serial = 1 task).
- **Tái sử dụng trường `is_assembly_required`**: Trong module `bike_picking` chúng ta đã có trường này để cấu hình xe cần lắp ráp. Do đó, tôi sẽ dùng luôn trường này thay vì tạo mới trường `requires_assembly` như tài liệu.

## Open Questions

> [!WARNING]
> Vui lòng xác nhận các câu hỏi sau trước khi tôi tiến hành lập trình:

1. **Liên kết với Picking**: Chúng ta có nên thêm trường `picking_id` vào phiếu Assembly Order để nhân viên dễ dàng tra cứu ngược lại phiếu xuất kho và luồng cung ứng không? (Tôi đề xuất CÓ).
2. **Trạng thái của Assembly Order**: Tài liệu quy định các state gồm `draft, assigned, in_progress, completed, rework, pdi, ready_pickup`. Tuy nhiên, các trạng thái `pdi` và `ready_pickup` có vẻ thuộc về luồng của PDI sẽ làm ở Phase tiếp theo (mục 4.6). Chúng ta có nên chỉ giữ vòng đời Assembly Order đến trạng thái `completed` (và `rework`), sau đó khi hoàn tất sẽ kích hoạt sinh phiếu PDI mới cho module sau này không?
3. **Cấu hình Checklist theo Category**: Tôi đề xuất tạo model `bike.assembly.template` được link trực tiếp với `product.category`. Khi hệ thống tạo Assembly Order, nó sẽ dò Category của xe và tự động copy các công việc vào phiếu. Bạn đồng ý với kiến trúc này chứ?
4. **Tên module**: Tài liệu sử dụng `bike.assembly.order` cho data và `Bike Workshop` cho Menu. Tôi sẽ đặt tên module là `bike_workshop` để tiện mở rộng (như sửa chữa/service) trong tương lai. Bạn đồng ý không?

## Proposed Changes

Tất cả các thay đổi sẽ nằm trong thư mục `c:\Users\phanp\Documents\odoo_edu\demo_odoo\custom_addons\bike_workshop`. Đồng thời sẽ bổ sung logic vào module `bike_picking` hiện có.

### 1. Models (Cấu trúc dữ liệu `bike_workshop`)

#### [NEW] `models/assembly_template.py`
- Model `bike.assembly.template`:
  - `name`: Tên template (VD: Road Bike Checklist)
  - `category_id`: Many2one tới `product.category`
  - `line_ids`: One2many tới `bike.assembly.template.line`
- Model `bike.assembly.template.line`:
  - `name`: Tên công việc (VD: Install front wheel, Brake adjustment)
  - `sequence`: Thứ tự ưu tiên

#### [NEW] `models/assembly_order.py`
- Model `bike.assembly.order`:
  - `name`: Số phiếu tự động (Sequence ASM0001...)
  - `picking_id`: Many2one (`stock.picking`)
  - `sales_order_id`: Many2one (`sale.order`)
  - `customer_id`: Many2one (`res.partner`)
  - `product_id`: Many2one (`product.product` - Xe đạp)
  - `serial_id`: Many2one (`stock.lot` - Frame serial)
  - `technician_id`: Many2one (`res.users` - Technician)
  - `checklist_template_id`: Many2one (`bike.assembly.template`)
  - `start_time`, `finish_time`: Datetime
  - `state`: Selection (`draft`, `assigned`, `in_progress`, `completed`, `rework`, `pdi`, `ready_pickup`)
  - `checklist_line_ids`: One2many tới `bike.assembly.checklist.line`
  - Các hàm Action: `action_assign()`, `action_start_assembly()`, `action_complete_assembly()`, `action_send_pdi()`.
  - Logic Validation: Kiểm tra tất cả checklist phải được đánh dấu và serial phải tồn tại trước khi cho phép Complete.

#### [NEW] `models/assembly_checklist_line.py`
- Model `bike.assembly.checklist.line`:
  - `order_id`: Many2one tới `bike.assembly.order`
  - `task_name`: Tên nhiệm vụ
  - `completed`: Boolean (Checkbox hoàn thành)
  - `notes`: Text (Ghi chú nếu có lỗi)
  - `completed_by`: Many2one (`res.users`)
  - `completed_at`: Datetime

### 2. Sửa đổi Module `bike_picking`

#### [MODIFY] `../bike_picking/models/stock_picking.py`
- Ghi đè hoặc mở rộng action `action_complete_picking()`: Sau khi kho nhấn Complete, tìm tất cả các xe có `is_assembly_required = True`. Dùng thông tin `stock.move.line` (đã có Serial) để tự động gọi hàm tạo `bike.assembly.order` bên module `bike_workshop`.

### 3. Views (Giao diện UI)

#### [NEW] `views/assembly_order_views.xml`
- Tạo **Menu chính**: `Bike Workshop`
- Sub-menus: `Assembly Queue`, `My Assembly`, `Completed`.
- **Kanban view**: Kéo thả trạng thái công việc (Assigned -> In Progress -> Completed -> Rework...).
- **Form view**:
  - Giao diện Header: Số phiếu, Trạng thái (Statusbar), Các nút bấm Start/Complete/Assign.
  - Tab Checklist: Hiển thị tree view có checkbox để click trực tiếp `completed`.
  - Tab Notes: Chứa ghi chú Rework.

#### [NEW] `views/assembly_template_views.xml`
- Menu: `Configuration -> Assembly Checklist`.
- Giao diện quản lý các Template và công việc con.

#### [NEW] `data/ir_sequence.xml`
- Định nghĩa sequence tự động tăng cho Assembly Order (Ví dụ: `ASM-%(y)s-%(month)s-0001`).

### 4. Security (Phân quyền truy cập)

#### [NEW] `security/security.xml`
- Tạo groups: `group_workshop_technician`, `group_workshop_manager`.
#### [NEW] `security/ir.model.access.csv`
- Cấp quyền đọc/ghi/tạo/xóa cho các groups tương ứng (Technician chỉ thấy task của mình và chuyển trạng thái, Manager thấy tất cả và được Reassign).

## Verification Plan

### Automated Tests / Manual Verification
### Manual Verification
- Deploy to test environment and test end-to-end workflow: Picking -> Task created -> Assigned -> Started -> Completed.
- Ensure only required fields are editable when task is completed.
- Check user group permissions.

---

# [PDI Feature] Tính năng Kiểm định trước khi giao xe (PDI)

# [PDI Feature] Tách tính năng Kiểm định (PDI) thành Module độc lập

Theo yêu cầu mới, tính năng PDI sẽ được thiết kế thành một module hoàn toàn độc lập (ví dụ: `bike_pdi`), tách rời khỏi `bike_workshop`. Điều này giúp hệ thống module hóa tốt hơn và rõ ràng về mặt nghiệp vụ.

> [!WARNING]
> ## User Review Required
> Vui lòng xem qua kế hoạch tách module dưới đây. Tôi sẽ dọn dẹp lại module `bike_workshop` (xóa các file PDI vừa tạo) và chuyển toàn bộ sang module `bike_pdi` mới.
> 
> **Câu hỏi:** Module mới sẽ có tên kỹ thuật là `bike_pdi`. Nó sẽ phụ thuộc (`depends`) vào `bike_workshop` (để kế thừa sự kiện hoàn tất Lắp ráp) và `stock` (để lấy sự kiện xuất kho). Bạn đồng ý với kiến trúc này chứ?

## Proposed Changes

---

### Tách và tạo mới Module `bike_pdi`

#### [NEW] `custom_addons/bike_pdi/__init__.py` & `__manifest__.py`
Tạo thông tin khai báo cho module mới. Cấu hình `depends`: `['base', 'stock', 'sale_management', 'bike_workshop']`.

#### [NEW] `custom_addons/bike_pdi/models/`
Chuyển toàn bộ các file core sang module mới:
- `pdi_template.py`: Quản lý PDI Template.
- `pdi_order.py`: Quản lý phiếu PDI và luồng xử lý Pass/Fail.
- `sale_order.py`: Quản lý trường `pdi_status`.
- `stock_picking.py`: Hook `button_validate` để chặn giao hàng và `_action_done` để sinh PDI cho xe không cần lắp ráp.
- `assembly_order.py`: Kế thừa `bike.assembly.order` từ module workshop, override hàm `action_complete_assembly` để tự động sinh phiếu PDI khi lắp ráp xong.

#### [NEW] `custom_addons/bike_pdi/views/` & `security/` & `data/`
- Chuyển `pdi_template_views.xml`, `pdi_order_views.xml`, `sale_order_views.xml`.
- Tạo Root Menu riêng cho PDI (Kiểm định) không nằm trong Workshop nữa.
- Chuyển `ir.sequence`, `ir.model.access.csv`, `security_rules.xml`.

---

### Dọn dẹp Module `bike_workshop` (Revert)

#### [MODIFY] `models/stock_picking.py` & `models/assembly_order.py`
Xóa bỏ các đoạn code tự động sinh phiếu PDI và logic liên quan đến PDI mà tôi vừa thêm vào ở bước trước.

#### [DELETE] Các tệp tin PDI đã tạo
Xóa `pdi_template.py`, `pdi_order.py`, `sale_order.py` và các file view/security tương ứng khỏi `bike_workshop`. Cập nhật lại `__manifest__.py` và `__init__.py`.

## Verification Plan

### Automated Tests
- Cài đặt mới module `bike_pdi` trên Odoo 19.

### Manual Verification
- Test luồng 1 (Có lắp ráp): Picking -> Lắp ráp (Workshop) hoàn thành -> Tự động sinh PDI bên module Kiểm định -> Pass PDI -> Giao hàng.
- Test luồng 2 (Không lắp ráp): Picking -> Tự động sinh PDI -> Pass PDI -> Giao hàng.
- Test chặn giao hàng khi chưa Pass PDI.
