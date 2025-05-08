from django.db import migrations

def handle_duplicate_categories(apps, schema_editor):
    Category = apps.get_model('finance_app', 'Category')
    
    # Lấy tất cả các danh mục
    categories = Category.objects.all()
    
    # Tạo dictionary để lưu trữ danh mục theo user và tên
    category_dict = {}
    
    # Xử lý các danh mục trùng lặp
    for category in categories:
        key = (category.user_id, category.name.lower())
        if key in category_dict:
            # Nếu đã tồn tại, xóa danh mục trùng lặp
            category.delete()
        else:
            # Nếu chưa tồn tại, lưu vào dictionary
            category_dict[key] = category

class Migration(migrations.Migration):
    dependencies = [
        ('finance_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(handle_duplicate_categories),
    ] 