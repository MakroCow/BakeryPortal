# Generated by Django 2.0.2 on 2018-03-15 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0005_auto_20180315_1557'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='unit',
            field=models.CharField(blank=True, choices=[('ml', 'Milliliter'), ('l', 'Liter'), ('g', 'Gramm'), ('mg', 'Milligramm'), ('Stück', 'Stück'), ('Prise', 'Prise (3g)')], help_text='Einheit', max_length=6),
        ),
    ]
