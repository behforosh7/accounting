from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import PasswordChangeView,PasswordResetConfirmView
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.views.generic import FormView,ListView, CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied,ViewDoesNotExist
from django.conf import settings
from .forms import loginform
from .models import User, Profile, Voucher,VoucherType
from .forms import *
from django.urls import reverse
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import permission_required,login_required
from django.http import JsonResponse,HttpResponse,Http404,HttpResponseBadRequest
from datetime import date
from jalali_date import jdatetime,datetime2jalali,date2jalali
from django.utils  import timezone
from django.utils.timezone import timedelta
from django.utils.timezone import datetime
from .isikato import IsikatoAPI
import json
from django.core.exceptions import BadRequest
from accounts.utils import queryset_to_csv
import os
import mimetypes
from django.db.models import Value, CharField, ExpressionWrapper
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from Crypto.Util.Padding import pad, unpad
timezone.activate('Asia/Tehran')
from jdatetime import datetime as jdatetime
from Crypto.Cipher import PKCS1_OAEP
@permission_required('accounts.add_user')
def voucher_csvexport(request):
    try:
        csv_file_path=os.path.join(settings.MEDIA_ROOT,'voucher.csv')
        voucher_csv=Voucher.objects.values('user__username','user__organization__name','voucher_type__name'
                                  ,'used','is_valid','assign_by__username','start_date'
                                  ).order_by('-id') 
    #     voucher_csv = Voucher.objects.all().values('user__username','user__organization__name','voucher_type__name'
    #                               ,'used','is_valid','assign_by__username','start_date'
    #                               ).order_by('-id').annotate(
    #                                 jalali_date=ExpressionWrapper(
    #     Value(datetime2jalali('start_date').strftime('%Y-%m-%d')),
    #     output_field=CharField()
    # ))
        queryset_to_csv(voucher_csv,csv_file_path)
        if os.path.exists(csv_file_path):
            mime_type, _ = mimetypes.guess_type(csv_file_path)                
            with open(csv_file_path, 'rb') as fh:    
                response = HttpResponse(fh.read(), content_type=mime_type)    
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(csv_file_path)    
                return response                                           

    except Exception as e:
        messages.add_message(request, messages.ERROR, e) 
    return redirect('/')   

# def calltime(request):
#     return render(request, 'accounts/onlineusers.html')

# def cal_time(request):
#     #Time Calculations Performed Here
#     time1=datetime.now()
#     print(time1.hour)
#     time_dict={'days': time1.microsecond, 'hours': time1.hour, 'minutes': time1.minute, 'seconds': time1.second}
#     return JsonResponse(time_dict)
@login_required
def paymentresult(request):
    status_str = request.GET.get('status')
    reference = request.GET.get('ref')
    invoice_number = request.GET.get('invoiceNumber')
    status=False
    if status_str == 'ok':
        params={
            "invoiceNumber":invoice_number,
            "reference":reference,
        }
        isikato=IsikatoAPI()
        result=isikato.check_transaction(params)
        if result["success"]:
            status=True
    
    payments=get_object_or_404(Payment,id=invoice_number,activate=True)
    payments.activate=False
    payments.success=status
    if reference:
        payments.reference=reference
    else:
        payments.message="لغو شده"
    payments.save()
    if status:
        voucher=Voucher()
        voucher.user=payments.user
        voucher.voucher_type=payments.voucher_type
        voucher.assign_by=get_object_or_404(User,username="IGP")
        voucher.save()
        voucher_log_payment(request.user,"Voucher","voucher assigned to user",voucher)                
        payments.voucher=voucher
        payments.save()
    # else:
    #     raise BadRequest
    context={'status': status,'reference': reference,'voucher_type_name': payments.voucher_type.name,'price': payments.amount}
    return render(request, 'accounts/paymentresult.html',context)

