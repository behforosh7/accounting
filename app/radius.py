from __future__ import print_function
from pyrad import dictionary, packet, server
from pyrad.tools import *
import logging
import socketserver
import django
import os
from datetime import date
import signal
import sys
# logging.basicConfig(filename="pyrad.log", level="DEBUG",
#                      format="%(asctime)s [%(levelname)-8s] %(message)s")
online_users={}
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()
from django.contrib.auth import authenticate
from radiuslog.models import *
from django.utils import timezone
from django.utils.timezone import timedelta
from django.db.models import Sum
from django.utils.timezone import datetime
import jalali_date
from django.conf import settings
from accounts.models import Voucher,VoucherType
timezone.activate('Asia/Tehran')
HOST, PORT = "0.0.0.0", int(settings.LOG_SERVER_PORT)

def _startdate():
    vouchers=Voucher.objects.all()
    for voucher in vouchers:
        if not voucher.start_date and voucher.used>0:
            voucher.start_date=voucher.created_date
            voucher.save()

class RadiusServer(server.Server):
    def _isauthenticate(self,uname,pwd):
        user = authenticate(request=None,username=uname, password=pwd)
        if user is not None:
            return user
        else:
            return None

                    
    def account_reply(self,user):
        def voucher_count(total_usage,voucher):
            if voucher.voucher_type.upload_speed>0:
                rate_limit=str(voucher.voucher_type.upload_speed) + 'M/'
            if voucher.voucher_type.download_speed>0:
                rate_limit=rate_limit+str(voucher.voucher_type.download_speed) + 'M' 
            total_limit=(voucher.voucher_type.volume*1024*1024)-total_usage
            total_limit=divmod(total_limit,4294967296)
            return [rate_limit,total_limit]   
        
        vouchers=Voucher.objects.filter(user=user,is_valid=True).order_by('id')   
        if vouchers:
            voucher=vouchers[0]
            if not voucher.start_date and voucher.used==0:
                voucher.start_date=timezone.now()
                voucher.save()

        else:
            reply_message=u'عدم وجود بسته اینترنتی برای کاربر'
            reply={"Reply-Message": reply_message,}     
            return(False,reply)
        
        if voucher.start_date:
            start_date=voucher.start_date
        else:
            start_date=voucher.created_date       

        used_sum=Accounting.objects.filter(user=user,login_time__gte = start_date).aggregate(download=Sum('acct_output_octets'),upload=Sum('acct_input_octets'))
        if not used_sum['download']:
            download=0
        else:
            download=used_sum['download']
        if not used_sum['upload']:
            upload=0
        else:
            upload=used_sum['upload']
        
        total_usage=download+upload
        if total_usage/(1024*1024)<voucher.voucher_type.volume:
            limit=voucher_count(total_usage,voucher)
            voucher.pre_used=total_usage
            voucher.used=total_usage  #/(1024*1024)
            voucher.save()
        else:
            voucher.is_valid=False
            voucher.used=total_usage #/(1024*1024)
            voucher.save()
            if vouchers.count()>1:
                voucher=vouchers[1]
                limit=voucher_count(0,voucher)
                voucher.start_date=timezone.now()
                voucher.save()
            else:
                reply_message=u'عدم وجود بسته اینترنتی برای کاربر'
                reply={"Reply-Message": reply_message,}     
                return(False,reply)


        remain_time=(start_date + timedelta(days=voucher.voucher_type.duration_day)) -timezone.now()
        second=remain_time.days*24*3600+remain_time.seconds
        if second<=0:
            voucher.is_valid=False
            voucher.used=total_usage #/(1024*1024)
            voucher.save()
            second=120
            if vouchers.count()>1:
                voucher=vouchers[1]
                limit=voucher_count(0,voucher)
                voucher.start_date=timezone.now()
                voucher.save()
                remain_time=(start_date + timedelta(days=voucher.voucher_type.duration_day)) -timezone.now()
                second=remain_time.days*24*3600+remain_time.seconds
            else:
                reply_message=u'عدم وجود بسته اینترنتی برای کاربر'
                reply={"Reply-Message": reply_message,}     
                return(False,reply)

        rate_limit=limit[0]
        total_limit=limit[1]    
        reply_message='User Authenticate Successfully'
        reply={"Idle-Timeout":'604800',"Service-Type": "Framed-User",
                        "Session-Timeout":second,
                        "Mikrotik-Rate-Limit": rate_limit,
                        "Mikrotik-Total-Limit": total_limit[1],
                        "Mikrotik-Total-Limit-Gigawords": total_limit[0],
                        "Reply-Message": reply_message,}
        
        return (True,reply)
    def HandleAuthPacket(self, pkt):
        pwd = pkt.PwDecrypt(pkt['User-Password'][0])
        uname = pkt['User-Name'][0]
        try:
            user=self._isauthenticate(uname,pwd)
            if user is not None:
                self.auth_save(user,pkt)
                ip_addr=pkt['Framed-IP-Address'][0]
                online_users[ip_addr]=user
                acc_reply=self.account_reply(user)
                reply = self.CreateReplyPacket(pkt, **acc_reply[1])
                if acc_reply[0]:
                    reply.code = packet.AccessAccept
                else:
                    reply.code = packet.AccessReject
                # reply = self.CreateReplyPacket(pkt, **self.account_reply(user))
                # reply.code = packet.AccessAccept
            else:
                reply_message='user name or password not match'
                reply = self.CreateReplyPacket(pkt, **{
                    "Reply-Message": reply_message,})
                reply.code = packet.AccessReject
        except Exception as e:
            print("Oops!", e, "occurred on Authentication.")  
        self.SendReplyPacket(pkt.fd, reply)

    def HandleAcctPacket(self, pkt):
        try:
            reply = self.CreateReplyPacket(pkt)
            self.SendReplyPacket(pkt.fd, reply)
            ip_addr=pkt['Framed-IP-Address'][0]
            user=online_users.get(ip_addr)
            if user:
                self.accounting_save(user,pkt)
                if pkt['Acct-Status-Type'][0]=='Stop':
                    online_users.pop(ip_addr) 
            else:
                auth=Authenticate.objects.filter(user_ip_address=ip_addr).last()
                if auth:
                    user=auth.user
                    self.accounting_save(user,pkt)
                    online_users[ip_addr]=user
                    if pkt['Acct-Status-Type'][0]=='Stop':
                        online_users.pop(ip_addr)                     

        except Exception as e:
            print("Oops!", e, "occurred on Accounting.")  
    def auth_save(self,user,Radius_attributes):
        auth=Authenticate()
        auth.user = user #Authenticate.objects[user=user)
        auth.nas_ip_address=Radius_attributes['NAS-IP-Address'][0]
        auth.nas_identifier=Radius_attributes['NAS-Identifier'][0]
        auth.user_ip_address=Radius_attributes['Framed-IP-Address'][0]
        auth.acct_session_id=Radius_attributes['Acct-Session-Id'][0]
        auth.save()
    def accounting_save(self,user,Radius_attributes):
        giga=4294967296
        session_id=Radius_attributes['Acct-Session-Id'][0]
        if Radius_attributes['Acct-Status-Type'][0]=='Start':
            acc=Accounting()
        elif Radius_attributes['Acct-Status-Type'][0]=='Stop':
            acc=(Accounting.objects.filter(user=user,acct_session_id=session_id).exclude(acct_status_type=StatusType.objects.get(name='Stop')))[0]
            acc.logout_time=timezone.now()
            acc.update_time=timezone.now()
        else:
            acc1=Accounting.objects.filter(user=user,acct_session_id=session_id).exclude(acct_status_type=StatusType.objects.get(name='Stop'))
            if acc1:
                acc=acc1[0]
            else:
                acc=Accounting()
            if acc is None:
                return 0
            acc.update_time=timezone.now()
        acc.user=user
        if Radius_attributes.has_key('NAS-IP-Address'):
            acc.nas_ip_address=Radius_attributes['NAS-IP-Address'][0]
        if Radius_attributes.has_key('NAS-Identifier'):
            acc.nas_identifier=Radius_attributes['NAS-Identifier'][0]
        if Radius_attributes.has_key('Framed-IP-Address'):
            acc.user_ip_address=Radius_attributes['Framed-IP-Address'][0]
        if Radius_attributes.has_key('Acct-Session-Id'):
            acc.acct_session_id=Radius_attributes['Acct-Session-Id'][0]
        if Radius_attributes.has_key('Acct-Status-Type'):
            status_type=StatusType.objects.get(name=Radius_attributes['Acct-Status-Type'][0])
            acc.acct_status_type=status_type
        if Radius_attributes.has_key('Acct-Input-Octets'):
            acc.acct_input_octets=int(Radius_attributes['Acct-Input-Octets'][0])
        if Radius_attributes.has_key('Acct-Input-Gigawords'):
            acc.acct_input_octets+=int(Radius_attributes['Acct-Input-Gigawords'][0])*giga
        if Radius_attributes.has_key('Acct-Output-Octets'):
            acc.acct_output_octets=int(Radius_attributes['Acct-Output-Octets'][0])
        if Radius_attributes.has_key('Acct-Output-Gigawords'):
            acc.acct_output_octets+=int(Radius_attributes['Acct-Output-Gigawords'][0])*giga
        if Radius_attributes.has_key('Acct-Input-Packets'):
            acc.acct_input_packets=int(Radius_attributes['Acct-Input-Packets'][0])
        if Radius_attributes.has_key('Acct-Output-Packets'):
            acc.acct_output_packets=int(Radius_attributes['Acct-Output-Packets'][0])
        if Radius_attributes.has_key('Acct-Session-Time'):
            acc.acct_session_time=int(Radius_attributes['Acct-Session-Time'][0])
        if Radius_attributes.has_key('Acct-Terminate-Cause'):
            # acc.acct_terminate_cause=acc.terminate_cause_mapper[Radius_attributes['Acct-Terminate-Cause'][0]]
            acc.acct_terminate_cause=TerminateCause.objects.get(name=Radius_attributes['Acct-Terminate-Cause'][0])
        upload=acc.acct_input_octets
        download=acc.acct_output_octets

        acc.save()
        vouchers=Voucher.objects.filter(user=user,is_valid=True).order_by('id')   
        if vouchers:
            voucher=vouchers[0]
            total_usage=download+upload
            # print('total_usage:', total_usage)
            # duffrence1=voucher.used-total_usage
            # print('duffrence1:', duffrence1)
            # duffrence2=voucher.pre_used-duffrence1
            # print('duffrence2:', duffrence2)
            # voucher.pre_used=voucher.used
            # print('voucher.pre_used:', voucher.pre_used)
            voucher.used=voucher.pre_used+total_usage
            # print('voucher.used', voucher.used)
            voucher.save()
