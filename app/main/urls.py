from django.urls import path, include , re_path
from main.views import index,login_accounting_view,logout_view,locked_out
app_name='main'
urlpatterns = [
    path('',index,name='index'),
    path('login',login_accounting_view,name='login'),
    path('logout',logout_view,name='logout'),
    path('captcha/', include('captcha.urls')),
    re_path(r'^locked/$', locked_out, name='locked_out'),
]
