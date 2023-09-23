from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView
from .models import *
from django.db.models import Sum
from accounts.models import Organization
from accounts.forms import SearchDateForm,SearchDateForm2
from django.utils  import timezone
from django.utils.timezone import timedelta
from jalali_date import jdatetime,datetime2jalali,date2jalali
from django.contrib import messages
from datetime import date,datetime
import random
import os
import mimetypes
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from djqscsv import write_csv
from django.shortcuts import redirect
from django.http import HttpResponse
from django.db.models import CharField, Value
timezone.activate('Asia/Tehran')

def queryset_to_csv(qs,file_path):
    field_header={
        'user__username':'کاربر',
        'user__organization__name':'سازمان',
        'user_ip_address':'آدرس شبکه کاربر',
        'acct_status_type__name':'نوع لاگ',
        'acct_input_octets':'حجم آپلود',
        'acct_output_octets':'حجم دانلود',
        'acct_input_packets':'تعداد پکت ارسالی',
        'acct_output_packets':'تعداد پکت دریافتی',
        'acct_session_time':'زمان جلسه',
        'acct_terminate_cause__name':'علت خاتمه دادن',
        'login_time':'زمان ورود',
        'logout_time':'زمان خروج',
        'update_time':'زمان آخرین تغییر',
        'jalali_login_time':'زمان آخرین تغییر',
    }
    with open(file_path, 'wb') as csv_file:
        write_csv(qs, csv_file,field_header_map=field_header)
    return True 
@permission_required('accounts.add_user')
def accounting_csvexport(request):
    try:
        csv_file_path=os.path.join(settings.MEDIA_ROOT,'accounting.csv')
        accounting_csv=Accounting.objects.values('user__username','user__organization__name','user_ip_address'
                                  ,'acct_status_type__name','acct_input_octets','acct_output_octets','acct_input_packets'
                                  ,'acct_output_packets','acct_session_time','acct_terminate_cause__name','login_time'
                                  ,'logout_time','update_time'
                                  ).order_by('-id') 
        # print('***************',accounting_csv[0])
        # date1=datetime2jalali(accounting_csv[0]['login_time'])
        # print('***************',date1)
        # accounting_csv.annotate(jalali_login_time=Value(datetime2jalali('login_time'),output_field=CharField()))
        queryset_to_csv(accounting_csv,csv_file_path)
        if os.path.exists(csv_file_path):
            mime_type, _ = mimetypes.guess_type(csv_file_path)                
            with open(csv_file_path, 'rb') as fh:    
                response = HttpResponse(fh.read(), content_type=mime_type)    
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(csv_file_path)    
                return response                                           

    except Exception as e:
        messages.add_message(request, messages.ERROR, e) 
    return redirect('/')   