@login_required
def payment(request):
    if request.POST:
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.instance.user=request.user
            form.instance.amount= VoucherType.objects.filter(id=form.instance.voucher_type.id)[0].price 
            payment=form.save()
            params={
                "invoiceNumber":str(payment.id),
                "invoiceDate":payment.created_date.strftime("%Y/%m/%d"),
                "amount":payment.amount,
                "mobile":request.user.mobile_nu,
            }

            isikato=IsikatoAPI()
            result=isikato.shaparak(params)
            if result["success"]:
                payment.token=result["token"]
                payment.save()
                return redirect(settings.PAYMENT_URL + "/?token=%s" %payment.token)
            else:
                messages.add_message(request, messages.ERROR, 'خطا در اتصال به درگاه پرداخت')
                return redirect('/accounts/payment')            
            # return JsonResponse(result, safe=False, json_dumps_params={'ensure_ascii': False})            
    form = PaymentForm()
    return render(request, 'accounts/payment.html', {'form': form})

class VoucherCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'accounts.add_user'
    template_name = 'accounts/voucher.html'
    form_class = VoucherForm
    success_url = '/accounts/voucher/create'
    success_message = 'بسته اینترنتی کاربر با موفقیت فعال شد.'
    error_message = 'خطا در هنگام تخصیص بسته به کاربر، لطفا خطاهای زیر را برطرف نمایید!'
    def get_form_kwargs(self):
        kwargs = super(VoucherCreate, self).get_form_kwargs()
        kwargs['request']= self.request
        return kwargs  
    def form_valid(self, form):
        form.instance.assign_by = self.request.user
        try:
            voucher_log(self.request.user,"Voucher","voucher assigned to user",form.instance)                
        except:
            pass
        return super().form_valid(form)


class VoucherListView(PermissionRequiredMixin, ListView):
    permission_required = ['accounts.add_user',
                           'accounts.delete_user', 'accounts.change_user']
    template_name = 'accounts/voucherlist.html'
    context_object_name = 'voucher'
    start_date=timezone.now().date() - timedelta(365)
    end_date=timezone.now().date()    
    search_form = SearchDateForm1()
    org_name=0
    dns_log=''
    username=''
    def post(self, request, *args, **kwargs):
        self.search_form = SearchDateForm1(self.request.POST or None)
        if self.search_form.is_valid():
            self.start_date=timezone.now().date() - timedelta(365)
            self.end_date=timezone.now().date() 
            self.org_name= int(self.search_form.cleaned_data['org_name'])
            self.username= self.search_form.cleaned_data['username']
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
            self.search_form = SearchDateForm1(self.request.POST or None)
        date_str='(' + str(date2jalali(self.start_date)) + ' - ' + str(date2jalali(self.end_date))+ ')'
        self.end_date=self.end_date + timedelta(1)
        search_arg={"created_date__gte":self.start_date, "created_date__lte":self.end_date}
        if self.org_name>0:
            search_arg['user__organization__id']=self.org_name
        if self.username!='':
            search_arg['user__username__contains']=self.username        
        if self.request.user.is_superuser:
            vouchers = Voucher.objects.filter(**search_arg)[:100]
            organizations=Organization.objects.all()
        else:
            search_arg['user__organization__id']=self.request.user.organization.id
            vouchers = Voucher.objects.filter(**search_arg)[:100]
            organizations=Organization.objects.filter(name=self.request.user.organization)
            # vouchers = Voucher.objects.filter(user__organization=self.request.user.organization,created_date__gte=self.start_date, created_date__lte=self.end_date)[:1000]
        context = {'vouchers': vouchers,'organizations':organizations,'date_str':date_str}
        return context