ignor_address_list=['samsungcloud','expressapis','dbankcdn',
'dbank','microsoft','apple.com','gstatic','google','ntp.org'
,'enamad.ir','gvt1.com','gvt2.com','sync.com','adv.']
class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = str(bytes.decode(self.request[0].strip()))
            if data.startswith('dns query from'):
                data_list=data.split('dns query from ')[1].split(' ')
                ip_addr=data_list[0][:len(data_list[0])-1]
                address=data_list[2][:len(data_list[2])-1]
                if ip_addr:
                    user=online_users.get(ip_addr)
                    if user:
                        if not any(ele in address for ele in ignor_address_list):
                            user_log=UserLog()
                            user_log.user=user
                            user_log.user_ip_address=ip_addr
                            user_log.dns_log=address
                            user_log.save()
        except Exception as e:
            print("Oops!", e, "occurred on sysloge.")  
def signal_handler(signal, frame):
    print('\nYou pressed Ctrl+C, keyboardInterrupt detected!')
    print ("Crtl+C Pressed.Radius Shutting down.")
    print ("Crtl+C Pressed.Syslog Shutting down.")

    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)

if __name__ == '__main__':
        try:
            # _startdate()
            srv = RadiusServer(dict=dictionary.Dictionary("dictionary"))
            srv.hosts["0.0.0.0"] = server.RemoteHost("0.0.0.0", bytes(settings.RADIUS_SECRET, encoding= 'utf-8'),
             "mikrotik",settings.RADIUS_PORT,settings.ACCOUNTING_PORT)
            srv.BindToAddress("0.0.0.0")
            signal.signal(signal.SIGINT, signal_handler)
            srv.Run()
            # srv._isauthenticate('09352002000','Qaz@1234')
            print("Run RADIUS server Successfully")
        except Exception as e:
            print("Oops!", e.__class__, "occurred.")
        except KeyboardInterrupt:
            print ("Crtl+C Pressed.Radius Shutting down.")
            
        try:
            print("Run SysLog server Successfully")
            signal.signal(signal.SIGINT, signal_handler)
            server = socketserver.UDPServer((HOST,PORT), SyslogUDPHandler)
            server.serve_forever(poll_interval=0.5)
        except (IOError, SystemExit):
            raise
        except KeyboardInterrupt:
            print ("Crtl+C Pressed.Syslog Shutting down.")









    # def HandleCoaPacket(self, pkt):
    #     print("Received an coa request")
    #     print("Attributes: ")
    #     for attr in pkt.keys():
    #         print("%s: %s" % (attr, pkt[attr]))
    #     reply = self.CreateReplyPacket(pkt)
    #     self.SendReplyPacket(pkt.fd, reply)
    # def HandleDisconnectPacket(self, pkt):
    #     reply = self.CreateReplyPacket(pkt)
    #     # COA NAK
    #     reply.code = 45
    #     self.SendReplyPacket(pkt.fd, reply)


    # if acc.status_mapper[Radius_attributes['Acct-Status-Type'][0]]==2:
    #     session_id=Radius_attributes['Acct-Session-Id'][0]
    #     acc.objects.filter(user=user,acct_session_id=session_id,acct_status_type=3).delete()


        # print("Received an accounting request")
        # print("Attributes: ")
        # for attr in pkt.keys():
        #     print("%s: %s" % (attr, pkt[attr]))




        # if user.profile is not None:
        #     profile=user.profile
        # elif user.organization is not None:
        #     if user.organization.profile is not None:
        #         profile=user.organization.profile
        #     else:
        #         return reply                
        # else:
        #     return reply
        # rate_limit='0'    
        # if profile.is_limit_speed:
        #      rate_limit= profile.upload_speed  + 'M/' + user.profile.download_speed + 'M'
        # total_limit='0'
        # total_limit_gig='0'
        # if profile.is_limit_download:
        #     if profile.daily_download>0:
        #         todaysum_obj=Accounting.objects.filter(user=user,login_time__date=date.today())
        #         todaysum=sum(todaysum_obj.values_list('acct_input_octets',flat=True))+sum(todaysum_obj.values_list('acct_output_octets',flat=True))
        #         total_limit= profile.daily_download*1024*1024-todaysum
        #     else:
        #         if profile.monthly_download>0:
        #             jdate=jalali_date.jdatetime.date.today()
        #             date1=jalali_date.jdatetime.JalaliToGregorian(jdate.year,jdate.month,1)    
        #             start_date = date(year=date1.gyear,month=date1.gmonth,day=date1.gday)
        #             todaysum_obj=Accounting.objects.filter(user=user,login_time__date__gte=start_date)
        #             todaysum=sum(todaysum_obj.values_list('acct_input_octets',flat=True))+sum(todaysum_obj.values_list('acct_output_octets',flat=True))
        #             total_limit= profile.daily_download*1024*1024-todaysum
                    

        # print("Received an disconnect request")
        # print("Attributes: ")
        # for attr in pkt.keys():
        #     print("%s: %s" % (attr, pkt[attr]))                    
