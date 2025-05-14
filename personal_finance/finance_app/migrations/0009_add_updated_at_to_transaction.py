from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('finance_app', '0008_goaltransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ] 