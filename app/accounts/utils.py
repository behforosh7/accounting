from djqscsv import write_csv

def queryset_to_csv(qs,file_path):
    field_header={
        'user__username':'کاربر',
        'user__organization__name':'سازمان',
        'voucher_type__name':'نوع بسته',
        'used':'مقدار مصرف شده',
        'is_valid':'فعال',
        'assign_by__username':'کاربر تخصیص دهنده',
        'start_date':'زمان شروع استفاده'
    }
    with open(file_path, 'wb') as csv_file:
        write_csv(qs, csv_file,field_header_map=field_header)
    return True 