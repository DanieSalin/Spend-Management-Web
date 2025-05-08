from django.db import migrations

def add_default_categories(apps, schema_editor):
    Category = apps.get_model('finance_app', 'Category')
    User = apps.get_model('auth', 'User')
    
    # Lấy tất cả các user
    users = User.objects.all()
    
    # Danh sách danh mục mặc định
    default_categories = [
        'Ăn uống', 'Chi tiêu hằng ngày', 'Quần áo', 'Mỹ phẩm',
        'Phí giao lưu', 'Y tế', 'Giáo dục', 'Tiền điện',
        'Đi lại', 'Phí liên lạc', 'Tiền nhà'
    ]
    
    # Thêm danh mục mặc định cho mỗi user
    for user in users:
        for category_name in default_categories:
            # Kiểm tra xem danh mục đã tồn tại chưa
            if not Category.objects.filter(user=user, name=category_name).exists():
                Category.objects.create(
                    name=category_name,
                    user=user,
                    type='expense',
                    is_default=True
                )

class Migration(migrations.Migration):
    dependencies = [
        ('finance_app', '0003_add_is_default_and_unique_together'),
    ]

    operations = [
        migrations.RunPython(add_default_categories),
    ] 