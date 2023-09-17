import requests
import json
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from pathlib import Path
import base64
from django.conf import settings

class APIException(Exception):
    pass

class HTTPException(Exception):
    pass
class IsikatoAPI(object):
    def __init__(self):
        self.json_str =""

    def _request(self,version, action, method):
        self.json_str=self.json_str.replace(": ",":")
        self.json_str=self.json_str.replace(", ",",")

        url =settings.PAYMENT_URL + '/api/' + version  + '/' + action + '/' + method
        try:
            resp = requests.post(url , headers=self.header(),auth=None,data=self.json_str)
            try:
                if resp.status_code == 200:
                    response_content = json.loads(resp.content.decode("utf-8"))
                else:
                    raise APIException((u'APIException[%s] %s' % (resp.status_code,resp.reason)).encode('utf-8'))
            except ValueError as e:
                raise HTTPException(e)
            return (response_content)
        except requests.exceptions.RequestException as e:
            raise HTTPException(e)
        
    def shaparak(self,params):
        parameters={}
        parameters['invoiceNumber']=params['invoiceNumber']
        parameters['invoiceDate']=params['invoiceDate']
        parameters['terminal']=settings.PYMENT_TERMINAL
        parameters['merchant']=settings.PYMENT_MERCHANT
        parameters['amount']=params['amount']
        parameters['redirectAddress']=settings.PAYMENT_REDIRECT_URL
        parameters['action']='PAY-SHAPARAK'
        parameters['mobile']=params['mobile']
        parameters['account']=settings.PYMENT_ACCOUNT
        self.json_str = json.dumps(parameters)
        return self._request('v2','token', 'get')
    def check_transaction(self,params):
        parameters={}
        parameters['invoiceNumber']=params['invoiceNumber']
        parameters['reference']=params['reference']
        parameters['terminal']=int(settings.PYMENT_TERMINAL)
        parameters['merchant']=int(settings.PYMENT_MERCHANT)
        self.json_str = json.dumps(parameters)
        
        return self._request('v1','transaction', 'check-transaction')    
    def header(self):
        credentials = ('%s:%s' % (settings.PYMENT_USERNAME, settings.PYMENT_PASSWORD)).encode('ascii')
        encoded_credentials = base64.b64encode(credentials).decode('ascii')        
        return {"Content-Type": "application/json; charset=utf-8",
                        "Authorization":"Basic %s" % encoded_credentials,
                        "sign":self.sign_data()}

    def sign_data(self):
        BASE_DIR = Path(__file__).resolve().parent.parent
        # Hash json string by SHA256
        sha256_hash =SHA256.new(self.json_str.encode())

        # Load private key from file
        with open(BASE_DIR / 'private.pem', 'rb') as key_file:
            private_key = RSA.importKey(key_file.read())
        # Sign the hashed array using the private key
        signature = pkcs1_15.new(private_key).sign(sha256_hash)

        # Convert the array into a HEX string
        hex_str = signature.hex()

        # Convert the generated HEX string to UPPERCASE format
        uppercase_hex_str = hex_str.upper()

        # Print the final result
        return uppercase_hex_str
