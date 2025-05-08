from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('finance_app', '0002_handle_duplicate_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_default',
            field=models.BooleanField(default=False, verbose_name='Danh mục mặc định'),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('name', 'user')},
        ),
    ] 