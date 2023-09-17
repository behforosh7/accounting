# Generated by Django 4.1.3 on 2022-12-05 20:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_rename_mobile_is_validate_user_is_mobile_verified_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='mobile_nu',
            field=models.CharField(blank=True, help_text='Please enter your name...', max_length=12, null=True, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '09xxxxxxxxx'. Up to 11 digits allowed.", regex='^09(1[0-9]|3[1-9])-?[0-9]{3}-?[0-9]{4}$')], verbose_name='شماره موبایل'),
        ),
    ]