class VoucherEdit(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'accounts.change_user'
    model = Voucher
    template_name = 'accounts/voucher.html'
    form_class = VoucherForm
    success_message = 'تغییرات با موفقیت انچام شد.'
    success_url = '/accounts/voucher'
    def get_initial(self):
        voucher_for_change=Voucher.objects.get(pk=self.kwargs.get('pk'))
        if voucher_for_change.used>0:
            messages.add_message(self.request, messages.ERROR,'این بسته استفاده شده و قابل تغییر نیست')
            raise PermissionDenied
            # return reverse('accounts:voucher-list')
    def get_form_kwargs(self):
        kwargs = super(VoucherEdit, self).get_form_kwargs()
        kwargs['request']= self.request
        return kwargs  
class OrganizationEdit(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'accounts.add_user'
    model = Organization
    template_name = 'accounts/organization.html'
    form_class = OrganizationForm
    success_message = 'تغییرات با موفقیت انچام شد.'
    success_url = '/accounts/organization'

    def get_success_url(self):
        pk = self.kwargs["pk"]
        return reverse("accounts:organization-edit", kwargs={"pk": pk})
class ProfileCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'accounts.add_user'
    template_name = 'accounts/profile.html'
    form_class = ProfileForm
    success_url = '/accounts/profile/create'
    success_message = 'پروفایل کاربران با موفقیت ایجاد شد.'
    error_message = 'خطا در هنگام ایجاد پروفایل کاربران لطفا خطاهای زیر را برطرف نمایید!'
    def form_valid(self, form):
        form.instance.created_user = self.request.user.id
        return super().form_valid(form)


class ProfileListView(PermissionRequiredMixin, ListView):
    permission_required = ['accounts.add_user',
                           'accounts.delete_user', 'accounts.change_user']
    template_name = 'accounts/profilelist.html'
    context_object_name = 'profile'

    def get_queryset(self):
        profiles = Profile.objects.filter(created_user=self.request.user.id)
        context = {'profiles': profiles}
        return context


class ProfileEdit(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'accounts.change_user'
    model = Profile
    template_name = 'accounts/profile.html'
    form_class = ProfileForm
    success_message = 'تغییرات با موفقیت انچام شد.'
    success_url = '/accounts/profile'



class ProfileDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = 'accounts.delete_user'
    model = Profile
    success_url = '/accounts/profile'


class UserCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'accounts.add_user'
    template_name = 'accounts/user.html'
    form_class = SignUpForm
    success_url = '/accounts/user/create'
    success_message = 'کاربر با موفقیت ایجاد شد.'
    error_message = 'خطا در هنگام ایجاد کاربر لطفا خطاهای زیر را برطرف نمایید!'
    def get_form_kwargs(self):
        kwargs = super(UserCreate, self).get_form_kwargs()
        kwargs['request']= self.request
        return kwargs    
    def form_valid(self, form):
        form.instance.created_user = self.request.user.id
        return super().form_valid(form)
class UserListView(PermissionRequiredMixin, ListView):
    permission_required = ['accounts.add_user',
                           'accounts.delete_user', 'accounts.change_user']
    template_name = 'accounts/userlist.html'
    context_object_name = 'users'

    def get_queryset(self):
        if self.request.user.is_superuser:
            users = User.objects.all().order_by('username')[:1000]
        else:
            users = User.objects.filter(organization=self.request.user.organization).order_by('username')[:1000]

        organizations=Organization.objects.all()
        context = {'users': users,'organizations':organizations}
        return context

class PasswordResetByUser(LoginRequiredMixin, SuccessMessageMixin,PasswordChangeView):
    template_name = 'accounts/reset-password.html'
    success_url = '/'
    success_message = 'کلمه عبور با موفقیت تغییر یافت'

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            update_session_auth_hash(self.request, self.request.user)
            self.request.user.force_change_pass = False
            self.request.user.save()            
            users_log(self.request.user,"User","user changed password",self.request.user)                
        except:
            pass
        return super().form_valid(form)    

class UserEdit(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'accounts/user.html'
    form_class = UserForm
    success_message = 'تغییرات با موفقیت انچام شد.'
    success_url = '/'
    def get_initial(self):
        if self.request.user.is_superuser:
            return self.initial
        if self.request.user.is_organization_admin:
            user_for_change=User.objects.get(pk=self.kwargs.get('pk'))
            if user_for_change is None:
                raise  ViewDoesNotExist
            if self.request.user.organization==user_for_change.organization:
                return self.initial

        if self.request.user.id!= self.kwargs.get('pk'):
            raise PermissionDenied
        return self.initial
    def form_valid(self, form):
        try:
            users_log(self.request.user,"User","update",form.instance)                
        except:
            pass 
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context.update({"username":self.object.username})
        return context
class UsersEdit(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'accounts.change_user'
    model = User
    template_name = 'accounts/user.html'
    success_message = 'تغییرات با موفقیت انچام شد.'
    success_url = '/accounts/user'
    form_class = UsersForm
    # def dispatch(self, request, *args, **kwargs):
    #     self.form_class = get_usersform_class(request.user)
    #     return super().dispatch(request, *args, **kwargs)
    def get_initial(self):
        if self.request.user.is_superuser:
            return self.initial
        if self.request.user.is_organization_admin:
            user_for_change=User.objects.get(pk=self.kwargs.get('pk'))
            if user_for_change is None:
                raise  ViewDoesNotExist
            if self.request.user.organization==user_for_change.organization:
                return self.initial
        if self.request.user.id!= self.kwargs.get('pk'):
            raise PermissionDenied
        return self.initial
    def get_form_kwargs(self):
        kwargs = super(UsersEdit, self).get_form_kwargs()
        kwargs['request']= self.request
        return kwargs  
    def form_valid(self, form):
        try:
            users_log(self.request.user,"User","update",form.instance)                
        except:
            pass 
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context.update({"username":self.object.username})
        return context
class UserDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = 'accounts.delete_user'
    model = User
    success_url = '/accounts/user'
    success_url = reverse_lazy('user_list')
    success_message = "کاربر با موفقیت حذف شد"
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.is_superuser:
            raise PermissionDenied("امکان حذف کاربر مدیر وجود ندارد")
        return obj
@permission_required('accounts.change_user')
def user_deactive(request, pk):
    try:
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            messages.add_message(request, messages.ERROR, 'امکان مسدود کردن کاربر مدیر وجود ندارد')
            return redirect('/accounts/user')
        user.is_active = False
        user.created_user = request.user.id
        user.save()
        messages.add_message(request, messages.SUCCESS,
                             'کاربر با موفقیت غیر فعال شد')
        try:
            users_log(request.user,"User","admin Deactived User",user)                
        except:
            pass                              
    except Exception as e:
        messages.add_message(request, messages.ERROR, e)
    return redirect('/accounts/user')


@permission_required('accounts.change_user')
def user_active(request, pk):
    try:
        user = get_object_or_404(User, pk=pk)
        user.is_active = True
        user.created_user = request.user.id
        user.save()
        messages.add_message(request, messages.SUCCESS,
                             'کاربر با موفقیت فعال شد')
        try:
            users_log(request.user,"User","admin Actived User",user)                
        except:
            pass                             
    except Exception as e:
        messages.add_message(request, messages.ERROR, e)                             
    return redirect('/accounts/user')



def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_REMOTE_ADDR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')    
    return ip


@login_required
def mobile_verification_check_view(request,pk,expire_at):
    if request.method == 'POST':
        form=MobileVerificationForm(request.POST)
        if form.is_valid():
            try:     
                mobile_verif=MobileVerification.objects.get(pk=pk)
                if form.cleaned_data['code']==mobile_verif.code:
                    if mobile_verif.is_expired:
                        messages.add_message(request, messages.ERROR, 'خطا کد اعتبار سنجی منقضی شده است')  
                        return redirect('/')                                  
                    mobile_verif.revoked=True
                    mobile_verif.save()
                    try:
                        user=User.objects.get(id=request.user.id)
                        user.is_mobile_verified= True
                        user.save()
                        messages.add_message(request, messages.SUCCESS, 'شماره موبایل با موفقیت تایید شد')  
                        return redirect('/')
                    except Exception as e:
                        messages.add_message(request, messages.ERROR, e)                       
                else:
                    messages.add_message(request, messages.ERROR, 'کد ارسالی اشتباه است')  
                return redirect('/accounts/mobileverification/'+ str(pk)+ '/' + str(expire_at))
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)  
        else:
            for err_msg in form.errors.values():
                messages.add_message(request, messages.ERROR,err_msg)            
            return redirect('/accounts/mobileverification/'+ str(pk)+ '/' + str(expire_at))

    form=MobileVerificationForm
    context = {'form': form, 'check': True,'pk':pk,'expire_at':expire_at}
    return render(request, 'accounts/mobile-verification.html',context)
@login_required
def mobile_verification_view(request):
    if request.method == 'POST':
        validate=validate_mobile_number(request)
        if validate:
            if request.user.mobile_nu is not None:
                try:     
                    mobile_verif=MobileVerification(user=request.user,mobile_nu=request.user.mobile_nu)           
                    mobile_verif.save()
                    expire=timezone.localtime(mobile_verif.expire_at).strftime('%H:%M:%S')
                    return redirect('/accounts/mobileverification/' + str(mobile_verif.pk)+'/' + str(expire))
                except Exception as e:
                    messages.add_message(request, messages.ERROR, e)  
        else:
            return redirect('/')
    else:
        # mobile_verif=MobileVerification.objects.filter(user=request.user,revoked=False).latest('expire_at')
        mobile_verifs=MobileVerification.objects.filter(user=request.user,revoked=False).order_by('-expire_at')
        if mobile_verifs:
            mobile_verif=mobile_verifs[0]
            if not mobile_verif.is_expired and not mobile_verif.revoked:
                expire=timezone.localtime(mobile_verif.expire_at).strftime('%H:%M:%S')
                return redirect('/accounts/mobileverification/' + str(mobile_verif.pk)+'/' + str(expire))        
    context = {'check': False,}
    return render(request, 'accounts/mobile-verification.html',context)
def validate_mobile_number(request):
    mobile_nu = normalize_mobile_number(request.user.mobile_nu)
    if request.user.is_mobile_verified is True:
        messages.add_message(request, messages.ERROR, "شماره همراه شما قبلا تایید شده است") 
        return  False
        # raise forms.ValidationError(("شماره همراه شما تایید شده است"))
    if request.user.mobile_nu != mobile_nu:
        messages.add_message(request, messages.ERROR, "انجام عملیات امکان‌پذیر نیست.")   
        return  False
    if User.objects.filter(mobile_nu=mobile_nu, is_mobile_verified=True).exists():
        messages.add_message(request, messages.ERROR, "انجام عملیات امکان‌پذیر نیست. با شماره دیگری امتحان کنید.")   
        return  False
    return  True
from Crypto.PublicKey import RSA
import base64
import json
from Crypto.Cipher import PKCS1_v1_5

def login_view(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            privateKey = settings.RSA_KEY.exportKey('PEM')
            RSAprivateKey = RSA.importKey(privateKey)
            cipher = PKCS1_v1_5.new(RSAprivateKey)
            print("*****pass:",request.POST['password'])
            encrypted_data = base64.b64decode(request.POST['password'])
            decrypted_data = cipher.decrypt(encrypted_data, None)
            new_request=request
            post_data = new_request.POST.copy()
            post_data['password'] = decrypted_data
            form = loginform(request=new_request, data=post_data)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')

                user = authenticate(
                    request, username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    return redirect('/')
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
        context = {'form': form, 'accounting': False}
        return render(request, 'accounts/login.html', context)
    else:
        return redirect('/')

@permission_required('accounts.change_user')
def user_change_password(request, pk):
    user_account = get_object_or_404(User, pk=pk)
    if not request.user.is_superuser and request.user.organization != user_account.organization:
        raise PermissionDenied
    if request.method == 'POST':
        user_account.created_user=request.user.id
        form = AdminPasswordChangeForm(user_account, request.POST)
        if form.is_valid():
            try:
                users_log(request.user,"User","admin changed password",user_account)                
            except:
                pass
            try:
                form.save()
                user_account.force_change_pass=True
                user_account.save()
                messages.add_message(request, messages.SUCCESS, 'کلمه عبور با موفقیت تغییر کرد')
            except:
                messages.add_message(request, messages.ERROR, 'تغییر کلمه عبور با خطا مواجه شد!')
            return redirect('/accounts/user')
        else:
            for err_msg in form.errors.values():
                messages.add_message(request, messages.ERROR,err_msg)
    form = AdminPasswordChangeForm(user_account)
    context = {'form': form, 'user_account': user_account}
    return render(request, 'accounts/admin-changepassword.html', context)
def custom_page_not_found_view(request, exception):
    return render(request, "error/404.html", {})

def custom_error_view(request, exception=None):
    return render(request, "error/500.html", {})

def custom_permission_denied_view(request, exception=None):
    return render(request, "error/403.html", {})

def custom_bad_request_view(request, exception=None):
    return render(request, "error/400.html", {})