# coding: utf-8
# %
import time
import sys
import datetime
import urllib2
import urllib
import json
import ssl
import smtplib
from email.mime.text import MIMEText
from ntlm import HTTPNtlmAuthHandler


class reStartService:

    def __init__(self, user, pwd, portalUrl, serverAdminUrl, folder):
        self.user = user
        self.pwd = pwd
        self.portalUrl = portalUrl
        self.serverAdminUrl = serverAdminUrl
        self.folder = folder
    # Internal server authentication is federated, so it needs acquire token from portal.
    # External server authentication will acquire token from
    # admin/generatetoken.
    def sendEmail(self, _msg):
        msg = MIMEText(_msg)
        msg["Subject"] = "Printing service restart error!"
        msg["From"] = "" # email from-address
        msg["To"] = ""   # email to-address
        s.sendmail(msg["From"], msg["To"], msg.as_string())

    def getToken(self):
        print "Get Token Access on:" + self.serverAdminUrl
        tokenUrl = "/sharing/generateToken"
        params = {"username": self.user, "password": self.pwd,
                  "referer": self.serverAdminUrl, "f": "json"}
        # print self.user + " " + self.pwd + " " + self.portalUrl + " " + self.serverAdminUrl + " " + self.folder
        passmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passmgr.add_password(None, self.portalUrl, self.user, self.pwd)
        authNTLM = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(passmgr)
        opener = urllib2.build_opener(authNTLM)
        urllib2.install_opener(opener)
        try:
            req = urllib2.Request(self.portalUrl + tokenUrl,
                                  urllib.urlencode(params))
            response = urllib2.urlopen(req)
            data = json.load(response)
            print "Get Token Access on:" + self.serverAdminUrl + " successful!"
            return data['token']
        except Exception as e:
            print e.args
            print "Get Token Access on:" + self.serverAdminUrl + " failed!"
            self.sendEmail(e.args)
            return None

    def call(self):
        user = self.user
        pwd = self.pwd
        portalUrl = self.portalUrl
        serverAdminUrl = self.serverAdminUrl
        folderList = [self.folder]
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        token = self.getToken()
        if token is None:
            raise ValueError('Unable fetch token, token value is None!')
        else:
            serverAdminServicesUrl = serverAdminUrl + "/services"
            print token
            for folder in folderList:
                passmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passmgr.add_password(None, serverAdminUrl, user, pwd)
                authNTLM = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(passmgr)
                opener = urllib2.build_opener(authNTLM)
                urllib2.install_opener(opener)
                try:
                    catalog = json.load(urllib2.urlopen(
                        serverAdminServicesUrl + "/" + "?f=json&token=" + token))
                    print "Root"
                    if "error" in catalog:
                        return
                    folders = catalog['folders']
                    for folder in folders:
                        print folder
                        if "error" in catalog:
                            return
                        if folder == "printtool":
                            catalog = json.load(urllib2.urlopen(
                                serverAdminServicesUrl + "/" + folder + "?f=json&token=" + token))
                            if "error" in catalog:
                                return
                            services = catalog["services"]
                            for service in services:
                                stop = "STOP"
                                start = "START"
                                params = urllib.urlencode(
                                    {'token': token, 'f': 'json'})
                                gpServiceUrl = serverAdminServicesUrl + "/" + folder + \
                                    "/" + service["serviceName"] + \
                                    "." + service['type']
                                req = urllib2.Request(
                                    gpServiceUrl + "/" + stop, params, headers=headers)
                                response = urllib2.urlopen(req)
                                if response.code == 200:
                                    print "Start : %s" % time.ctime()
                                    time.sleep(5)
                                    print "End : %s" % time.ctime()
                                    req = urllib2.Request(
                                        gpServiceUrl + "/" + start, params, headers=headers)
                                    response = urllib2.urlopen(req)
                                    if response.code != 200:
                                        raise IOError('Unable to perform POST request to start the {0} services'.format(
                                            service["serviceName"]))
                                else:
                                    raise IOError('Unable to perform POST request to stop the {0} services!'.format(
                                        service["serviceName"]))
                except Exception as e:
                    print e.args
                    self.sendEmail(e.args)


def main():
    print "Start"
    startTime = time.time()
    now = datetime.datetime.now()
    print now.strftime("%d-%m-%Y_%H-%M")
    print sys.version
    print "*** Restarting printing on Dev Site ***"
    restartDev = reStartService("", "", "https://arcmapsdev.wairc.govt.nz/portal",
                                "https://arcmapsdev.wairc.govt.nz/arcgis/admin", "printtool")
    restartDev.call()
    print "*** Restarting printing on Test Site ***"
    restartTest = reStartService("", "", "https://arcmapstest.wairc.govt.nz/portal",
                                 "https://arcmapstest.wairc.govt.nz/arcgis/admin", "printtool")
    restartTest.call()
    print "*** Restarting printing on Live Site ***"
    restartLive = reStartService("", "", "https://arcmapslive.wairc.govt.nz/portal",
                                 "https://arcmapslive.wairc.govt.nz/arcgis/admin", "printtool")
    restartLive.call()

    print "Finish"
    now = datetime.datetime.now()
    print now.strftime("%d-%m-%Y_%H-%M")
    exit()
if __name__ == '__main__':
    main()
