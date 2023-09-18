from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib import messages,humanize
from accounts.models import Profile,User,Voucher
from accounts.forms import loginform
from django.contrib.auth import authenticate, login, logout
from radiuslog.models import Accounting
from datetime import date
from django.conf import settings
from jalali_date import jdatetime,date2jalali
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils  import timezone
from datetime import timedelta
import routeros_api
from routeros_api import exceptions as RouterException
from django.http import JsonResponse
from axes.utils import reset_request
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from accounts.forms import AxesCaptchaForm
from axes.backends import AxesBackend

class MyBackend(AxesBackend):
    def authenticate(self, request=None, *args, **kwargs):
        if request:
            return super().authenticate(request, *args, **kwargs)
def locked_out(request):
    if request.POST:
        form = AxesCaptchaForm(request.POST)
        if form.is_valid():
            reset_request(request)
            return HttpResponseRedirect(reverse_lazy('auth_login'))
    else:
        form = AxesCaptchaForm()

    return render(request, 'accounts/captcha.html', {'form': form})
def lockout(request, credentials, *args, **kwargs):
    return JsonResponse({"status": "به علت تلاش غیر مجاز برای ورود به سامانه نام کاربری شما به مدت 10 دقیقه غیر فعال شده است، لطفا با مدیر سامانه تماس بگیرید."}, status=403)
