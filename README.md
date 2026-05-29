### Odoo Custom Quy trình bán hàng cho Công ty TNHH EcoBike
<strong>Môn học: ERP Mã nguồn mở

Thông tin thành viên nhóm E</strong>

| Họ và tên | MSSV |
|---|---|
| Nguyễn Thuỵ Minh Anh | 31231025284 |
| Đặng Nguyễn Gia Hân | 31231022523 |
| Nguyễn Hoàng Như Ngọc | 31231020862 |
| Phan Thanh Phước | 31231020195 |
| Đỗ Dương Thảo Trúc | 31231024111 |

---
<strong>Giới thiệu</strong>

Bộ module Odoo tùy chỉnh dành cho quy trình bán hàng và dịch vụ xe đạp EcoBike. Repository này bao gồm các module phục vụ báo giá bán xe đạp, quản lý thành viên, xử lý giao nhận (Picking), lắp ráp, kiểm định (PDI), đóng gói, bảo hành, phiếu sửa chữa và mô phỏng phát hành hóa đơn điện tử.

---

<strong>Danh sách Module</strong>

| Module | Chức năng | Phụ thuộc chính |
| --- | --- | --- |
| `bicycle_membership` | Quản lý hạng thành viên, điểm tích lũy, giảm giá thành viên, kiểm tra thông tin liên hệ và tính toán cấp độ thành viên. | `base`, `sale` |
| `bike_sales_quotation` | Quản lý lý do mất báo giá, quy trình chỉnh sửa báo giá, cron tự động xử lý báo giá thất bại và áp dụng giảm giá theo hạng thành viên trên dòng báo giá. | `sale`, `bicycle_membership` |
| `bike_sales_order` | Tùy chỉnh đơn bán hàng và mở rộng trường thời hạn bảo hành sản phẩm. | `sale`, `sale_management`, `sale_stock` |
| `bike_picking` | Quản lý trạng thái giao nhận dành riêng cho xe đạp, đánh dấu sản phẩm xe đạp, kiểm tra số serial/frame và điều hướng sang Assembly hoặc PDI. | `stock`, `sale_management` |
| `bike_assembly` | Quản lý lệnh lắp ráp, phân công kỹ thuật viên, checklist lắp ráp và tự động tạo công việc lắp ráp từ phiếu Picking xe đạp. | `base`, `stock`, `sale_management`, `bike_picking` |
| `bike_pdi` | Quản lý kiểm tra trước giao hàng (PDI), checklist kiểm tra, quy trình đạt/rớt kiểm tra, chặn giao hàng khi PDI chưa đạt và xử lý tái kiểm tra. | `base`, `stock`, `sale_management`, `bike_assembly` |
| `bike_packing` | Quản lý đóng gói và checklist đóng gói sau khi hoàn tất PDI/lắp ráp. | `bike_pdi`, `sale`, `stock` |
| `product_warranty` | Bổ sung trường thời hạn bảo hành trên sản phẩm. | `product` |
| `bike_warranty` | Tạo phiếu bảo hành, báo cáo bảo hành, trạng thái hết hạn bảo hành và tự động tạo bảo hành từ đơn bán hàng đã xác nhận. | `sale`, `product`, `product_warranty`, `base_setup` |
| `repair_order` | Quản lý phiếu sửa chữa, gói dịch vụ, checklist sửa chữa, linh kiện thay thế, giảm giá bảo hành/thành viên và liên kết đơn bán hàng để tính phí sửa chữa. | `base`, `mail`, `sale`, `stock`, `account`, `hr`, `bike_warranty`, `bicycle_membership` |
| `account_move_einvoice` | Mô phỏng chức năng phát hành hóa đơn điện tử từ hóa đơn đã xác nhận với mã tra cứu tự động sinh. | `account` |

---

<strong>Quy trình hoạt động chính</strong>

