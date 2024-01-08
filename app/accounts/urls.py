from django.urls import path, include
from accounts.views import *
from django.contrib.auth import views as auth_views
app_name='accounts'

urlpatterns = [
    path('login',login_view,name='login'),
    path('user',UserListView.as_view(),name='user-list'),
    path('user/create',UserCreate.as_view(),name='user-create'),
    path('user/<int:pk>/edit',UserEdit.as_view(),name='user-edit'),
    path('users/<int:pk>/edit',UsersEdit.as_view(),name='users-edit'),
    path('user/<int:pk>/delete',UserDelete.as_view(),name='user-delete'),
    path('resetpassword/',PasswordResetByUser.as_view(),name='reset-password'),
    path('mobileverification/<int:pk>/<str:expire_at>',mobile_verification_check_view,name='mobile-verification-check'),
    path('user/deactive/<int:pk>',user_deactive,name='user-deactive'),
    path('user/active/<int:pk>',user_active,name='user-active'),
    path('user/changepassword/<int:pk>',user_change_password,name='user-changepassword'),
    path('profile',ProfileListView.as_view(),name='profile-list'),
    path('profile/create',ProfileCreate.as_view(),name='profile-create'),
    path('profile/<int:pk>/edit',ProfileEdit.as_view(),name='profile-edit'),
    path('profile/<int:pk>/delete',ProfileDelete.as_view(),name='profile-delete'),
    path('organization/<int:pk>/edit',OrganizationEdit.as_view(),name='organization-edit'),
    path('voucher',VoucherListView.as_view(),name='voucher-list'),
    path('voucher/create',VoucherCreate.as_view(),name='voucher-create'),
    path('voucher/<int:pk>/edit',VoucherEdit.as_view(),name='voucher-edit'),
    path('voucher/csvexport',voucher_csvexport,name='voucher-csvexport'),

    path('captcha/', include('captcha.urls')),
    path('payment',payment,name='payment'),
    path('paymentresult',paymentresult,name='paymentresult'),
]
    # path('user',UserView.as_view(),name='user'),
    # path('user',user_view,name='user'),
    # path('mobileverification/',MobileVerificationView.as_view(),name='mobile-verification'),
    # path('login/accounting',login_accounting_view,name='login_accounting'),
    # path('logout',logout_view,name='logout'),
    # path('time',calltime,name='time'),
    # path('calltime',cal_time,name='calltime'),
    # path('mobileverification/',mobile_verification_view,name='mobile-verification'),
