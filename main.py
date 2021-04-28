#! /usr/bin/python3
"""
    HG532D-Status-Collector: This is a helper script to collect device status data for Zabbix NMS.
    
    The status data collected can be piped into other network monitoring tools with some custom 
    preprocessing done. The status data is returned in JSON format.
    This script was tested on Zabbix NMS, but can be modified to run on other monitoring servers which 
    have a Python 3 runtime.
    
    For performance reasons, try not to run this script with small time intervals of less than a minute.
    Suggested setting interval duration of at least 1 minute.
    
    To begin usage, make sure to change the TARGET, USERNAME, and PASSWORD variabes to match your device's
    values.

    Usage:
        python3 main.py all
        python3 main.py [statusGroup] [statusItem]

    Example:
        python3 main.py DsLinkInfo DownLineAttenuation
        python3 main.py DsLinkInfo DslStatus
        python3 main.py InternetStatus OnlineDuration
        python3 main.py WifiBwUsage BytesSend

    Author: Wilfred Wulbou
    License: MIT
"""

import requests
import base64
import hashlib
import sys
import re
import json

TARGET = "192.168.1.1"
USERNAME = "user"
PASSWORD = "user"

paths = {
    "DslLinkInfo": {
        "path": "/html/status/dslinfo.asp",
        "regex": r'(?:var\s+DSLCfg\s=\snew\sArray\(new\s+stDsl\()\"(?P<IgDevice>[a-zA-Z0-9_.]+)\"\,\"(?P<LineStd>[a-zA-Z0-9_.]+)\"\,\"(?P<DslStatus>[a-zA-Z0-9_.]+)\"\,\"(?P<UpLineRate>[a-zA-Z0-9_.]+)\"\,\"(?P<DownLineRate>[a-zA-Z0-9_.]+)\"\,\"(?P<UpMaxLineRate>[a-zA-Z0-9_.]+)\"\,\"(?P<DownMaxLineRate>[a-zA-Z0-9_.]+)\"\,\"(?P<UpNoiseSafeCoeff>[a-zA-Z0-9_.]+)\"\,\"(?P<DownNoiseSafeCoeff>[a-zA-Z0-9_.]+)\"\,\"(?P<UpIntlDepth>[a-zA-Z0-9_.]+)\"\,\"(?P<DownIntlDepth>[a-zA-Z0-9_.]+)\"\,\"()\"\,\"(?P<UpLineAttenuation>[a-zA-Z0-9_.]+)\"\,\"(?P<DownLineAttenuation>[a-zA-Z0-9_.]+)\"\,\"(?P<UpOutputPwr>[a-zA-Z0-9_.]+)\"\,\"(?P<DownOutputPwr>[a-zA-Z0-9_.]+)\"\,\"(?P<ChType>[a-zA-Z0-9_.]+)'
    },
    "InternetStatus": {
        "path": "/html/status/internetstatus.asp",
        "regex": r'(?:var\sWanPPP\s=\snew\sArray\(new\sstWanPPP\()\"(?P<IgDevice>[a-zA-Z0-9._]+)\"\,\"(?P<ConnName>[a-zA-Z0-9._]+)\"\,\"(?P<IPv4Status>[a-zA-Z0-9._]+)\"\,\"(?P<IPv4Addr>[a-zA-Z0-9._]+)\"\,\"(?P<PrimaryDNS>[0-9.]+)\,(?P<SecondaryDNS>[0-9.]+)\"\,\"(?P<GatewayIP>[0-9.]+)\"\,\"(?P<OnlineDuration>[0-9]+)'
    },
    "WifiBwUsage": {
        "path": "/html/status/wlaninfo.asp",
        "regex": r'(?:var\sPacketInfo\s=\s\[\[\")(?P<IgDevice>[a-zA-Z0-9._]+)\"\,\"(?P<BytesSend>[0-9]+)\"\,\"(?:[0-9]+)\"\,\"(?P<BytesReceive>[0-9]+)'
    }
}

class StatsCollector:
    def __init__(self,):
        self.session = None
    
    def __enter__(self):
        # print('__enter___')
        self.session = self.getLoginSession()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # print('__close___')
        self.close()
    
    def getLoginSession(self):
        #   Initialize login credentials data.
        passwd_enc = PASSWORD.encode()
        m = hashlib.sha256()
        m.update(passwd_enc)
        loginformdata = {'Username': USERNAME, 'Password': base64.b64encode(m.hexdigest().encode())}

        #   Following cookies are needed for a successful login.
        cookieJar = requests.cookies.RequestsCookieJar()
        cookieJar.set('Language', 'en', domain=TARGET, path='/')
        cookieJar.set('FirstMenu', 'Admin_0', domain=TARGET, path='/')
        cookieJar.set('SecondMenu', 'Admin_0_0', domain=TARGET, path='/')
        cookieJar.set('ThirdMenu', 'Admin_0_0_0', domain=TARGET, path='/')

        session = requests.session()
        session.cookies = cookieJar
        # Login
        session.post(url="http://{}/index/login.cgi".format(TARGET), data=loginformdata)

        return session

    def getAllStats(self):
        """ 
            Collects all status information from HG532D device.

            Args:
                none

            Returns:
                statuses: 
                    a dict containing containing all status information
        """

        statuses = {}
        with self.session as s:
            # All status
            for statusGroup in paths.keys():
                # print('statusGroup: {}'.format(statusGroup))
                response = s.get(url="http://{}{}".format(TARGET, paths[statusGroup]["path"]))                
                try:
                    m = re.search(paths[statusGroup]["regex"], response.text, re.S)
                    # print(m.groupdict())
                    status = { statusGroup: m.groupdict() }
                    # print('status: {}'.format(status))
                    statuses.update(status)
                except Exception as e:
                    status = {statusGroup: "None: Unable to pull data"}
                    statuses.update(status)
        return statuses

    def getStat(self, statusGroup, statusItem):
        """ 
            Collects single status information from HG532D device.

            Args:
                statusGroup: 
                    a string value representing the group of status information. Eg. "DslLinkInfo"
                statusItem: 
                    a string representing the single status information from the group. Eg. DownLineRate

            Returns:
                status: 
                    a dict containing containing all status information
        """

        status = {}
        response = self.session.get(url="http://{}{}".format(TARGET, paths[statusGroup]["path"]))
        try:
            m = re.search(paths[statusGroup]["regex"], response.text, re.S)
            # print(m.groupdict())
            status = { statusGroup: {statusItem: m.group(statusItem) }}
        except Exception as e:
            status = { statusGroup: {statusItem: "None: Unable to pull data"}}
        
        return status

    def close(self):
        self.session.post(url="http://{}/index/logout.cgi".format(TARGET))
        self.session.close()

def main():
    """ Main function """
    try:
        with StatsCollector() as statsCollector:
            # Validate cmdline inputs
            if len(sys.argv) < 2:
                print("Usage Error: Incorrect number of arguments")
                sys.exit(1)
            if (sys.argv[1] != "all" and sys.argv[1] not in paths.keys()):
                print("Error: `{}` is not a valid argument".format(sys.argv[1]))
                sys.exit(1)
            if sys.argv[1] == "all":
                print(json.dumps(statsCollector.getAllStats()))
                sys.exit(0)
            else:
                print(json.dumps(statsCollector.getStat(sys.argv[1], sys.argv[2])))

    except OSError as e:
        statuses = {"msg": "Error: Network unreachable"} 
        print(json.dumps(statuses))
    except Exception as e:
        raise e

if __name__ == "__main__":
    main()