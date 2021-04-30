# HG532D Status Collector

## Description
HG532D-Status-Collector: This is a helper script to collect device status data for [Zabbix NMS](https://www.zabbix.com/)
    
The status data collected can be piped into other network monitoring tools with some custom 
preprocessing done. The status data is returned in JSON format.
This script was tested on Zabbix NMS, but can be modified to run on other monitoring servers which 
have a Python 3 runtime.

For performance reasons, try not to run this script with small time intervals of less than a minute.
Suggested setting interval duration of at least 1 minute.

To begin usage, make sure to change the TARGET, USERNAME, and PASSWORD variabes in main.py to match your device's values.

## Usage:
        python3 main.py OPTIONS

## Usage Description
### OPTIONS:
        all: 
                Returns all the status data from the device.

        DslLinkInfo {DslStatus | LineStd | UpLineRate | DownLineRate } : 
                Returns a single status item from DslLinkInfo group.
                See source code script for full listing of status items available for querying.

        InternetStatus {IPv4Status | IPv4Addr | PrimaryDNS | SecondaryDNS | OnlineDurataion}
                Returns a single status item from InternetStatus group.
                See source code script for full listing of status items available for querying.

        WifiBwUsage { BytesSend | BytesReceive}
                Returns a single status item from WifiBwUsage.


### Examples:
        python3 main.py all
        python3 main.py DsLinkInfo DslStatus
        python3 main.py InternetStatus OnlineDuration
        python3 main.py WifiBwUsage BytesSend


# Author
Wilfred Wulbou
# License
MIT