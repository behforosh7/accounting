# Generated by Django 4.1.3 on 2022-12-03 04:13

import accounts.helpers
import accounts.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_profile_options_alter_organization_profile_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.profile', verbose_name='پروفایل سازمان'),
        ),
        migrations.AlterField(
            model_name='user',
            name='mobile_nu',
            field=models.CharField(blank=True, help_text='Please enter your name...', max_length=11, null=True, validators=[accounts.validators.validate_mobile_number], verbose_name='شماره موبایل'),
        ),
        migrations.CreateModel(
            name='MobileVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mobile_nu', models.CharField(max_length=12, validators=[accounts.validators.validate_mobile_number], verbose_name='شماره موبایل')),
                ('code', models.CharField(default=accounts.helpers.ModelDefaultRandomInt(5), max_length=5)),
                ('revoked', models.BooleanField(default=False)),
                ('expire_at', models.DateTimeField(default=accounts.helpers.ModelTimeInFuture(minutes=5))),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'کد تایید تلفن همراه',
                'verbose_name_plural': 'کدهای تایید تلفن همراه',
            },
        ),
    ]
