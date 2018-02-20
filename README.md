al-azure-api-tool
=================
Python script for using the Alert Logic Cloud Insight API and Cloud Defender API to retrieve Azure assets

run.py
------
Python wrapper to import Azure Virtual Machine names from Cloud Insight assets into Threat Manager protected hosts and Log Manager sources. The script will extract VM names from discovered assets in the Azure subscription ID provided in Cloud Defender environment. In addition, the script will mark hosts that have been offline for X amount of days (7 days by default) as DELETE and perform an archive from the Alert Logic User Interface.

Requirements
------------
* Alert Logic Account ID (CID)
* Credentials to Alert Logic Cloud Insight (this call is made from Cloud Insight API endpoint)
* User API Key for Alert Logic Cloud Defender API - API key can be requested from [here](https://www.alertlogic.com/resources/alert-logic-activeintegration-apis/#api-key)
* Configured Role-Based Access Control (RBAC) role for Cloud Defender (https://docs.alertlogic.com/gsg/Azure-environ-in-Cloud-Defender.htm)
