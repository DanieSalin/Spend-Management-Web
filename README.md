# Ứng dụng Quản lý Tài chính Cá nhân

Đây là một ứng dụng web được xây dựng bằng Django để giúp người dùng quản lý tài chính cá nhân một cách hiệu quả.

## Cấu trúc dự án

```
Spend-Management-Web/
├── personal_finance/                    # Thư mục gốc của dự án
│   ├── personal_finance/               # Cấu hình chính của dự án Django
│   │   ├── settings.py                # Cấu hình dự án
│   │   ├── urls.py                    # Định tuyến URL chính
│   │   ├── wsgi.py                    # Cấu hình WSGI
│   │   └── asgi.py                    # Cấu hình ASGI
│   │
│   ├── finance_app/                   # Ứng dụng chính xử lý logic tài chính
│   │   ├── models.py                  # Định nghĩa cấu trúc dữ liệu
│   │   ├── views.py                   # Xử lý logic nghiệp vụ
│   │   ├── forms.py                   # Định nghĩa các form
│   │   ├── urls.py                    # Định tuyến URL của ứng dụng
│   │   ├── admin.py                   # Cấu hình trang admin
│   │   ├── templates/                 # Chứa các file template HTML
│   │   ├── static/                    # Chứa các file tĩnh của ứng dụng
│   │   ├── templatetags/              # Custom template tags
│   │   └── migrations/                # Quản lý thay đổi database
│   │
│   ├── staticfiles/                   # Chứa các file tĩnh (CSS, JS, images)
│   ├── media/                         # Thư mục lưu trữ file media
│   ├── db.sqlite3                     # Database SQLite
│   ├── manage.py                      # Script quản lý Django
│   └── requirements.txt               # Danh sách các thư viện cần thiết
│
├── venv/                             # Môi trường ảo Python
└── .git/                            # Thư mục Git
```

## Yêu cầu hệ thống

- Python 3.x
- Django
- Các thư viện được liệt kê trong file requirements.txt

## Hướng dẫn cài đặt và chạy ứng dụng (KHÔNG dùng Docker)

### 1. Clone repository:
```bash
git clone [URL_REPOSITORY]
cd Spend-Management-Web
```

### 2. Tạo và kích hoạt môi trường ảo (venv):
```bash
python -m venv venv
# Trên Windows:
venv\Scripts\activate
# Trên macOS/Linux:
source venv/bin/activate
```

### 3. Cài đặt các thư viện cần thiết:
```bash
pip install -r personal_finance/requirements.txt
```

### 4. Chạy migrate để tạo database:
```bash
cd personal_finance
python manage.py migrate
```

### 5. Tạo tài khoản admin (tùy chọn):
```bash
python manage.py createsuperuser
```

### 6. Chạy server:
```bash
python manage.py runserver
```

### 7. Truy cập ứng dụng:
- Mở trình duyệt và truy cập: http://localhost:8000

## Tính năng chính

### 1. Quản lý giao dịch
- **Danh sách giao dịch** (`transaction_list.html`): Hiển thị tất cả các giao dịch thu chi
- **Thêm/Sửa giao dịch** (`transaction_form.html`): Form nhập liệu cho giao dịch mới hoặc chỉnh sửa
- **Chi tiết giao dịch** (`transaction_detail.html`): Xem thông tin chi tiết của một giao dịch
- **Xóa giao dịch** (`transaction_confirm_delete.html`): Xác nhận xóa giao dịch

### 2. Quản lý mục tiêu tài chính
- **Danh sách mục tiêu** (`goal_list.html`): Hiển thị các mục tiêu tài chính
- **Thêm/Sửa mục tiêu** (`goal_form.html`): Tạo hoặc chỉnh sửa mục tiêu
- **Chi tiết mục tiêu** (`goal_detail.html`): Xem thông tin chi tiết và tiến độ của mục tiêu
- **Đóng góp vào mục tiêu** (`goal_contribution.html`): Thêm khoản đóng góp cho mục tiêu
- **Xóa mục tiêu** (`goal_confirm_delete.html`): Xác nhận xóa mục tiêu

### 3. Quản lý danh mục
- **Danh sách danh mục** (`category_list.html`): Hiển thị và quản lý các danh mục chi tiêu
- **Thêm/Sửa danh mục** (`category_form.html`): Tạo hoặc chỉnh sửa danh mục
- **Xóa danh mục** (`category_confirm_delete.html`): Xác nhận xóa danh mục

### 4. Quản lý thẻ
- **Danh sách thẻ** (`card_list.html`): Quản lý các thẻ thanh toán
- **Thêm/Sửa thẻ** (`card_form.html`): Thêm hoặc chỉnh sửa thông tin thẻ
- **Xóa thẻ** (`card_confirm_delete.html`): Xác nhận xóa thẻ

### 5. Quản lý ngân sách
- **Danh sách ngân sách** (`budget_list.html`): Theo dõi ngân sách cho các danh mục
- **Thêm/Sửa ngân sách** (`budget_form.html`): Thiết lập hoặc điều chỉnh ngân sách
- **Xóa ngân sách** (`budget_confirm_delete.html`): Xác nhận xóa ngân sách

### 6. Thống kê và báo cáo
- **Trang thống kê** (`statistics.html`): Hiển thị các biểu đồ và báo cáo tài chính
- **Trang chủ** (`index.html`): Tổng quan về tình hình tài chính

### 7. Thông báo
- **Danh sách thông báo** (`notification_list.html`): Hiển thị các thông báo hệ thống

### 8. Giao diện người dùng
- **Trang đích** (`landing.html`): Trang giới thiệu và đăng nhập
- **Giao diện cơ sở** (`base.html`): Template chung cho toàn bộ ứng dụng
- **Giao diện đích cơ sở** (`base_landing.html`): Template chung cho trang đích

## Đóng góp

Mọi đóng góp đều được hoan nghênh. Vui lòng tạo issue hoặc pull request để đóng góp vào dự án.

## Giấy phép

Dự án này được phát hành dưới giấy phép MIT. 