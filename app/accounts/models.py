from unittest.util import _MAX_LENGTH
from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, PermissionsMixin)
from django.core.validators import RegexValidator
from datetime import datetime
from model_utils import FieldTracker
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .validators import validate_mobile_number, validate_national_id
from .helpers import ModelDefaultRandomInt, ModelTimeInFuture
from django.utils import timezone
from django.db.models import signals
from django.dispatch import receiver
from django.template.loader import render_to_string
from .services import SendMessage
from .helpers import normalize_mobile_number
from django.contrib import messages

class Profile(models.Model):
    name = models.CharField(
        max_length=50, verbose_name=u"نام پروفایل", unique=True, blank=False, null=False)
    download_speed = models.CharField(max_length=10, verbose_name=u"حداکثر سرعت دانلود",
                                      help_text='مگابیت بر ثانیه، مقدار صفر به معنی بدون محدودیت سرعت است')
    upload_speed = models.CharField(max_length=10, verbose_name=u"حداکثر سرعت آپلود",
                                    help_text='مگابیت بر ثانیه، مقدار صفر به معنی بدون محدودیت سرعت است')
    is_limit_speed = models.BooleanField(default=0, verbose_name=u"محدودیت سرعت",
                                         help_text='درصورت غیر فعال بودن محدودیت سرعت برای این کاربر اعمال نخواهد شد')
    daily_download = models.BigIntegerField(
        default=0, verbose_name=u"جداکثر دانلود روزانه", help_text='مگابایت')
    monthly_download = models.BigIntegerField(
        default=0, verbose_name=u"جداکثر دانلود ماهانه", help_text='مگابایت')
    is_limit_download = models.BooleanField(default=0, verbose_name=u"محدودیت دانلود",
                                            help_text=u"با فعال بودن این گزینه محاسبه مقدار استفاده بر اساس تنظیمات دانلود روزانه و ماهانه انجام می شود و اولویت این از بسته اینترنتی بالاتر است.")
    is_voucher = models.BooleanField(default=0, verbose_name=u"بسته اینترنتی",
                                     help_text=u"با فعال بودن این گزینه کاربر می بایست بسته اینترنتی خریداری نماید.")
    remain = models.IntegerField(
        default=0, verbose_name=u"باقیمانده حجم", help_text='به مگابایت')
    created_date = models.DateTimeField(
        auto_now_add=True, verbose_name=u"تاریخ ایجاد")
    updated_date = models.DateTimeField(
        auto_now=True, blank=True, null=True, verbose_name=u"زمان تغییر")
    created_user = models.BigIntegerField(
        default=0, blank=True, null=True, verbose_name='کاربر ایجاد کننده')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name_plural = u"پروفایل ها"
        verbose_name = u"پروفایل"

class UserManager(BaseUserManager):
    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('The given mobile number must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, password, **extra_fields)


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"نام سازمان")
    profile = models.ForeignKey(Profile, verbose_name=u"پروفایل سازمان", blank=True, null=True, on_delete=models.SET_NULL)
    class Meta:
        verbose_name_plural = u"سازمان ها"
        verbose_name = u"سازمان"
    def __str__(self):
        return self.name


