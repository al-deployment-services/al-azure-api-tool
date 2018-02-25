from __future__ import print_function

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'lib')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'env/Lib/site-packages')))
import json, requests, datetime

#Put your user API key and CID
API_KEY = 'ENTER API KEY HERE'
CUST_ID = 'ENTER CUSTOMER ID HERE'

TARGET_PROTECTED_HOST = []
TARGET_SOURCE = []
TARGET_HOST = []

#minimum delta since last update
MIN_DELTA = 7

#request API call static Params
#Change .com to .net if deployed in the Denver DC
HEADERS = {'content-type': 'application/json'}
ALERT_LOGIC_API_TM_URL = "https://publicapi.alertlogic.com/api/tm/v1/"
ALERT_LOGIC_API_LM_URL = "https://publicapi.alertlogic.com/api/lm/v1/"

def find_inactive_protectedhost():
	RESPONSE = list_inactive_protectedhost()
	HOST_DATA = RESPONSE["protectedhosts"]

	#find host id with status offline
	for item in HOST_DATA:
		if item["protectedhost"]["status"]["status"] == "offline":
			#get the delta days since last update
			LAST_UPDATE = datetime.datetime.utcfromtimestamp(item["protectedhost"]["status"]["updated"])
			DAYS_DELTA = datetime.datetime.utcnow() - LAST_UPDATE
			print ("Found host name " + str(item["protectedhost"]["name"]) + " id " + str(item["protectedhost"]["id"]) + " host id " + str(item["protectedhost"]["host_id"]) + " IP Address " + str(item["protectedhost"]["metadata"]["local_ipv4"]) + " Last update " + str(LAST_UPDATE) + " delta days : " + str(DAYS_DELTA.days))
			#add protected host to target to be deleted if it's has been offline for more than MIN_DELTA
			if DAYS_DELTA.days > MIN_DELTA:
				TARGET_PROTECTED_HOST.append(item["protectedhost"]["id"])
				TARGET_HOST.append(item["protectedhost"]["host_id"])

	return True

def find_inactive_source():
	RESPONSE = list_inactive_source()
	SOURCE_DATA = RESPONSE["sources"]

	#find source id based on host id
	for host_id in TARGET_HOST:
		for item in SOURCE_DATA:
			if item["syslog"]["agent"]["host_id"] == host_id:
				print ("Found source name " + str(item["syslog"]["name"]) + " id " + str(item["syslog"]["id"]) + " host id " + str(host_id))
				TARGET_SOURCE.append(item["syslog"]["id"])

	return True

def list_inactive_protectedhost():
	#find all protected host with deployment model agent and status is offline
	API_ENDPOINT = ALERT_LOGIC_API_TM_URL + CUST_ID + "/protectedhosts?config.collection_method=agent&metadata.host_type=ms_azure&status.status=offline&type=host&offset=0"
	REQUEST = requests.get(API_ENDPOINT, headers=HEADERS, auth=(API_KEY,''))
	RESULT = json.loads(REQUEST.text)
	return RESULT

def list_inactive_source():
	#find all the source in log manager with deployment model syslog / agent and status is offline
	API_ENDPOINT = ALERT_LOGIC_API_LM_URL + CUST_ID + "/sources?method=agent&metadata.host_type=ms_azure&status=offline&offset=0"
	REQUEST = requests.get(API_ENDPOINT, headers=HEADERS, auth=(API_KEY,''))
	RESULT = json.loads(REQUEST.text)
	return RESULT

def delete_inactive_protectedhost(target):
	RESULT = ""
	for items in target:
		API_ENDPOINT = ALERT_LOGIC_API_TM_URL + CUST_ID + "/protectedhosts/" + items
		REQUEST = requests.delete(API_ENDPOINT, headers=HEADERS, auth=(API_KEY,''))
		RESULT = RESULT + str(REQUEST.text) + " Protected Host ID : " + items + "\n"
	return RESULT

def delete_inactive_source(target):
	RESULT = ""
	for items in target:
		API_ENDPOINT = ALERT_LOGIC_API_LM_URL + CUST_ID + "/sources/" + items
		REQUEST = requests.delete(API_ENDPOINT, headers=HEADERS, auth=(API_KEY,''))
		RESULT = RESULT + str(REQUEST.status_code) + " Source ID : " + items + "\n"
	return RESULT

def delete_inactive_host(target):
	RESULT = ""
	for items in target:
		API_ENDPOINT = ALERT_LOGIC_API_TM_URL + CUST_ID + "/hosts/" + items
		REQUEST = requests.delete(API_ENDPOINT, headers=HEADERS, auth=(API_KEY,''))
		RESULT = RESULT + str(REQUEST.status_code) + " Host ID : " + items + "\n"
	return RESULT

if __name__ == '__main__':
	#call list of inactive protected host
	if (find_inactive_protectedhost()):
		find_inactive_source()

	print ("Target protected host: " + str(TARGET_PROTECTED_HOST))
	print ("Target source: " + str(TARGET_SOURCE))
	print ("Target host: " + str(TARGET_HOST))

	#delete the targeted protected host and source and then host
	if len(TARGET_HOST) >= 0:
		print ("\n" + "==== DELETE STATUS ====")
		RESULT = delete_inactive_source(TARGET_SOURCE)
		print ("Delete source : " + "\n" + str(RESULT))

		RESULT = delete_inactive_protectedhost(TARGET_PROTECTED_HOST)
		print ("Delete protected host : " + "\n" + str(RESULT))

		RESULT = delete_inactive_host(TARGET_HOST)
		print ("Delete host : " + "\n" + str(RESULT))
		print ("\n" + "==== END STATUS ====")
	else:
		print ("No candidate hosts that match the delete criteria")
