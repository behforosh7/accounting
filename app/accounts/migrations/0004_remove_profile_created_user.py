# Generated by Django 4.1.3 on 2022-11-24 17:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_profile_created_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='created_user',
        ),
    ]