class User (AbstractBaseUser, PermissionsMixin):
    mobile_nu = models.CharField(validators=[validate_mobile_number], blank=True, null=True,
                                 max_length=12, verbose_name=u"شماره موبایل", help_text=u"Please enter your name...")
    username = models.CharField(max_length=50, verbose_name=u"نام کاربری", unique=True, blank=False, null=False)
    first_name = models.CharField(max_length=50, null=True, blank=True, verbose_name=u"نام")
    last_name = models.CharField(max_length=70, null=True, blank=True, verbose_name=u"نام خانوادگی")
    is_active = models.BooleanField(default=True, verbose_name=u"فعال")
    is_staff = models.BooleanField(default=False, verbose_name=u"مدیر")
    is_mobile_verified = models.BooleanField(default=False, verbose_name=u"تایید شماره موبایل")
    organization = models.ForeignKey(Organization, blank=True, null=True, verbose_name=u"سازمان", on_delete=models.SET_NULL)
    is_organization_admin = models.BooleanField(default=False, verbose_name=u"مدیر سازمان")
    profile = models.ForeignKey(Profile, blank=True, null=True,on_delete=models.SET_NULL, verbose_name=u"پروفایل کاربری")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=u"تاریخ ایجاد")
    updated_date = models.DateTimeField(auto_now=True, verbose_name=u"زمان تغییر")
    created_user = models.BigIntegerField(default=0, blank=True, null=True, verbose_name='کاربر ایجاد کننده')
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []
    objects = UserManager()
    tracker = FieldTracker()

    def __str__(self):
        return self.username

    class Meta:
        ordering = ('username',)
        indexes = [
            models.Index(fields=['username',]),
            models.Index(fields=['organization',]),
        ]
    def save(self,*args, **kwargs):
        group_admin, created = Group.objects.get_or_create(name='group_admin')
        if created:
            from radiuslog.models import Accounting
            content_type = ContentType.objects.get_for_model(User)
            User_permission = Permission.objects.filter(content_type=content_type)
            for perm in User_permission:
                group_admin.permissions.add(perm)
            content_type = ContentType.objects.get_for_model(Profile)
            User_permission = Permission.objects.filter(content_type=content_type)
            for perm in User_permission:
                group_admin.permissions.add(perm)
            content_type = ContentType.objects.get_for_model(Accounting)
            User_permission = Permission.objects.filter(content_type=content_type)
            for perm in User_permission:
                if perm.codename == "view_accounting":
                    group_admin.permissions.add(perm)        
        
        organization_admin = self.tracker.has_changed('is_organization_admin')
        pre_organization_admin = self.tracker.previous('is_organization_admin')
        mobile_nu_changed = self.tracker.has_changed('mobile_nu')
        if mobile_nu_changed and self.tracker.previous('mobile_nu') is not None:
            mobile_changed_obj=MobileNuChanged(user=self,mobile_nu_old=self.tracker.previous('mobile_nu'),
            mobile_nu_new=self.mobile_nu,is_Verified=self.is_mobile_verified)
            mobile_changed_obj.save()
            self.is_mobile_verified = False

        self.mobile_nu=normalize_mobile_number(self.mobile_nu)
        super().save()
        if self.is_organization_admin:
            group_admin.user_set.add(self.pk)
        if organization_admin:          
            if pre_organization_admin:
                group_admin.user_set.remove(self.pk)
    class Meta:
        verbose_name_plural = "کاربران"
        verbose_name = "کاربر"

class UserActivity(models.Model):
    user = models.ForeignKey(User,verbose_name=u"کاربر", on_delete=models.DO_NOTHING)
    form =  models.CharField(max_length=30, verbose_name=u"نام صفحه")
    event = models.CharField(max_length=100, verbose_name=u"رویداد")
    data = models.TextField(verbose_name=u"داده")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=u"تاریخ ایجاد")
    class Meta:
        verbose_name_plural = "فعالیت کاربران"
        verbose_name = "فعالیت کاربر"
        indexes = [
            models.Index(fields=['user',]),
            models.Index(fields=['created_date',]),
            models.Index(fields=['user','created_date',]),
        ]
class MobileNuChanged(models.Model):
    phone_regex = RegexValidator(
    regex=r'^09(1[0-9]|3[1-9])-?[0-9]{3}-?[0-9]{4}$', message="Phone number must be entered in the format: '09xxxxxxxxx'. Up to 11 digits allowed.")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    mobile_nu_old = models.CharField(validators=[validate_mobile_number], blank=True, null=True,
                                 max_length=12, verbose_name=u"شماره موبایل قدیم", help_text=u"Please enter your name...")
    mobile_nu_new = models.CharField(validators=[validate_mobile_number], blank=True, null=True,
                                 max_length=12, verbose_name=u"شماره موبایل جدید", help_text=u"Please enter your name...")
    is_Verified = models.BooleanField(default=0, verbose_name=u"تایید شده")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=u"تاریخ ایجاد")
    def __str__(self):
        return "{} - {}".format(self.user, self.mobile_nu_old)
    class Meta:
        verbose_name_plural = "شماره موبایلهای تغییر یافته"
        verbose_name = "شماره موبایل تغییر یافته"
