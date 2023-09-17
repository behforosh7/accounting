import logging
from urllib.parse import urlencode
from django.conf import settings
import requests
logger = logging.getLogger(__name__)

class SendMessage(object):
    def __init__(self, message):
        self.message = message

        self.username = settings.SMS_API_USERNAME
        self.password = settings.SMS_API_PASSWORD

    def sms(self, recipient_number):

        # Stop sending SMS when in DEV
        # if settings.DEVELOPMENT:
        #     return

        url = "https://ws.adpdigital.com/url/send?"
        query_params = {
            "username": self.username,
            "password": self.password,
            "body": self.message,
            "dstaddress": recipient_number,
            "unicode": 1,
        }

        url = url + urlencode(query_params, "utf-8")

        response = requests.get(url)

        if "ID:" not in response.text:
            logger.critical("Something went wrong when trying to send the sms")
            logger.debug(response.text)
            logger.debug(url)
