# Generated by Django 4.1.3 on 2022-12-05 21:27

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_alter_mobilenuchanged_mobile_nu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mobileverification',
            name='mobile_nu',
            field=models.CharField(max_length=12, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '09xxxxxxxxx'. Up to 11 digits allowed.", regex='^09(1[0-9]|3[1-9])-?[0-9]{3}-?[0-9]{4}$')], verbose_name='شماره موبایل'),
        ),
    ]