class VoucherType(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"نام بسته اینترنتی")
    volume = models.BigIntegerField(default=0, verbose_name=u"حجم", help_text='به مگابایت')
    duration_day = models.IntegerField(default=0, verbose_name=u"مدت زمان-روز")
    price = models.IntegerField(default=0, verbose_name=u"مبلغ")
    is_valid = models.BooleanField(default=1, verbose_name=u"فعال")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=u"تاریخ ایجاد")
    download_speed = models.IntegerField(verbose_name=u"حداکثر سرعت دانلود",
                                      help_text='مگابیت بر ثانیه، مقدار صفر به معنی بدون محدودیت سرعت است')
    upload_speed = models.IntegerField( verbose_name=u"حداکثر سرعت آپلود",
                                    help_text='مگابیت بر ثانیه، مقدار صفر به معنی بدون محدودیت سرعت است')
    class Meta:
        ordering = ('duration_day','price')
        verbose_name_plural = u"بسته های اینترنتی"
        verbose_name = u"بسته اینترنتی"
       
    def __str__(self):
        return self.name + u" -" + f"{int(self.price/10):,}" + u" تومان"


class Voucher(models.Model):
    user = models.ForeignKey(User,verbose_name=u"کاربر", related_name='user', on_delete=models.DO_NOTHING)
    voucher_type = models.ForeignKey(VoucherType, on_delete=models.DO_NOTHING, verbose_name=u"بسته حجمی")
    pre_used = models.BigIntegerField(default=0, verbose_name=u"حجم مصرف شده قبلی", help_text='به مگابایت')
    used = models.BigIntegerField(default=0, verbose_name=u"حجم مصرف شده", help_text='به مگابایت')
    is_valid = models.BooleanField(default=1, verbose_name=u"فعال")
    assign_by=models.ForeignKey(User,verbose_name=u"تخصیص دهنده",related_name='assign', on_delete=models.DO_NOTHING)
    start_date = models.DateTimeField( null=True, blank=True, verbose_name=u"زمان شروع")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=u"تاریخ ایجاد")
    update_date = models.DateTimeField(auto_now=True, verbose_name=u"زمان تغییر")
    class Meta:
        ordering = ('-is_valid','-id')
        verbose_name_plural = u"بسته های اینترنتی کاربران"
        verbose_name = u"بسته های اینترنتی کاربر"
        indexes = [
            models.Index(fields=['user',]),
            models.Index(fields=['assign_by',]),
            models.Index(fields=['is_valid',]),
            models.Index(fields=['created_date',]),
            models.Index(fields=['user','is_valid','created_date',]),
            models.Index(fields=['user','created_date',]),
        ]         
    def __str__(self):
        return "{} - {}".format(self.user, self.voucher_type.name)
class Payment(models.Model):
    user = models.ForeignKey(User,verbose_name=u"کاربر", related_name='payment_user', on_delete=models.DO_NOTHING)
    voucher_type = models.ForeignKey(VoucherType,related_name='payment_vouchettype', on_delete=models.DO_NOTHING, verbose_name=u"نوع بسته حجمی")
    voucher = models.ForeignKey(Voucher, null=True, blank=True,related_name='payment_vouchet', on_delete=models.DO_NOTHING, verbose_name=u"بسته حجمی")
    amount=models.IntegerField(default=0, verbose_name=u"مبلغ", help_text='به ریال')
    success=models.BooleanField(default=False)
    token=models.CharField(max_length=255, null=True, blank=True, verbose_name=u"توکن پرداخت")
    message=models.CharField(max_length=255, null=True, blank=True, verbose_name=u"پیام")
    reference=models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name=u"شماره پیگیری")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=u"تاریخ ایجاد")
    updated_date = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u"زمان تغییر")
    activate=models.BooleanField(default=True)

    def save(self, *args, **kwargs):
            super(Payment, self).save(*args, **kwargs) 
            return self
    class Meta:
        verbose_name = u"پرداخت"
        verbose_name_plural =u"پرداخت ها"
    def __str__(self):
        return "{} - {}".format(self.user, self.voucher_type)
        
