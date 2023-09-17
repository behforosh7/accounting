from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple    
from django.contrib.auth.models import Group
from jalali_date import datetime2jalali, date2jalali
from jalali_date.admin import ModelAdminJalaliMixin, StackedInlineJalaliMixin, TabularInlineJalaliMixin

class CustomUserAdmin(TabularInlineJalaliMixin,UserAdmin):
    model=User
    list_display = ('username','mobile_nu','last_name', 'is_staff', 'is_active','organization','is_organization_admin','get_updated_date','created_date','created_user')
    list_filter = ('organization',)
    fieldsets = (
        ('Authentication', {'fields': ('username','mobile_nu', 'password','first_name','last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser','is_mobile_verified')}),
        ('Organization', {'fields': ('organization','is_organization_admin')}),
        ('Profile', {'fields': ('profile',)}),

    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_staff', 'is_active', 'created_user')}
        ),
    )
    search_fields = ('username',)
    ordering = ('username',)
    def get_updated_date(self, obj):
	    return datetime2jalali(obj.updated_date).strftime('%y/%m/%d _ %H:%M:%S')      
class CustomProfileAdmin(TabularInlineJalaliMixin,admin.ModelAdmin):
    model=Profile
    list_display = ('name', 'download_speed','upload_speed','daily_download','get_created_date')
    def get_created_date(self, obj):
	        return datetime2jalali(obj.created_date).strftime('%y/%m/%d _ %H:%M:%S') 

         
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile,CustomProfileAdmin)
admin.site.register(VoucherType)
# admin.site.register(VoucherAssign)
admin.site.register(Organization)
admin.site.register(MobileVerification)
admin.site.register(MobileNuChanged)

class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = []

    # Add the users field.
    users = forms.ModelMultipleChoiceField(
         queryset=User.objects.all(), 
         required=False,
         # Use the pretty 'filter_horizontal widget'.
         widget=FilteredSelectMultiple('users', False)
    )

    def __init__(self, *args, **kwargs):
        # Do the normal form initialisation.
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['users'].initial = self.instance.user_set.all()

    def save_m2m(self):
        # Add the users to the Group.
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        # Default save
        instance = super(GroupAdminForm, self).save()
        # Save many-to-many data
        self.save_m2m()
        return instance
admin.site.unregister(Group)

# Create a new Group admin.
class GroupAdmin(admin.ModelAdmin):
    # Use our custom form.
    form = GroupAdminForm
    # Filter permissions horizontal as well.
    filter_horizontal = ['permissions']

# Register the new Group ModelAdmin.
admin.site.register(Group, GroupAdmin)
class PermissionAdmin(admin.ModelAdmin):
    model = Permission
    fields = ['name']

admin.site.register(Permission, PermissionAdmin)
class CustomVoucherAdmin(TabularInlineJalaliMixin,admin.ModelAdmin):
    search_fields = ('user__username','assign_by__username')
    list_filter = ('voucher_type','is_valid')
    model=Voucher
    list_display = ('id','user','voucher_type', 'used','is_valid','assign_by','get_start_date','get_created_date')
    def get_start_date(self, obj):
        if obj.start_date:
            return datetime2jalali(obj.start_date).strftime('%y/%m/%d _ %H:%M:%S')  
    def get_created_date(self, obj):
	    return datetime2jalali(obj.created_date).strftime('%y/%m/%d _ %H:%M:%S')
admin.site.register(Voucher,CustomVoucherAdmin)

class CustomUsersActivity(TabularInlineJalaliMixin,admin.ModelAdmin):
    search_fields = ('user__username',)
    list_filter = ('event','form')
    model=UserActivity
    list_display = ('id','user','form','event', 'get_created_date')
    def get_created_date(self, obj):
	    return datetime2jalali(obj.created_date).strftime('%y/%m/%d _ %H:%M:%S')    
admin.site.register(UserActivity,CustomUsersActivity)

class CustomPayment(TabularInlineJalaliMixin,admin.ModelAdmin):
    search_fields = ('user__username',)
    list_filter = ('voucher_type','success')
    model=Payment
    list_display = ('user','voucher_type','amount','success','reference','message', 'get_created_date')
    def get_created_date(self, obj):
	    return datetime2jalali(obj.created_date).strftime('%y/%m/%d _ %H:%M:%S')    
admin.site.register(Payment,CustomPayment)