# Generated by Django 4.1.3 on 2022-12-10 11:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_alter_mobilenuchanged_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mobilenuchanged',
            options={'verbose_name': 'شماره موبایل تغییر یافته', 'verbose_name_plural': 'شماره موبایلهای تغییر یافته'},
        ),
        migrations.AlterModelOptions(
            name='organization',
            options={'verbose_name': 'سازمان', 'verbose_name_plural': 'سازمان ها'},
        ),
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ('id',), 'verbose_name': 'پروفایل', 'verbose_name_plural': 'پروفایل ها'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'کاربر', 'verbose_name_plural': 'کاربران'},
        ),
        migrations.AlterModelOptions(
            name='voucher',
            options={'verbose_name': 'بسته های اینترنتی کاربر', 'verbose_name_plural': 'بسته های اینترنتی کاربران'},
        ),
        migrations.AlterModelOptions(
            name='voucherassign',
            options={'verbose_name': 'کاربر اختصاص دهنده بسته', 'verbose_name_plural': 'کاربرانی که بسته اختصاص داده اند'},
        ),
        migrations.AlterModelOptions(
            name='vouchertype',
            options={'verbose_name': 'بسته اینترنتی', 'verbose_name_plural': 'بسته های اینترنتی'},
        ),
        migrations.AddField(
            model_name='voucher',
            name='assign_by',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.DO_NOTHING, related_name='assign', to=settings.AUTH_USER_MODEL, verbose_name='تخصیص دهنده'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='voucher',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='user', to=settings.AUTH_USER_MODEL, verbose_name='کاربر'),
        ),
    ]
