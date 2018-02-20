import sys, os, datetime, json
import httplib, urllib
import time
from base64 import b64encode

# Provide credentials for Alert Logic
EMAIL_ADDRESS="ENTER USERNAME OR ACCESS_KEY_ID HERE"
PASSWORD="ENTER PASSWORD OR SECRET_KEY HERE"
API_KEY="ENTER CLOUD DEFENDER API KEY HERE:"

CD_KEY = b64encode(bytes(API_KEY)).decode("ascii")
CD_HEADERS = {}
CD_HEADERS['Authorization'] = 'Basic ' + CD_KEY
CD_HEADERS['Accept'] = 'application/json'

CI_HEADERS = {}
CI_HEADERS['Accept'] = 'application/json'

# Provide account ID and API endpoints
TARGET_CID = "ENTER CUSTOMER ID HERE"
ALERT_LOGIC_API_CI = "api.cloudinsight.alertlogic.com"
ALERT_LOGIC_CI_ENV = "https://api.cloudinsight.alertlogic.com/environments/v1/"
ALERT_LOGIC_CI_SOURCES = "https://api.cloudinsight.alertlogic.com/sources/v1/"
ALERT_LOGIC_CI_ASSETS = "https://api.cloudinsight.alertlogic.com/assets/v1/"
# Change .net to .com if deployed in the Ashburn DC
ALERT_LOGIC_CID = "https://api.alertlogic.net/api/customer/v1/"
ALERT_LOGIC_API_TM_URL = "publicapi.alertlogic.net/api/tm/v1/"
ALERT_LOGIC_API_TM = "publicapi.alertlogic.net"

MASTER_ENV = []
PHOST_DIC = []
MASTER_DIC = {}
MASTER_DIC["PHOST"] = []

def authenticate(user, paswd,yarp):
    #Authenticate with CI yarp to get token
    url = yarp
    userAndPass = str(user) + ":" + str(paswd)
    userAndPass = b64encode(bytes(userAndPass)).decode("ascii")
    conn = httplib.HTTPSConnection(yarp)
    headers = { 'Authorization' : 'Basic %s' % userAndPass }
    conn.request('POST', '/aims/v1/authenticate', headers=headers)
    REQUEST = conn.getresponse()
    RESULT = json.loads(REQUEST.read())
    if REQUEST.status != 200:
        sys.exit("Unable to authenticate %s" % (REQUEST.status))
    account_id = RESULT['authentication']['user']['account_id']
    token = RESULT['authentication']['token']
    return token

def get_cd_phost_by_criteria(target_cid, host_status, asset_type, platform):
    API_ENDPOINT = "/api/tm/v1/" + target_cid + "/protectedhosts?type=" + asset_type + "&status.status=" + host_status + "&metadata.host_type=" + platform
    conn = httplib.HTTPSConnection(ALERT_LOGIC_API_TM)
    conn.request('GET',API_ENDPOINT, headers=CD_HEADERS)
    REQUEST = conn.getresponse()
    RESULT = json.loads(REQUEST.read())
    if REQUEST.status != 200:
        sys.exit("API Call failed with error code = %s" % (REQUEST.status))
    return RESULT

def get_ci_assets(target_cid, token, env_id, asset_type):
    API_ENDPOINT = "/assets/v1/" + target_cid + "/environments/" + env_id + "/assets?asset_types=" + asset_type
    CI_HEADERS['x-aims-auth-token'] = token
    conn = httplib.HTTPSConnection(ALERT_LOGIC_API_CI)
    conn.request('GET',API_ENDPOINT, headers=CI_HEADERS)
    REQUEST = conn.getresponse()
    RESULT = json.loads(REQUEST.read())
    return RESULT

def get_cloud_defender_env_by_cid(target_cid, token, platform):
    API_ENDPOINT = "/environments/v1/" + target_cid + "?type=" + platform + "&defender_support=true"
    CI_HEADERS['x-aims-auth-token'] = token
    conn = httplib.HTTPSConnection(ALERT_LOGIC_API_CI)
    conn.request('GET',API_ENDPOINT, headers=CI_HEADERS)
    REQUEST = conn.getresponse()
    RESULT = json.loads(REQUEST.read())
    return RESULT

def phost_update_name(target_cid, target_phost, new_name):
    payload_phost = {}
    payload_phost["protectedhost"] = {}
    payload_phost["protectedhost"]["name"] = new_name
    payload_phost = json.dumps(payload_phost)

    API_ENDPOINT = "/api/tm/v1/" + target_cid + "/protectedhosts/" + target_phost
    #print (target_phost)
    #print (new_name)
    print (payload_phost)
    conn = httplib.HTTPSConnection(ALERT_LOGIC_API_TM)
    conn.request('POST', API_ENDPOINT, body=payload_phost, headers=CD_HEADERS)

    REQUEST = conn.getresponse()
    if REQUEST.status != 200:
        sys.exit("API Call failed with error code = %s" % (REQUEST.status))
    else:
        print ("API Call status = %s" % (REQUEST.status))