class MobileVerification(models.Model):
    phone_regex = RegexValidator(
    regex=r'^09(1[0-9]|3[1-9])-?[0-9]{3}-?[0-9]{4}$', message="Phone number must be entered in the format: '09xxxxxxxxx'. Up to 11 digits allowed.")
    mobile_nu = models.CharField(verbose_name=u"شماره موبایل", max_length=12,validators=[validate_mobile_number],)
    code = models.CharField(max_length=5, default=ModelDefaultRandomInt(5))
    revoked = models.BooleanField(default=False)
    # While registering user can be null
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    expire_at = models.DateTimeField(default=ModelTimeInFuture(minutes=5))

    class Meta:
        verbose_name = u"کد تایید تلفن همراه"
        verbose_name_plural =u"کدهای تایید تلفن همراه"
        indexes = [
            models.Index(fields=['user',]),
            models.Index(fields=['user','expire_at',]),
            models.Index(fields=['user','revoked','expire_at',]),
            models.Index(fields=['user','revoked','expire_at','code']),
            models.Index(fields=['user','expire_at','code']),
        ]
    def __str__(self):
        return "{} - {}".format(self.mobile_nu, self.code)

    @property
    def is_expired(self):
        return timezone.now() > self.expire_at

   # tracker_organization_admin = FieldTracker(fields=['is_organization_admin'])
    # tracker_mobile_nu = FieldTracker(fields=['mobile_nu'])

@receiver(signals.post_save, sender=User)
def users_log_signal(sender, instance, created, **kwargs):
    try:
        if created:
            user=User.objects.get(pk=instance.created_user)
            if user:
                event="create"
                users_log(user,"User",event,instance)
        return True
    except Exception as e:
        return False                
def users_log(user,page_form,event,instance):
    try:
        if user:
            user_activity=UserActivity()
            user_activity.event=event
            user_activity.user=user 
            user_activity.form=page_form
            user_str="user name:{username}, first name:{firstname}, last name:{lastname}, mobile number:{mobile_nu}, is mobile verified:{is_mobile_verified} ,organization:{organization}, is org admin:{is_org_admin}, is active:{is_active}"
            user_activity.data=user_str.format(username=instance.username, firstname=instance.first_name, 
                lastname=instance.last_name,mobile_nu=instance.mobile_nu,is_mobile_verified=instance.is_mobile_verified
                ,organization=instance.organization.name,is_org_admin=instance.is_organization_admin,is_active=instance.is_active )
            user_activity.save()
        return True
    except Exception as e:
        return False
def voucher_log(user,page_form,event,instance):
    try:
        if user:
            user_activity=UserActivity()
            user_activity.event=event
            user_activity.user=user 
            user_activity.form=page_form
            user_str="user name:{username}, first name:{firstname}, last name:{lastname}, voucher type:{voucher_type}, duration day:{duration_day} ,volume:{volume}"
            user_activity.data=user_str.format(username=instance.user.username, firstname=instance.user.first_name, 
                lastname=instance.user.last_name,voucher_type=instance.voucher_type,duration_day=instance.voucher_type.duration_day
                ,volume=instance.voucher_type.volume)
            user_activity.save()
        return True
    except Exception as e:
        return False
def voucher_log_payment(user,page_form,event,voucher):
    try:
        if user:
            user_activity=UserActivity()
            user_activity.event=event
            user_activity.user=user 
            user_activity.form=page_form
            user_str="payment user name:{username}, first name:{firstname}, last name:{lastname}, voucher type:{voucher_type}, duration day:{duration_day} ,volume:{volume}"
            user_activity.data=user_str.format(username=user.username, firstname=user.first_name, 
                lastname=user.last_name,voucher_type=voucher.voucher_type,duration_day=voucher.voucher_type.duration_day
                ,volume=voucher.voucher_type.volume)
            user_activity.save()
        return True
    except Exception as e:
        return False             
@receiver(signals.post_save, sender=MobileVerification)
def send_mobile_verification(sender, instance, created, **kwargs):
    try:
        #  Do not trigger the signal when loading fixtures
        if kwargs.get("raw", True):
            return True

        if created:

            message = render_to_string(
                "accounts/verify_phone.txt",
                context={"verification_code": instance.code},
            )
            message= "کد اعتبارسنجی شما برابر است با :" + instance.code
            print (message)
            client = SendMessage(message)
            client.sms(normalize_mobile_number(instance.mobile_nu))
        return True
    except Exception as e:
        return False
