import uuid
from datetime import timedelta

from django.utils.deconstruct import deconstructible
from django.utils import timezone
import base64
import hashlib
import os
import random as rnd
import re
import uuid
from django.conf import settings

@deconstructible
class ModelDefaultRandomInt:
    """
    It can be used as a default value for a Model field
    ex:
        product_id = models.CharField(max_length=5, default=ModelDefaultRandomInt(5))

    """

    def __init__(self, length):
        self.length = length

    def func(self):
        return str(uuid.uuid4().int)[-self.length:]

    def __call__(self):
        return self.func()


@deconstructible
class ModelTimeInFuture:
    """
    It can be used as a default value for a Model field
    ex:
        expire_at = models.CharField(max_length=5, default=ModelTimeInFuture(5))
        creates a datetime field 5 minutes in future.

    """

    def __init__(self, minutes):
        self.minutes = minutes

    def func(self):
        return timezone.now() + timedelta(minutes=5)

    def __call__(self):
        return self.func()

def normalize_mobile_number(value):
    """
    Tryies to normalize the mobile number to unique format.

    Supports these formats:
        9xxx    -> 989xx
        09xx    -> 989xx
        989xx   -> 989xx
        9809x   -> 989xx
        +989xx  -> 989xx
        +9809x  -> 989xx
    """
    try:
        value = str(value)
    except TypeError:
        return value

    return re.sub(r"(^09|^\+9809|^\+989|^9809|^989|^9)", "989", value)


def get_choices_key_index_dict(choices: tuple) -> dict:
    """
    Gets a nested tuple of choices, returns key: index dict

    Input:
    (
        ('KEY1', LABEL1),
        ('KEY2', LABEL2),
    )

    Output:
    {
        KEY1: 0
        EEY2: 1
    }

    """
    d = {}
    for inx, (key, __) in enumerate(choices):
        d[key] = inx
    return d


def captcha_challenge():
    return random_digit_challenge()


def random_digit_challenge():
    ret = ""
    for i in range(5):
        ret += str(rnd.randint(0, 9))
    return ret, ret


def math_challenge():
    #  fn = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"]

    operators = ["+", "-", "*"]
    operator = rnd.choice(operators)

    r1 = rnd.randint(0, 9)

    # Set max range when operator is - so we don't end with a nagitive number
    end = r1 if operator == "-" else 9

    r2 = rnd.randint(0, end)

    string = f"{r1}{operator}{r2}"
    answer = str(eval(string))

    return string, answer


def noise_arcs(draw, image):
    size = image.size
    x2, y2 = size
    c = settings.CAPTCHA_FOREGROUND_COLOR

    #  Add static line and arc
    draw.arc([-20, -20, size[0], 20], 0, 295, fill=c)
    draw.line([-20, rnd.randint(10, 60), size[0] + 20, size[1] - 20], fill=c)

    #  And two random line
    for i in range(2):
        x1 = rnd.randint(0, 40)
        y1 = rnd.randint(0, 40)
        draw.line((x1, y1, x2 - x1, y2 - y1), fill=c)

    return draw


def get_random_file_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = str(uuid.uuid4()) + "." + ext
    return os.path.join("files/", filename)


def get_log_level_filter(*levels):
    """
    It creates a log filter with the levels provided, for example:
    get_log_level_filter("DEBUG", "INFO") returns a logger that filters out
    DEBUG and INFO messages and anything else would be threwen away
    """

    def filter(record):
        return True if record.levelname in levels else False

    return filter


def get_str_hash(string, algorithm="sha1", salt=False):
    if salt:
        string = settings.SECRET_KEY + string

    hash_method = getattr(hashlib, algorithm)
    return hash_method(string.encode("utf-8")).hexdigest()


def is_base64(string):
    try:
        return base64.b64encode(base64.b64decode(string)).decode() == string
    except Exception:
        return False


def base64_decode(string):
    return base64.b64decode(string).decode()