if __name__ == '__main__':
    #Authenticate
    TOKEN = authenticate(EMAIL_ADDRESS, PASSWORD, ALERT_LOGIC_API_CI)

    #Grab all Azure Environment
    MASTER_ENV = get_cloud_defender_env_by_cid(TARGET_CID, TOKEN, "azure")
    print ("Found the following Deployments = " + str(MASTER_ENV["count"]))
    #print (json.dumps(MASTER_ENV, indent=2))

    print ("\nGather CI asset data for each Deployments \n")
    #Grab asset in each Azure Environment
    for ENV in MASTER_ENV["environments"]:
        #Get all asset with type host and state is running
        TEMP_ASSET = get_ci_assets(TARGET_CID, TOKEN, ENV["id"], "host")
        for ITEM in TEMP_ASSET["assets"]:
            MASTER_DIC["PHOST"].append(ITEM[0])

## OFFLINE HOST CHECK
    #Grab all PHOST by criteria
    PHOST_CRITERIA = "offline"
    PHOST_DIC = get_cd_phost_by_criteria(TARGET_CID, PHOST_CRITERIA, "host", "ms_azure")
    print ("Found the following offline PHOST = " + str(PHOST_DIC["total_count"]))

    #Check if PHOST exist in the asset
    print ("Find and match offline PHOST with CI Assets data \n" )
    for PHOST in PHOST_DIC["protectedhosts"]:
        print (PHOST["protectedhost"]["metadata"]["ec2_instance_id"])

        PHOST["protectedhost"]["rename"] = "AL_SKIP"

        #Assume we will delete it and recheck if we can find PHOST in Asset
        PHOST["protectedhost"]["marker"] = "DELETE"
        for ASSET in MASTER_DIC["PHOST"]:
            if PHOST["protectedhost"]["metadata"]["ec2_instance_id"] == ASSET["vm_id"]:
                print ("Match found : " + str(ASSET["key"]))
                print ("\n")
                PHOST["protectedhost"]["marker"] = "KEEP"
                PHOST["protectedhost"]["rename"] = ASSET["name"]
                break;

    print ("Here is what we found \n" )
    for PHOST in PHOST_DIC["protectedhosts"]:
        print (str(PHOST["protectedhost"]["metadata"]["ec2_instance_id"]) + "  " + (PHOST["protectedhost"]["marker"]))
        if PHOST["protectedhost"]["rename"] != "AL_SKIP":
            phost_update_name(TARGET_CID, PHOST["protectedhost"]["id"], PHOST["protectedhost"]["rename"])
        else:
            DELETE_MARKER = PHOST["protectedhost"]["metadata"]["local_hostname"] + " - DELETE"
            phost_update_name(TARGET_CID, PHOST["protectedhost"]["id"], DELETE_MARKER)

## 3. IF mark as DELETE, not in asset and older than 7 days, delete it
    DELETE_TIME_RANGE = 604800 #one week
    TODAY = time.time()

    PHOST_DELETE_DIC = []
    for PHOST in PHOST_DIC["protectedhosts"]:
        if PHOST["protectedhost"]["marker"] == "DELETE":
            if TODAY - PHOST["protectedhost"]["status"]["updated"] > DELETE_TIME_RANGE:
                PHOST_DELETE_DIC.append(PHOST)

    for PHOST in PHOST_DELETE_DIC:
        ARCHIVE_MARKER = PHOST["protectedhost"]["metadata"]["local_hostname"] + " - ARCHIVE"
        phost_update_name(TARGET_CID, PHOST["protectedhost"]["id"], ARCHIVE_MARKER)

## ONLINE HOST CHECK
    #Grab all PHOST by criteria
    PHOST_CRITERIA = "ok"
    PHOST_DIC = get_cd_phost_by_criteria(TARGET_CID, PHOST_CRITERIA, "host", "ms_azure")
    print ("Found the following OK PHOST = " + str(PHOST_DIC["total_count"]))

    #Check if PHOST exist in the asset
    print ("Find and match OK PHOST with CI Assets data \n" )
    for PHOST in PHOST_DIC["protectedhosts"]:
        print (PHOST["protectedhost"]["metadata"]["ec2_instance_id"])

        PHOST["protectedhost"]["rename"] = "AL_SKIP"
        for ASSET in MASTER_DIC["PHOST"]:
            if PHOST["protectedhost"]["metadata"]["ec2_instance_id"] == ASSET["vm_id"]:
                print ("Match found : " + str(ASSET["key"]))
                print ("\n")
                PHOST["protectedhost"]["rename"] = ASSET["name"]
                break;

    print ("Here is what we found \n" )
    for PHOST in PHOST_DIC["protectedhosts"]:
        print (str(PHOST["protectedhost"]["metadata"]["ec2_instance_id"]))
        if PHOST["protectedhost"]["rename"] != "AL_SKIP":
            phost_update_name(TARGET_CID, PHOST["protectedhost"]["id"], PHOST["protectedhost"]["rename"])