class OrgUsageListView(PermissionRequiredMixin, ListView):
    permission_required = ['accounts.add_user',
                           'accounts.delete_user', 'accounts.change_user']
    template_name = 'log/org-usage.html'
    context_object_name = 'accounting'
    start_date=timezone.now().date() - timedelta(365)
    end_date=timezone.now().date()    
    search_form = SearchDateForm()
    def post(self, request, *args, **kwargs):
        self.search_form = SearchDateForm(self.request.POST or None)
        if self.search_form.is_valid():
            self.start_date=timezone.now().date() - timedelta(365)
            self.end_date=timezone.now().date() 
            try:
                date1= self.search_form.cleaned_data['start_date']
                if len(date1)==23:
                    sdate=date1[:10]
                    edate=date1[13:23]
                    jd_s=jdatetime.JalaliToGregorian(int(sdate[0:4]),int(sdate[5:7]),int(sdate[8:10]))
                    jd_e=jdatetime.JalaliToGregorian(int(edate[0:4]),int(edate[5:7]),int(edate[8:10]))
                    self.start_date=date(jd_s.gyear,jd_s.gmonth,jd_s.gday)
                    self.end_date=date(jd_e.gyear,jd_e.gmonth,jd_e.gday)
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)
        else:
            messages.add_message(request, messages.ERROR, 'فرمت تاریخ قابل شناسایی نیست')
        return self.get(request, *args, **kwargs)
    def get_queryset(self):
        if self.request.GET:
            self.start_date=timezone.now().date() - timedelta(365)
            self.end_date=timezone.now().date()   
            self.search_form = SearchDateForm(self.request.GET or None)
        date_str='(' + str(date2jalali(self.start_date)) + ' - ' + str(date2jalali(self.end_date))+ ')'
        self.end_date=self.end_date + timedelta(1)
        xAxisData=[]
        download_data=[]
        upload_data=[]
        color_list=[]
        total_usage=[]
        if self.request.user.is_superuser:
            accountings = Accounting.objects.filter(login_time__gte=self.start_date, login_time__lte=self.end_date).values('user__organization__name'
            ).annotate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets')
            ).order_by('-download')[:10]
        else:
            accountings =  Accounting.objects.filter(user__organization=self.request.user.organization,login_time__gte=self.start_date, login_time__lte=self.end_date).values('user__organization__name'
            ).annotate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets')
            ).order_by('-download')[:10]

        for accounting in accountings:
            xAxisData.append(accounting['user__organization__name'])
            download_data.append(accounting['download']//(1024*1024))
            upload_data.append(accounting['upload']//(1024*1024))
            color_list.append("#%06x" % random.randint(0, 0xFFFFFF))
            total_usage.append(accounting['download']//(1024*1024)+accounting['upload']//(1024*1024))
        context = {'color_list':color_list,'total_usage':total_usage,'xAxisData':xAxisData,'download_data':download_data,'upload_data':upload_data,'date_str':date_str}
        return context    
class UserUsageListView(PermissionRequiredMixin, ListView):
    permission_required = ['accounts.add_user',
                           'accounts.delete_user', 'accounts.change_user']
    template_name = 'log/user-usage.html'
    context_object_name = 'accounting'
    start_date=timezone.now().date() - timedelta(365)
    end_date=timezone.now().date()    
    search_form = SearchDateForm
    org_name=0
    def post(self, request, *args, **kwargs):
        self.search_form = SearchDateForm(self.request.POST or None)
        if self.search_form.is_valid():
            try:
                self.start_date=timezone.now().date() - timedelta(365)
                self.end_date=timezone.now().date()  
                date1= self.search_form.cleaned_data['start_date']
                self.org_name= int(self.search_form.cleaned_data['org_name'])
                if len(date1)==23:
                    sdate=date1[:10]
                    edate=date1[13:23]
                    jd_s=jdatetime.JalaliToGregorian(int(sdate[0:4]),int(sdate[5:7]),int(sdate[8:10]))
                    jd_e=jdatetime.JalaliToGregorian(int(edate[0:4]),int(edate[5:7]),int(edate[8:10]))
                    self.start_date=date(jd_s.gyear,jd_s.gmonth,jd_s.gday)
                    self.end_date=date(jd_e.gyear,jd_e.gmonth,jd_e.gday)
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)
        else:
            messages.add_message(request, messages.ERROR, 'فرمت تاریخ قابل شناسایی نیست')
        return self.get(request, *args, **kwargs)
    def get_queryset(self):
        if self.request.GET:
            self.start_date=timezone.now().date() - timedelta(365)
            self.end_date=timezone.now().date()  
            self.search_form = SearchDateForm(self.request.GET or None)
        date_str='(' + str(date2jalali(self.start_date)) + ' - ' + str(date2jalali(self.end_date))+ ')'
        self.end_date=self.end_date + timedelta(1)
        xAxisData=[]
        download_data=[]
        upload_data=[]

        if self.request.user.is_superuser:
            if self.org_name==0:
                accountings = Accounting.objects.filter(login_time__gte=self.start_date, login_time__lte=self.end_date).values(
                'user_ip_address','user__username','user__last_name','user__organization'
                ).annotate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets')
                ).order_by('-download')[:1000]
            else:
                accountings = Accounting.objects.filter(login_time__gte=self.start_date, login_time__lte=self.end_date, user__organization__id=self.org_name).values(
                'user_ip_address','user__username','user__last_name','user__organization'
                ).annotate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets')
                ).order_by('-download')[:1000]

        else:
            accountings =  Accounting.objects.filter(user__organization=self.request.user.organization,login_time__gte=self.start_date, login_time__lte=self.end_date).values(
            'user_ip_address','user__username','user__last_name','user__organization'
            ).annotate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets')
            ).order_by('-download')[:1000]

        for accounting in accountings[:8]:
            xAxisData.append(accounting['user__username'])
            download_data.append(accounting['download']//(1024*1024))
            upload_data.append(accounting['upload']//(1024*1024))

        organizations=Organization.objects.all
        context = {'accounting':accountings, 'xAxisData':xAxisData,'download_data':download_data,'upload_data':upload_data,'organizations':organizations,'date_str':date_str,'form':self.search_form}
        return context
class AccountingListView(PermissionRequiredMixin, ListView):
    permission_required = ['accounts.add_user',
                           'accounts.delete_user', 'accounts.change_user']
    template_name = 'log/accounting.html'
    context_object_name = 'accounting'
    start_date=timezone.now().date() - timedelta(365)
    end_date=timezone.now().date()    
    search_form = SearchDateForm()
    def post(self, request, *args, **kwargs):
        self.search_form = SearchDateForm(self.request.POST or None)
        if self.search_form.is_valid():
            self.start_date=timezone.now().date() - timedelta(365)
            self.end_date=timezone.now().date() 
            try:
                date1= self.search_form.cleaned_data['start_date']
                if len(date1)==23:
                    sdate=date1[:10]
                    edate=date1[13:23]
                    jd_s=jdatetime.JalaliToGregorian(int(sdate[0:4]),int(sdate[5:7]),int(sdate[8:10]))
                    jd_e=jdatetime.JalaliToGregorian(int(edate[0:4]),int(edate[5:7]),int(edate[8:10]))
                    self.start_date=date(jd_s.gyear,jd_s.gmonth,jd_s.gday)
                    self.end_date=date(jd_e.gyear,jd_e.gmonth,jd_e.gday)
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)
        else:
            messages.add_message(request, messages.ERROR, 'فرمت تاریخ قابل شناسایی نیست')
        return self.get(request, *args, **kwargs)
    def get_queryset(self):
        if self.request.GET:
            self.start_date=timezone.now().date() - timedelta(365)
            self.end_date=timezone.now().date()  
            self.search_form = SearchDateForm(self.request.GET or None)
        date_str='(' + str(date2jalali(self.start_date)) + ' - ' + str(date2jalali(self.end_date))+ ')'
        self.end_date=self.end_date + timedelta(1)
                
        if self.request.user.is_superuser:
            accounting = Accounting.objects.filter(login_time__gte=self.start_date, login_time__lte=self.end_date).all().order_by('-update_time__date','user__username')[:1000]
        else:
            accounting = Accounting.objects.filter(user__organization=self.request.user.organization,login_time__gte=self.start_date, login_time__lte=self.end_date).order_by('-update_time__date','user__username')[:1000]
        organizations=Organization.objects.all
        context = {'accounting': accounting,'organizations':organizations,'date_str':date_str}
        return context
class AccountingAggListView(PermissionRequiredMixin, ListView):
    permission_required = ['accounts.add_user',
                           'accounts.delete_user', 'accounts.change_user']
    template_name = 'log/accounting-agg.html'
    context_object_name = 'accounting'
    start_date=timezone.now().date() - timedelta(365)
    end_date=timezone.now().date()    
    search_form = SearchDateForm()
    def post(self, request, *args, **kwargs):
        self.search_form = SearchDateForm(self.request.POST or None)
        if self.search_form.is_valid():
            self.start_date=timezone.now().date() - timedelta(365)
            self.end_date=timezone.now().date() 
            try:
                date1= self.search_form.cleaned_data['start_date']
                if len(date1)==23:
                    sdate=date1[:10]
                    edate=date1[13:23]
                    jd_s=jdatetime.JalaliToGregorian(int(sdate[0:4]),int(sdate[5:7]),int(sdate[8:10]))
                    jd_e=jdatetime.JalaliToGregorian(int(edate[0:4]),int(edate[5:7]),int(edate[8:10]))
                    self.start_date=date(jd_s.gyear,jd_s.gmonth,jd_s.gday)
                    self.end_date=date(jd_e.gyear,jd_e.gmonth,jd_e.gday)
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)
        else:
            messages.add_message(request, messages.ERROR, 'فرمت تاریخ قابل شناسایی نیست')
        return self.get(request, *args, **kwargs)
    def get_queryset(self):
        if self.request.GET:
            self.start_date=timezone.now().date() - timedelta(365)
            self.end_date=timezone.now().date()  
            self.search_form = SearchDateForm(self.request.GET or None)
        date_str='(' + str(date2jalali(self.start_date)) + ' - ' + str(date2jalali(self.end_date))+ ')'
        self.end_date=self.end_date + timedelta(1)
        
        if self.request.user.is_superuser:
            accounting = Accounting.objects.filter(login_time__gte=self.start_date, login_time__lte=self.end_date).values('user__username','user__first_name'
            ,'user__last_name','user__organization__name','user_ip_address','update_time__date'
            ).annotate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets')
            ).order_by('-update_time__date','user__last_name')[:1000]
        else:
            accounting = Accounting.objects.filter(user__organization=self.request.user.organization,login_time__gte=self.start_date, login_time__lte=self.end_date).values('user__username','user__first_name'
            ,'user__last_name','user__organization__name','user_ip_address','update_time__date'
            ).annotate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets')
            ).order_by('-update_time__date','user__last_name')[:1000]            

        organizations=Organization.objects.all
        context = {'accounting': accounting,'organizations':organizations,'date_str':date_str}
        return context
