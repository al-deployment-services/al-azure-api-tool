al-azure-api-tool
=================
Multi-tools for using the Alert Logic Cloud Insight API and Cloud Defender API to retrieve Azure assets and perform hosts cleanup of offline Agents in the Alert Logic User Interface.

rename_hosts.py
---------------
This will import Azure Virtual Machine names from Cloud Insight assets into Threat Manager protected hosts and Log Manager sources. The script will extract VM names from discovered assets in the Azure subscription ID provided in Cloud Defender environment.

cleanup_hosts.py
----------------
This will delete all defunct hosts (log sources and protected hosts) from the Cloud Defender User Interface. A defunct host is defined as an Agent that has been offline for some specified number of days. The default value is 7 days, however this can be changed under the script in line 17:
```
MIN_DELTA = 7
```

Requirements
------------
* Python 2.x, requests, hkdf
* Alert Logic Account ID (CID) - Contact Alert Logic support at support@alertlogic.com to get your customer id
* Credentials to Alert Logic Cloud Insight (this call is made from Cloud Insight API endpoint)
* User API Key for Alert Logic Cloud Defender API - API key can be requested from [here](https://www.alertlogic.com/resources/alert-logic-activeintegration-apis/#api-key)
* Configured Role-Based Access Control (RBAC) role for Cloud Defender (https://docs.alertlogic.com/gsg/Azure-environ-in-Cloud-Defender.htm)

Installation
------------
```
git clone https://github.com/muram/al-azure-api-tool.git
```
```
cd al-azure-api-tool
```
```
pip install -r requirements.txt
```

Configuration
-------------
Provide values to all variables (credentials and account ID) inside each script. Required values are:

#### For rename_hosts.py
```
EMAIL_ADDRESS="<ENTER USERNAME OR ACCESS_KEY_ID HERE>"
PASSWORD="<ENTER PASSWORD OR SECRET_KEY HERE>"
API_KEY="<ENTER CLOUD DEFENDER API KEY HERE>:"
TARGET_CID = "<ENTER CUSTOMER ID HERE>"
```

#### For cleanup_hosts.py
```
API_KEY = 'ENTER API KEY HERE'
CUST_ID = 'ENTER CUSTOMER ID HERE'
```

Usage
-----
### From a Local Terminal
```
$ python rename_hosts.py
```
```
$ python cleanup_hosts.py
```

### Run as an Azure Function with Time Trigger
Azure Function Apps allows to run server-less application in your Azure environment without setting up Virtual Machines to run those apps. More information can be found here (https://docs.microsoft.com/en-us/azure/azure-functions/functions-overview)
