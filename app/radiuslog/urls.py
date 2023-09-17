from django.urls import path
from radiuslog.views import *
app_name='log'

urlpatterns = [
    path('accounting',AccountingListView.as_view(),name='accounting-list'),
    path('accounting-agg',AccountingAggListView.as_view(),name='accounting-agg-list'),
    path('user-usage',UserUsageListView.as_view(),name='user-usage'),
    path('org-usage',OrgUsageListView.as_view(),name='org-usage'),
    path('log',UserLogListView.as_view(),name='log-list'),
]