def index(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    vouchers=Voucher.objects.filter(user=request.user,is_valid=True).order_by('id')   
    if vouchers:
        voucher=vouchers[0]
    else:
        voucher=None
    if not voucher:
        return render(request,'main/userdashboard.html')
    used_sum=Accounting.objects.filter(user=request.user,login_time__gte = voucher.start_date).aggregate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets'))

    if not used_sum['download']:
        download=0
    else:
        download=used_sum['download']
    if not used_sum['upload']:
        upload=0
    else:
        upload=used_sum['upload']
    
    used=download+upload    

    voucher.used=used
    voucher.save()

    remain_days=0
    used_days=0
    used_days=(timezone.now()-voucher.start_date).days
    remain_days=voucher.voucher_type.duration_day-used_days
    if remain_days<0:
        remain_days=0

    used_darsad=100
    if voucher.voucher_type.volume>0:
        used_darsad=100* (used//(1024*1024))//voucher.voucher_type.volume
    xAxisData=[]
    download_data=[]
    upload_data=[]
    user_usage_date=Accounting.objects.filter(user=request.user,login_time__gte=timezone.now()-timedelta(days=30)).annotate(login_date=TruncDate('login_time')).values('login_date').annotate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets')).order_by('login_date')

    jdate=jdatetime.date.today()
    date1=str(jdate.year)+"/"+str(jdate.month)+"/"
    for user_usage in user_usage_date:
        xAxisData.append(date2jalali(user_usage['login_date']).strftime('%y/%m/%d'))
        download_data.append(user_usage['download']//(1024*1024))
        upload_data.append(user_usage['upload']//(1024*1024))

    accounting = Accounting.objects.filter(user=request.user) if Accounting.objects.filter(user=request.user).exists() else None 

    context={'voucher': voucher, 'accounting':accounting[:50] if accounting!=None else None,'total_volume':(voucher.voucher_type.volume*1024*1024-used)
    ,'used':used , 'total_limit_day':voucher.voucher_type.volume, 'used_darsad':used_darsad
    ,'xAxisData':xAxisData,'download_data':download_data,'upload_data':upload_data,'remain_days':remain_days,'used_days':used_days}
    return render(request,'main/userdashboard.html',context)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_REMOTE_ADDR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')    
    return ip
def logout_view(request):
    if request.user.is_authenticated:
        if request.session.get('accounting_login'):
            user_name=request.user.username
            logout(request)
            mik_check_result=mikrotik_logout(user_name)
            if mik_check_result[0]:
                return redirect('/login') 
            elif mik_check_result[1]:
                messages.add_message(request, messages.ERROR,mik_check_result[1])
                return redirect('/login')          
        else:
            logout(request)
            return redirect('/accounts/login')
def login_accounting_view(request):
    ip_add = get_client_ip(request)
    if request.user.is_authenticated:
        UserObj = request.user
        mik_check_result=mikrotik_login_check(UserObj.username, ip_add)
        if mik_check_result[0]:
            return redirect('/')  # 'User already logged in by this ip address'
        elif len(mik_check_result)>1:
            messages.add_message(request, messages.ERROR,mik_check_result[1])
            return                      
        else:
            logout(request)
    if request.method == 'POST':
        form = loginform(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                try:
                    if ip_add:
                        request.session['accounting_login']=True
                        mik_login=mikrotik_login(username, password, ip_add)
                        if mik_login[0]:
                            login(request, user)
                            return redirect('/') 
                        else:
                            if mik_login[1]=="Radius Error: عدم وجود بسته اینترنتی برای کاربر":
                                login(request, user)
                                #Radius Error: unknown host IP 192.168.100.7
                                #Radius Error: RADIUS server is not responding
                                #Radius Error: عدم وجود بسته اینترنتی برای کاربر
                                message="کاربر محترم:به دلیل عدم وجود بسته اینترنتی فعال برای برقراری اینترنت ابتدا بسته مورد نظر را خریداری نمایید"
                                messages.add_message(request, messages.ERROR,message)                     
                                return redirect('/')
                            else:
                                messages.add_message(request, messages.ERROR,mik_login[1])                     

                    else:
                        messages.add_message(request, messages.ERROR,"خطا در شناسایی آدرس" )                     
                except Exception as e:
                    print("Oops!", e, "occurred on Authentication.")
                    messages.add_message(request, messages.ERROR,e )                     
            else:
                messages.add_message(
                    request, messages.ERROR, 'نام کاربری یا کلمه عبور نادرست است')
        else:
            if form.errors and 'captcha' in form.errors:
                messages.add_message(
                    request, messages.ERROR,'کد کپچا نادرست است')
            else:
                messages.add_message(
                    request, messages.ERROR, 'نام کاربری یا کلمه عبور نادرست است')
    form = loginform()
    context = {'form': form, 'ip_add': ip_add, 'accounting': True}
    return render(request, 'accounts/login.html', context)


def mikrotik_login(user, password, ip):
    try:
        connection = routeros_api.RouterOsApiPool(settings.MIKROTIK_IP,
                                                username=settings.MIKROTIK_ADMIN_USER, password=settings.MIKROTIK_ADMIN_PASSWORD,
                                                port=int(settings.MIKROTIK_API_PORT),
                                                use_ssl=True,
                                                ssl_verify=False,
                                                ssl_verify_hostname=False,
                                                ssl_context=None, plaintext_login=True)
        api = connection.get_api()
        list_user = api.get_resource('/ip/hotspot/active')
        active_user=list_user.get(address=ip)
        if active_user:
            list_user.remove(id=active_user[0]['id']) # اگر قبلا کاربر دیگری با همین آی پی به میکروتیک لاگین بوده لاگ اوت شود
        parameter = {"user": user, "password": password, "ip": ip}
        api.get_binary_resource('/').call('ip/hotspot/active/login', parameter)
        return (True,'Login Success')
    except RouterException.RouterOsApiCommunicationError as e:
        message="Radius Error: "
        if hasattr(e, 'original_message'):
            message=message+e.original_message.decode('unicode-escape').encode('latin1').decode('utf-8')
            print(message)
        else:
            print(message)        
        return (False,message)
 


def mikrotik_login_check(username, ip):
    try:
        connection = routeros_api.RouterOsApiPool(settings.MIKROTIK_IP,
                                                username=settings.MIKROTIK_ADMIN_USER, password=settings.MIKROTIK_ADMIN_PASSWORD,
                                                port=int(settings.MIKROTIK_API_PORT),
                                                use_ssl=True,
                                                ssl_verify=False,
                                                ssl_verify_hostname=False,
                                                ssl_context=None, plaintext_login=True)
        api = connection.get_api()
        list_user = api.get_resource('/ip/hotspot/active')
        active_user = list_user.get(user=username)
        if active_user:
            if active_user[0]['address'] == ip:
                print('کاربر با همین آی پی قبلا لاگین بوده')
                return True,'ok'  # اگر کاربر با همین آی پی لاگین است اقدامی انجام نشود
            else:
                print('کاربر با آی پی دیگه ای لاگین بوده و لاگ اوت شد')
                list_user.remove(id=active_user[0]['id']) # اگر کاربر با یک آی پی دیگر لاگین است لاگ اوت شود
        active_user=list_user.get(address=ip)

        if active_user:
            print('کاربر دیگری با همین آی پی لاگین بوده')
            list_user.remove(id=active_user[0]['id']) # اگر کاربر دیگری با این آی پی لاگین است لاگ اوت شود
        return False,
    except RouterException.RouterOsApiCommunicationError as e:
        message="Radius Error: "
        if hasattr(e, 'original_message'):
            message=message+e.original_message.decode('unicode-escape').encode('latin1').decode('utf-8')
            print(message)
        else:
            print(message)        
        return (False,message)

def mikrotik_logout(username):
    try:
        connection = routeros_api.RouterOsApiPool(settings.MIKROTIK_IP,
                                                username=settings.MIKROTIK_ADMIN_USER, password=settings.MIKROTIK_ADMIN_PASSWORD,
                                                port=int(settings.MIKROTIK_API_PORT),
                                                use_ssl=True,
                                                ssl_verify=False,
                                                ssl_verify_hostname=False,
                                                ssl_context=None, plaintext_login=True)
        api = connection.get_api()
        list_user = api.get_resource('/ip/hotspot/active')
        active_user = list_user.get(user=username)
        if active_user:
            list_user.remove(id=active_user[0]['id'])
        return True,
    except RouterException.RouterOsApiCommunicationError as e:
        message="Radius Error: "
        if hasattr(e, 'original_message'):
            message=message+e.original_message.decode('unicode-escape').encode('latin1').decode('utf-8')
            print(message)
        else:
            print(message)        
        return (False,message)




#    profile = Profile.objects.get(user=request.user) if Profile.objects.filter(user=request.user).exists() else None   
#     accounting = Accounting.objects.filter(user=request.user) if Accounting.objects.filter(user=request.user).exists() else None 
#     jdate=jdatetime.date.today()
#     todaysum=0
#     if accounting is not None:
#         todaysum_obj=Accounting.objects.filter(user=request.user,login_time__date=date.today())
#         todaysum=sum(todaysum_obj.values_list('acct_input_octets',flat=True))+sum(todaysum_obj.values_list('acct_output_octets',flat=True))
#     if request.user.profile is not None:
#         profile=request.user.profile
#     elif request.user.organization is not None:
#         if request.user.organization.profile is not None:
#             profile=request.user.organization.profile    
#     else:
#         pass
#     todaysum_day=0
#     todaysum_month=0
#     total_limit_day=0
#     if profile:
#         if profile.is_limit_download:
#             if profile.daily_download>0:
#                 todaysum_obj_day=Accounting.objects.filter(user=request.user,login_time__date=date.today())
#                 todaysum_day=sum(todaysum_obj_day.values_list('acct_input_octets',flat=True))+sum(todaysum_obj_day.values_list('acct_output_octets',flat=True))
#                 total_limit_day= profile.daily_download*1024*1024-todaysum_day
#             if profile.monthly_download>0:
#                 date1=jdatetime.JalaliToGregorian(jdate.year,jdate.month,1)    
#                 start_date = date(year=date1.gyear,month=date1.gmonth,day=date1.gday)
#                 todaysum_obj_month=Accounting.objects.filter(user=request.user,login_time__date__gte=start_date)
#                 todaysum_month=sum(todaysum_obj_month.values_list('acct_input_octets',flat=True))+sum(todaysum_obj_month.values_list('acct_output_octets',flat=True))
#                 total_limit_month= profile.monthly_download*1024*1024-todaysum_month        