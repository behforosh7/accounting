from django.contrib import admin
from jalali_date.admin import ModelAdminJalaliMixin, StackedInlineJalaliMixin, TabularInlineJalaliMixin
from .models import *
from jalali_date import datetime2jalali, date2jalali
class AccountingAdmin(TabularInlineJalaliMixin, admin.ModelAdmin):
    model=Accounting
    fieldsets = [
        ('General', {
            'fields': [
                        'user',
                        'nas_ip_address',
                        'nas_identifier',
                        'user_ip_address',
                        'acct_session_id',
                        'acct_status_type', 
            ]
        }),
        ('ِData', {
            'fields' : [
            'acct_input_octets',
            'acct_output_octets',
            'acct_input_packets',
            'acct_output_packets',
            ]
        }),
        ('Detail', {
            'fields' : ['acct_session_time',
            'acct_terminate_cause',
            'logout_time',
            ]
        }),
    ]
    list_display = ('user_ip_address','user','acct_session_id','acct_status_type', 'acct_output_octets', 'acct_input_octets','get_created_jalali')
    list_filter = ('user_ip_address', 'user',)
    search_fields = ('user_ip_address',)
    ordering = ('-id',)
    def get_created_jalali(self, obj):
	    return datetime2jalali(obj.login_time).strftime('%y/%m/%d _ %H:%M:%S')
class UserlogAdmin(TabularInlineJalaliMixin, admin.ModelAdmin):
    model=UserLog
    list_display = ('user', 'user_ip_address','dns_log','get_created_jalali')
    search_fields = ( 'dns_log',)
    list_filter = ('user',)
    def get_created_jalali(self, obj):
	    return datetime2jalali(obj.log_time).strftime('%y/%m/%d _ %H:%M:%S')

    # get_created_jalali.short_description = 'تاریخ ایجاد'
    # get_created_jalali.admin_order_field = 'created'

admin.site.register(Authenticate)
admin.site.register(Accounting,AccountingAdmin)
admin.site.register(UserLog,UserlogAdmin)
admin.site.register(TerminateCause)
admin.site.register(StatusType)

# Register your models here.