class UserLogListView(PermissionRequiredMixin, ListView):
    permission_required = ['radiuslog.view_userlog']
    template_name = 'log/userlog.html'
    context_object_name = 'userlog'
    start_date=timezone.now() - timedelta(7)
    end_date=timezone.now()    
    search_form = SearchDateForm2()
    org_name=0
    dns_log=''
    username=''
    def post(self, request, *args, **kwargs):
        self.search_form = SearchDateForm2(self.request.POST or None)
        if self.search_form.is_valid():
            self.start_date=timezone.now() - timedelta(7)
            self.end_date=timezone.now() 
            try:
                date1= self.search_form.cleaned_data['start_date']
                self.org_name= int(self.search_form.cleaned_data['org_name'])
                self.dns_log= self.search_form.cleaned_data['dns_log']
                self.username= self.search_form.cleaned_data['username']
                if len(date1)==35:
                    sdate=date1[:10]
                    edate=date1[19:29]
                    stime=date1[11:16]
                    etime=date1[30:35]
                    jd_s=jdatetime.JalaliToGregorian(int(sdate[0:4]),int(sdate[5:7]),int(sdate[8:10]))
                    jd_e=jdatetime.JalaliToGregorian(int(edate[0:4]),int(edate[5:7]),int(edate[8:10]))
                    self.start_date=datetime.strptime(str(jd_s.gyear)+"/"+
                    str(jd_s.gmonth)+"/"+str(jd_s.gday) + ' ' + stime, '%Y/%m/%d %H:%M')
                    self.end_date=datetime.strptime(str(jd_e.gyear)+"/"+
                    str(jd_e.gmonth)+"/"+str(jd_e.gday) + ' ' + etime, '%Y/%m/%d %H:%M')
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)
        else:
            messages.add_message(request, messages.ERROR, 'فرمت تاریخ قابل شناسایی نیست')
        return self.get(request, *args, **kwargs)
    def get_queryset(self):
        if self.request.GET:
            self.start_date=timezone.now() - timedelta(7)
            self.end_date=timezone.now()  
            self.search_form = SearchDateForm2(self.request.GET or None)
        date_str='(' + str(date2jalali(self.start_date)) + ' - ' + str(date2jalali(self.end_date))+ ')'
        search_arg={"log_time__gte":self.start_date, "log_time__lte":self.end_date}
        if self.org_name>0:
            search_arg['user__organization__id']=self.org_name
        if self.dns_log!='':
            search_arg['dns_log__contains']=self.dns_log
        if self.username!='':
            search_arg['user__username__contains']=self.username
        if self.request.user.is_superuser:
            userlog = UserLog.objects.filter(**search_arg)[:1000]
            organizations=Organization.objects.all
        else:
            search_arg['user__organization__id']=self.request.user.organization.id
            userlog = UserLog.objects.filter(**search_arg)[:1000]
            organizations=Organization.objects.filter(name=self.request.user.organization)
            

        context = {'userlog': userlog,'organizations':organizations,'date_str':date_str}
        return context
