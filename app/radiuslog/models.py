from django.db import models
from accounts.models import User
from django.utils.translation import gettext_lazy as _

class TerminateCause(models.Model):
    name = models.CharField(max_length=25)
    def __str__(self):
        return self.name
class StatusType(models.Model):
    name = models.CharField(max_length=25)
    def __str__(self):
        return self.name
class Authenticate(models.Model):
    user= models.ForeignKey(User, on_delete=models.DO_NOTHING)
    nas_ip_address= models.GenericIPAddressField(protocol='IPv4',verbose_name=u"آدرس شبکه دستگاه")
    nas_identifier= models.CharField(max_length=30,verbose_name=u"نام دستگاه")
    user_ip_address= models.GenericIPAddressField(protocol='IPv4',verbose_name=u"آدرس شبکه کاربر")
    acct_session_id= models.CharField(max_length=10,verbose_name=u"شناسه جلسه")
    login_time = models.DateTimeField(auto_now_add=True,verbose_name=u"زمان ورود")
    class Meta:
        verbose_name = u"احراز هویت"
        verbose_name_plural = u"احراز هویت ها"
        indexes = [
                    models.Index(fields=['user',]),
                    models.Index(fields=['login_time',]),
                    models.Index(fields=['user','login_time']),
                    ]        
    def __str__(self):
        return self.user.username
class Accounting(models.Model):
    status_mapper={'Start':1, 'Stop':2, 'Interim-Update':3}
    terminate_cause_mapper={'User-Request':1, 'Lost-Carrier':2,'Lost-Service':3
    ,'Idle-Timeout':4, 'Session-Timeout':5,'Admin-Reset':6, 'Admin-Reboot':7, 'Port-Error':8, 'NAS-Error':9
    ,'NAS-Request':10, 'NAS-Reboot':11, 'Port-Unneeded':12, 'Port-Preempted':13, 'Port-Suspended':14
    ,'Service-Unavailable':15, 'Callback':16, 'User-Error':17, 'Host-Request':18}
    user= models.ForeignKey(User, on_delete=models.DO_NOTHING)
    nas_ip_address= models.GenericIPAddressField(protocol='IPv4',verbose_name=u"آدرس شبکه دستگاه")
    nas_identifier= models.CharField(max_length=30,verbose_name=u"نام دستگاه")
    user_ip_address= models.GenericIPAddressField(protocol='IPv4',verbose_name=u"آدرس شبکه کاربر")
    acct_session_id= models.CharField(max_length=10,verbose_name=u"شناسه جلسه")
    acct_status_type=models.ForeignKey(StatusType,on_delete=models.DO_NOTHING,verbose_name=u"نوع لاگ")
    acct_input_octets=models.BigIntegerField(default=0,verbose_name=u"حجم آپلود")
    acct_output_octets=models.BigIntegerField(default=0,verbose_name=u"حجم دانلود")
    acct_input_packets=models.BigIntegerField(default=0,verbose_name=u"تعداد پکت ارسالی")
    acct_output_packets=models.BigIntegerField(default=0,verbose_name=u"تعداد پکت دریافتی")
    acct_session_time=models.IntegerField(default=0,verbose_name=u"زمان جلسه")
    acct_terminate_cause=models.ForeignKey(TerminateCause,on_delete=models.DO_NOTHING,null=True,verbose_name=u"علت خاتمه دادن")
    login_time = models.DateTimeField(auto_now_add=True,verbose_name=u"زمان ورود")
    logout_time = models.DateTimeField(null=True,verbose_name=u"زمان خروج")
    update_time= models.DateTimeField(auto_now=True,verbose_name=u"زمان آخرین تغییر")
    class Meta:
        ordering = ['-id']
        verbose_name_plural = u"مصرف کاربران"
        verbose_name = u"مصرف کاربر"
        indexes = [
            models.Index(fields=['user',]),
            models.Index(fields=['login_time',]),
            models.Index(fields=['user','login_time']),
            ] 
    def __str__(self):
        return self.user.username
class UserLog(models.Model):
    user= models.ForeignKey(User,null=True, on_delete=models.DO_NOTHING)
    user_ip_address= models.GenericIPAddressField(protocol='IPv4',verbose_name=u"آدرس شبکه کاربر")
    dns_log= models.CharField(max_length=255,verbose_name=u"آدرس",null=True)
    log_time = models.DateTimeField(auto_now_add=True,verbose_name=u"زمان ایجاد")
    class Meta:
        indexes = [
            models.Index(fields=['user',]),
            models.Index(fields=['log_time',]),
            models.Index(fields=['dns_log',]),
            models.Index(fields=['user','log_time']),
            models.Index(fields=['user','dns_log']),
            models.Index(fields=['user','log_time','dns_log']),
            ]         
        ordering = ['-id']
        verbose_name_plural = u"لاگ کاربران"
        verbose_name = u"لاگ کاربر"
    def __str__(self):
        return self.user.username
   # class Acct_Status(models.TextChoices):
    #     Start = 'Start'
    #     Stop = 'Stop'
    #     Interim_Update='Interim_Update'

    # class Acct_Terminate_Cause(models.TextChoices):
    # User_Request= 1
    # Lost_Carrier=2
    # Lost_Service=3
    # Idle_Timeout=4
    # Session_Timeout=5
    # Admin_Reset=6
    # Admin_Reboot=7
    # Port_Error=8
    # NAS_Error=9
    # NAS_Request=10
    # NAS_Reboot=11
    # Port_Unneeded=12
    # Port_Preempted=13
    # Port_Suspended=14
    # Service_Unavailable=15
    # Callback=16
    # User_Error=17
    # Host_Request=18