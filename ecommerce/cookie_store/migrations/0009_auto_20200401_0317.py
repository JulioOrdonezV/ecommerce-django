# Generated by Django 3.0.4 on 2020-04-01 03:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cookie_store', '0008_auto_20200330_1603'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='nombre',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='item',
            old_name='precio',
            new_name='price',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='completada',
            new_name='completed',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='fecha_orden',
            new_name='order_date',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='cantidad',
            new_name='quantity',
        ),
    ]
