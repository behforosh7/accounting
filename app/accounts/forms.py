from .models import *
from django.contrib.auth.forms import AuthenticationForm,UserCreationForm,UserChangeForm,PasswordChangeForm
from captcha.fields import CaptchaField,CaptchaTextInput
from django import forms
from .helpers import normalize_mobile_number
from django.core.exceptions import ValidationError
class AxesCaptchaForm(forms.Form):
    captcha = CaptchaField(
    required=False, label='', error_messages={'invalid': 'Captcha incorrect!'}
)
class loginform(AuthenticationForm):
    captcha = CaptchaField(
    required=True, label='', error_messages={'invalid': 'کد کپچا صحیح نیست'}
)
    def __init__(self, *args, **kwargs):
            super(loginform, self).__init__(*args, **kwargs)
            self.fields['captcha'].widget.attrs['placeholder'] = 'ورود کد کپچا'
            self.fields['captcha'].widget.attrs['class'] = 'form-control'
            self.fields['captcha'].label = "Captcha"
    class Meta:
        model = User
        fields = ('username', 'password')

class PasswordResetForm(PasswordChangeForm):
    class Meta:
        model = User


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(UserCreationForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is forms.fields.BooleanField:
                visible.field.widget.attrs['class'] = 'form-check-input'
            elif type(visible.field) is forms.models.ModelChoiceField:
               visible.field.widget.attrs['class'] = 'form-select'
            else:
                visible.field.widget.attrs['class'] = 'form-control'
        if not self.request.user.is_superuser:
            self.fields['organization'].queryset = Organization.objects.filter(id=self.request.user.organization.id)        
        # self.fields['profile'].queryset = Profile.objects.filter(created_user=self.request.user.id)
    def clean(self):
        if not self.cleaned_data['organization']:
            self.add_error('organization', 'لطفا سازمان مربوطه را انتخاب نمایید.')
            # raise forms.ValidationError('لطفا سازمان مربوطه را انتخاب نمایید.')
    class Meta:
        model=User
        fields = 'username','first_name','last_name', 'password1', 'password2','organization','is_organization_admin','mobile_nu','is_active'
        # fields = 'username','first_name','last_name', 'password1', 'password2','profile','organization','is_organization_admin','mobile_nu','is_active'
# def get_usersform_class(user):
    # if user.is_organization_admin:
    #     field_list='first_name','last_name','mobile_nu','is_active','is_organization_admin'
    #     # field_list='first_name','last_name','mobile_nu','is_active','is_organization_admin','profile'
    # if user.is_superuser:
    # field_list='username','first_name','last_name','mobile_nu','is_active','organization','is_organization_admin'
        # field_list='username','first_name','last_name','mobile_nu','is_active','organization','is_organization_admin','profile'
class UsersForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(UserChangeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        for visible in self.visible_fields():
            if type(visible.field) is forms.fields.BooleanField:
                visible.field.widget.attrs['class'] = 'form-check-input'
            elif type(visible.field) is forms.models.ModelChoiceField:
                visible.field.widget.attrs['class'] = 'form-select'
            else:
                visible.field.widget.attrs['class'] = 'form-control'
        # self.fields['profile'].queryset = Profile.objects.filter(created_user=self.request.user.id)
        # if instance and instance.pk:
        #     self.fields['username'].widget.attrs['readonly'] = "readonly"        
        if not self.request.user.is_superuser:
            self.fields['organization'].queryset = Organization.objects.filter(id=self.request.user.organization.id)        

    def clean_username(self):
        if self.instance: 
            return self.instance.username
        else: 
            return self.fields['username']                     
    def clean(self):
        if not self.cleaned_data['organization']:
            self.add_error('organization', 'لطفا سازمان مربوطه را انتخاب نمایید.')
                
    class Meta:
        model=User
        fields = 'first_name','last_name','mobile_nu','is_active','organization','is_organization_admin'
        read_only_fields = ("username",)    

    # return UsersForm
class UserForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is forms.fields.BooleanField:
                visible.field.widget.attrs['class'] = 'form-check-input'
            elif type(visible.field) is forms.models.ModelChoiceField:
                visible.field.widget.attrs['class'] = 'form-select'
            else:
                visible.field.widget.attrs['class'] = 'form-control'
        # self.fields['username'].widget.attrs['readonly'] = True
        # self.fields['username'].required = False
    class Meta:
        model=User
        fields = 'first_name','last_name','mobile_nu'
        read_only_fields = ("username",)    
    def clean_username(self):
        if self.cleaned_data['username']:
            raise ValidationError('تغییر نام کاربری امکان پذیر نیست')
        return self.cleaned_data['username']        
class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is forms.fields.BooleanField:
                visible.field.widget.attrs['class'] = 'col-md-6 form-check-input'
            elif type(visible.field) is forms.models.ModelChoiceField:
                visible.field.widget.attrs['class'] = 'col-md-6 form-select'
            else:
                visible.field.widget.attrs['class'] = 'col-md-6 form-control'
        
    class Meta:
        model=Profile
        fields = 'name','download_speed','upload_speed','is_limit_speed','daily_download','monthly_download','is_limit_download','is_voucher'
        # widgets = {"user": forms.HiddenInput()}
class OrganizationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is forms.fields.BooleanField:
                visible.field.widget.attrs['class'] = 'col-md-6 form-check-input'
            elif type(visible.field) is forms.models.ModelChoiceField:
                visible.field.widget.attrs['class'] = 'col-md-6 form-select'
            else:
                visible.field.widget.attrs['class'] = 'col-md-6 form-control'
        
    class Meta:
        model=Organization
        fields = 'name','profile'
class SearchDateForm(forms.Form):
    start_date=forms.CharField(max_length=255, required=False)
    org_name=forms.CharField(max_length=255, required=False)
class SearchDateForm1(forms.Form):
    start_date=forms.CharField(max_length=255, required=False)
    org_name=forms.CharField(max_length=255, required=False)    
    username=forms.CharField(max_length=255, required=False)
class SearchDateForm2(forms.Form):
    start_date=forms.CharField(max_length=255, required=False)
    org_name=forms.CharField(max_length=255, required=False)
    dns_log=forms.CharField(max_length=255, required=False)
    username=forms.CharField(max_length=255, required=False)
class PaymentResultForm(forms.Form):
    success = forms.BooleanField()
    message = forms.CharField(max_length=255)
    token = forms.CharField(max_length=255)
class PaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # self.request = kwargs.pop('request')
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is forms.fields.BooleanField:
                visible.field.widget.attrs['class'] = 'col-md-6 form-check-input'
            elif type(visible.field) is forms.models.ModelChoiceField:
                visible.field.widget.attrs['class'] = 'col-md-6 form-select'
                # visible.field.widget.attrs['data-options'] = '{"removeItemButton":true,"placeholder":true}'
                # visible.field.widget.attrs['id'] = 'organizerSingle'
            else:
                visible.field.widget.attrs['class'] = 'col-md-6 form-control'
       
        self.fields['voucher_type'].widget.attrs['onchange'] = 'selectVoucher()'                
        self.fields['voucher_type'].widget.attrs['id'] = 'vouchertype'   
        self.fields['user'].widget.attrs['readonly'] = True
        self.fields['user'].widget.attrs['hidden'] = True
        self.fields['user'].required = False
        self.fields['amount'].widget.attrs['readonly'] = True
        self.fields['amount'].widget.attrs['hidden'] = True
        self.fields['amount'].required = False

    class Meta:
        model=Payment
        fields = 'voucher_type','amount','user'
        read_only_fields = ("amount",)    
class VoucherForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if type(visible.field) is forms.fields.BooleanField:
                visible.field.widget.attrs['class'] = 'col-md-6 form-check-input'
            elif type(visible.field) is forms.models.ModelChoiceField:
                visible.field.widget.attrs['class'] = 'col-md-6 form-select js-choice'
                visible.field.widget.attrs['data-options'] = '{"removeItemButton":true,"placeholder":true}'
                visible.field.widget.attrs['id'] = 'organizerSingle'
            else:
                visible.field.widget.attrs['class'] = 'col-md-6 form-control'
        if not self.request.user.is_superuser:
            self.fields['user'].queryset = User.objects.filter(organization=self.request.user.organization)

    class Meta:
        model=Voucher
        fields = 'user','voucher_type','is_valid'
        read_only_fields = ("used",)
        # widgets = {"user": forms.HiddenInput()}
class MobileField(forms.CharField):
    def __init__(self, **kwargs):
        super(MobileField, self).__init__(**kwargs)
        self.validators.append(validate_mobile_number)
    def to_internal_value(self, data):
        value = super(MobileField, self).to_internal_value(data)
        value = normalize_mobile_number(value)
        return value
class MobileVerificationForm(forms.Form):
    code=forms.CharField(max_length=6)


# class MobileVerificationForm(forms.ModelForm):
#     # mobile_number = MobileField(label=_("شماره همراه"))
#     # # ttl = forms.formMethodField()
#     class Meta:
#         model=MobileVerification
#         fields = ["code","mobile_nu","user"]
#     def customSave(self):
#         mobile_verify = self.save(commit=False)
#         mobile_verify.save()
#         return mobile_verify
    # def __init__(self, init_user, init_mobile_nu,postrequest, *args, **kwargs):
    #     super(MobileVerificationForm, self).__init__(*args, **kwargs)
    #     if postrequest:
    #         self.fields['user'] = init_user
    #         self.fields['mobile_nu'] = init_mobile_nu
 

    # read_only_fields = ("expire_at",)
    # def clean(self):
    #     super().clean()
    #     self.instance.user = self.request.user.id
    #     self.instance.mobile_nu = self.request.user.mobile_nu
         
    #     # for form in self.forms:
    #     # print(vars(self))
    #     # print(self.fields['mobile_nu'])
    #     # validate_mobile_number(self.fields['mobile_nu'])
    #     # mobile_nu = normalize_mobile_number(self.mobile_nu)
    #     # print(mobile_nu)
    #     # self.mobile_nu = mobile_nu
    #     # self.cleaned_data['mobile_nu'] = mobile_nu
    #     # update the instance value.
    #     try:
    #         if MobileVerification.objects.get(
    #             mobile_number=self.get("mobile_number"),
    #             expire_at__gte=now(),
    #             revoked=False,):
    #             raise forms.ValidationError(("شماره همراه شما هنوز در مرحله تایید است  ")) 
    #     except MobileVerification.DoesNotExist:
    #         pass
            

    # def validate_mobile_number(self, value):
    #     mobile_nu = normalize_mobile_number(value)

    #     if request := self.context.get("request", None):
    #         if request.user.is_authenticated:

    #             if request.user.is_mobile_verified is True:
    #                 raise forms.ValidationError(("شماره همراه شما تایید شده است"))

    #             # Logged in user, is trying to request a verification code for
    #             # a mobile number not in its own account
    #             if request.user.mobile_nu != mobile_nu:
    #                 raise forms.ValidationError(("انجام عملیات امکان‌پذیر نیست."))

    #     # Mobile number already verified and is in use
    #     if User.objects.filter(mobile_nu=mobile_nu, is_mobile_verified=True).exists():
    #         raise forms.ValidationError(("انجام عملیات امکان‌پذیر نیست. با شماره دیگری امتحان کنید."))

    #     return value

