from .models import Authenticate,Accounting
from django import forms
class AuthenticateForm(forms.ModelForm): 
    # captcha = CaptchaField()
    class Meta():
        model = Authenticate

class AccountingForm(forms.ModelForm): 
    # captcha = CaptchaField()
    class Meta():
        model = Accounting