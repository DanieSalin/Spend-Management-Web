# Generated by Django 5.2 on 2025-05-11 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance_app', '0011_alter_card_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='card_type',
            field=models.CharField(choices=[('credit', 'Thẻ tín dụng'), ('debit', 'Thẻ ghi nợ'), ('ewallet', 'Ví điện tử')], max_length=10, verbose_name='Loại thẻ/ví'),
        ),
    ]