1. Tạo sản phẩm và đánh dấu sản phẩm xe đạp bằng trường `Is Bike`.
2. Với xe cần lắp ráp tại xưởng, bật `Is Assembly Required`.
3. Cấu hình hạng thành viên, mức giảm giá, hệ số tích điểm và số lượt bảo trì miễn phí.
4. Tạo báo giá và đơn bán hàng. Giảm giá thành viên sẽ được áp dụng theo hạng của khách hàng.
5. Xác nhận đơn bán hàng. Điểm tích lũy và thẻ bảo hành có thể được tạo tự động tùy theo cấu hình module.
6. Xử lý phiếu xuất kho (Stock Picking). Các phiếu xuất xe đạp yêu cầu nhập số serial/frame trước khi hoàn tất.
7. Nếu cần lắp ráp, hệ thống sẽ tạo Assembly Order cùng checklist tương ứng từ template phù hợp.
8. Sau khi lắp ráp xong — hoặc ngay sau bước Picking với xe không cần lắp ráp — hệ thống sẽ tạo PDI Order.
9. PDI phải đạt yêu cầu trước khi xác nhận giao hàng. Nếu không đạt, xe có thể được chuyển về quy trình sửa lỗi (Rework).
10. Packing Order được sử dụng sau khi hoàn tất PDI và lắp ráp. Việc giao hàng có thể bị chặn cho đến khi đóng gói hoàn tất.
11. Phiếu bảo hành có thể được in và sử dụng lại trong các phiếu sửa chữa sau này.
12. Phiếu sửa chữa có thể tự động tạo đơn bán hàng liên kết để tính phí công sửa chữa và linh kiện.
13. Các hóa đơn đã xác nhận có thể được phát hành dưới dạng hóa đơn điện tử mô phỏng.

---

<strong>Cài đặt</strong>

1. Clone repository này vào thư mục custom add-ons của Odoo.

```bash
./odoo-bin --addons-path=/path/to/odoo/addons,/path/to/demo_Odoo_Cki
````

2. Khởi động lại Odoo server.
3. Bật Developer Mode.
4. Vào **Apps** → chọn **Update Apps List**.
5. Tìm và cài đặt các module cần thiết.

<strong>Thứ tự cài đặt đề xuất</strong>

1. `bicycle_membership`
2. `bike_sales_quotation`
3. `bike_picking`
4. `bike_assembly`
5. `bike_pdi`
6. `bike_packing`
7. `product_warranty`
8. `bike_warranty`
9. `repair_order`
10. `account_move_einvoice`

---

<strong>Cấu hình hệ thống</strong>

<strong>Sản phẩm xe đạp</strong>

Mở Product Template và cấu hình:

* `Is Bike`: đánh dấu sản phẩm là xe đạp.
* `Is Assembly Required`: chuyển xe sang quy trình lắp ráp sau khi Picking.
* `Warranty Duration`: số tháng bảo hành của sản phẩm.

Đối với quy trình quản lý serial/frame number, cần cấu hình tracking của sản phẩm để serial hoặc frame number xuất hiện trên Stock Move Line.

<strong>Thành viên</strong>

Tạo các hạng thành viên với:

* Điểm tích lũy tối thiểu
* Tỷ lệ giảm giá
* Hệ số nhân điểm
* Mô tả quyền lợi
* Số lượt bảo trì miễn phí

Khách hàng có thể được đánh dấu là thành viên. Hạng thành viên sẽ được tính tự động dựa trên điểm tích lũy.

<strong>Assembly và PDI</strong>

Tạo checklist template theo danh mục sản phẩm:

* Assembly template được sử dụng bởi `bike_assembly`
* PDI template được sử dụng bởi `bike_pdi`

Khi hoàn tất Picking xe đạp, hệ thống sẽ dựa vào category sản phẩm để tìm checklist template phù hợp và tạo checklist vận hành tương ứng.

<strong> Bảo hành</strong>

Trong phần Settings, chọn các category sản phẩm yêu cầu tạo thẻ bảo hành.

Khi đơn bán hàng đã xác nhận chứa sản phẩm thuộc category này và sản phẩm có thời hạn bảo hành lớn hơn 0, hệ thống sẽ tự động tạo thẻ bảo hành.

<strong>Repair</strong>

Tạo các gói dịch vụ sửa chữa. Mỗi gói sẽ tự động tạo service product liên kết và có thể gắn với checklist template.

Repair Order có thể:

* Thêm linh kiện thay thế
* Tính chi phí công sửa chữa và linh kiện
* Áp dụng giảm giá bảo hành/thành viên
* Tạo Sales Order liên kết để thanh toán

---

<strong>Cấu trúc Repository</strong>

```text
account_move_einvoice/
bicycle_membership/
bike_assembly/
bike_packing/
bike_pdi/
bike_picking/
bike_sales_order/
bike_sales_quotation/
bike_warranty/
product_warranty/
repair_order/
```

```
```
