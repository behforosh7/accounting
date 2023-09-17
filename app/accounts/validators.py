import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_mobile_number(value):
    pattern = "^989(1[0-9]|2[0-9]|3[0-9]|9[0-9])[0-9]{7}$"
    regex=r'^09(1[0-9]|3[1-9]|2[1-9]|0[0-3]|9[0-3])-?[0-9]{3}-?[0-9]{4}$'
    if not re.match(pattern, str(value)):
        if not re.match(regex, str(value)):
            raise ValidationError(_("شماره موبایل معتبر نیست"))
    return value


def validate_phone_number(value):
    pattern = "^0[1-9]{2}-[0-9]{8}$"
    if not re.match(pattern, str(value)):
        raise ValidationError(_("شماره تلفن معتبر نیست"))

    return value


def validate_postal_code(value):
    pattern = r"\b(?!(\d)\1{3})[13-9]{4}[1346-9][013-9]{5}\b"
    if not re.match(pattern, str(value)):
        raise ValidationError(_("کد پستی معتبر نیست"))

    return value


def validate_national_id(value):
    error_message = "کد ملی معتبر نیست"

    if not re.search(r"^\d{10}$", value):
        raise ValidationError(_(error_message))

    check = int(value[9])
    s = sum([int(value[x]) * (10 - x) for x in range(9)]) % 11
    if not ((s < 2 and check == s) or (s >= 2 and check + s == 11)):
        raise ValidationError(_(error_message))

    return value


def validate_persian_text(value):
    pattern = r"^[\u0600-\u06FF\s0-9 ‌ $&+,:;=?@#|\"'<>.^*()%!-_]+$"
    if not re.match(pattern, value):
        raise ValidationError(_("کارکتر غیر فارسی استفاده شده است"))

    return value
