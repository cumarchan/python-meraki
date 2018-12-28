#!/usr/bin/env python3
'''
Author: Cumar Chandrasegaran
Script: ex20.py
Purpose: Read CSV file for store specific configurations, check if a store network already exists on the Meraki portal and deploy network accordingly.
Date: 28/11/2018
Version: 0.1

'''

from meraki import meraki
from tabulate import tabulate
from texttable import Texttable
from prettytable import PrettyTable
import requests
import sys
import csv
import json
#import numpy as np

##### GLOBAL VARIABLES #####

apikey = "<enter_api_key>"
orgid = "<enter_org_id>"
tz = "Europe/London"

    
##### READ CSV #####


def readcsv():
    with open('/home/cumar/scripts/python/v3_6/merakiMXVlanTest.csv') as csv_file:
        store_info = csv.reader(csv_file, delimiter=',')
        storeNumber = []
        storeName = []
        O2MX = []
        O2Vlan = []
        yogMX = []
        enrolVlan = []
        fosVlan = []
        aboVlan = []
        dptVlan = []

        for row in store_info:
            storenum = row[0]
            storename = row[1]
            o2mx = row[2]
            o2vlan = row[3]
            yogmx = row[4]
            wtr_enroll = row[5]
            wtr_fos = row[6]
            wtr_abo = row[7]
            wtr_dpt = row[8]                                                                            

            storeNumber.append(storenum)
            storeName.append(storename)
            O2MX.append(o2mx)
            O2Vlan.append(o2vlan)
            yogMX.append(yogmx)
            enrolVlan.append(wtr_enroll)
            fosVlan.append(wtr_fos)
            aboVlan.append(wtr_abo)
            dptVlan.append(wtr_dpt)

        whatStoreNum = input('\n\nEnter a valid 3-digit store number: ')
        storeNumIndex = storeNumber.index(whatStoreNum)
        theStoreName = storeName[storeNumIndex]
        theO2MX = O2MX[storeNumIndex]
        theO2Vlan = O2Vlan[storeNumIndex]
        theYogMX = yogMX[storeNumIndex]
        theEnrolVlan = enrolVlan[storeNumIndex]
        theFosVlan = fosVlan[storeNumIndex]
        theAboVlan = aboVlan[storeNumIndex]
        theDptVlan = dptVlan[storeNumIndex]

        print ('\n\n*** DESIRED ANCHORING/VLAN CONFIGURATION FOR THIS STORE ***')
        print ('\n\nStore Number:\t\t',whatStoreNum,'\nStore Name:\t\t',theStoreName,'\nO2 Anchor MX:\t\t',theO2MX,'\nO2 Wifi VLAN:\t\t',theO2Vlan,'\nYogaowt Anchor MX:\t',theYogMX,'\nEnrol VLAN:\t\t',theEnrolVlan, '\nFOS VLAN:\t\t',theFosVlan,'\nABO VLAN:\t\t',theAboVlan)
   
    check_meraki_network(whatStoreNum, theStoreName)
    network_option = input('\n\nSelect\n4 for MFD / QC4 deployment\n5 for MFD / QC5 deployment\nq to exit\nEnter:')
    if network_option == "4":
        create_network(whatStoreNum, theStoreName)
        thisNetworkID = find_wireless_network_id(whatStoreNum)
        thisO2MxID = find_mx_network_id(theO2MX)
        print("##########\nO2 MX id: ",thisO2MxID,"\n\n##########")
        thisYogMxID = find_mx_network_id(theYogMX)
        print("\n\n##########\nYogaowt MX id: ",thisYogMxID,"\n\n##########\n")
        update_ssid_o2wifi(thisNetworkID, thisO2MxID, theO2Vlan,0)
        update_ssid_yogaowt(thisNetworkID, thisYogMxID, 2110,1)
        update_ssid_jocgitm(thisNetworkID,2)
        update_ssid_habhakk(thisNetworkID,3)
        update_ssid_firewall_policy(thisNetworkID,0)
    elif network_option == "5":
        create_network(whatStoreNum, theStoreName)
        thisNetworkID = find_wireless_network_id(whatStoreNum)
        thisO2MxID = find_mx_network_id(theO2MX)
        print("##########\nO2 MX id: ",thisO2MxID,"\n\n##########")
        thisYogMxID = find_mx_network_id(theYogMX)
        print("\n\n##########\nYogaowt MX id: ",thisYogMxID,"\n\n##########\n")
        update_ssid_o2wifi(thisNetworkID, thisO2MxID, theO2Vlan,0)
        update_ssid_yogaowt(thisNetworkID, thisYogMxID, 2110,1)
        update_ssid_jocgitm(thisNetworkID,2)
        update_ssid_habhakk(thisNetworkID,3)
        update_ssid_firewall_policy(thisNetworkID,0)
    elif network_option == "q":
         exit()
    else:
         readcsv()
    


##### VIEW MERAKI #####


def check_meraki_network(whatStoreNum, theStoreName):
## Login to Meraki API using personalized API key and retrieve ORG information and check that a network doesn't already exist for the entered store ID
    #apikey = "52ec3626df03676d5a2f4c3e4034b56dc6bab3ca"
    #apikey = input('Enter your API Key: ')
    #apikey = str(apikey)
    myOrgs = meraki.myorgaccess(apikey)
    print (myOrgs)
    #orgid = input("\n\nEnter ORG ID you are working on: ")
    #orgid = 789251
    #orgid = int(orgid)
    myNetworks = meraki.getnetworklist(apikey, orgid)
## Login to Meraki API, retrieve a list of dictionaries of existing networks and store this as myNetworks, convert this into a CSV file called meraki_nets.csv
    f_nets = open('/home/cumar/scripts/python/v3_6/meraki_nets.csv', "w")
    writer = csv.DictWriter(
        f_nets, fieldnames=["id","organizationId","name","timeZone","tags","type","configTemplateId","disableMyMerakiCom","disableRemoteStatusPage"])
    writer.writeheader()                                                                                                         
    writer.writerows(myNetworks)
    f_nets.close()
## Compare the entered store number with existing network names to identify if it's an existing store. If exists cannot deploy. If not then proceed to deploy.
    whatStoreNum_s = str(whatStoreNum)
    print ("\n\nChecking if this network already exists on Meraki portal.....\n\n")
    with open('/home/cumar/scripts/python/v3_6/meraki_nets.csv') as csv_file2:
        existing_nets = csv.reader(csv_file2, delimiter=',')
        existingID = []
        existingStoreName = []        
        for row in existing_nets:
            id = row[0]
            name = row[2]
            if whatStoreNum_s == name[:3]:
                print ("Network ",id," for store ",whatStoreNum," already exists.\n\nCANNOT DEPLOY\n\nAbandoning script\n\n")
                exit()
    print ("\n\nOkay to proceed deploying network for store id", whatStoreNum,"-",theStoreName,"\n\n")
    #deploy_meraki(whatStoreNum, theStoreName)
   

      
##### CREATE NEW NETWORK #####
        
def create_network(whatStoreNum, theStoreName):
    #print ('\n\n',whatStoreNum,'-',theStoreName,' will be deployed as a QC4/MFD Site\n')
    name = str(whatStoreNum + " - " + theStoreName)
    type = "wireless switch appliance"
    tags = "Wtr_Branch API_Test Python_Test"
    #Use "QC5 - Master Template - DO NOT DELETE" as the base network to copy from when creating other networks
    copyFromNetworkId = "L_681169443639798259"
    url_update_ssid = "https://n210.meraki.com/api/v0/organizations/%s/networks" % (orgid)
    print ("\n\n",name,"\n\n")    
    headers = {'X-Cisco-Meraki-API-Key': apikey}
    payload = {'name':name, "timeZone": tz, 'type':type, 'tags':tags, 'copyFromNetworkId':copyFromNetworkId, 'disableMyMerakiCom':'false'}
    create_network = requests.post(url_update_ssid, data=payload, headers=headers)    
    print ("\n\nNetwork just created is\n\n",create_network)    
    #go find the network id for the just created network using the find_wireless_network_id function
    thisNetworkID = find_wireless_network_id(whatStoreNum)
    print ('\n\nNetwork ID for store',whatStoreNum,'-',theStoreName,'is: ',thisNetworkID)
    

 
##### FIND NETWORK ID #####

def find_wireless_network_id(whatStoreNum):    
    myNetworks = meraki.getnetworklist(apikey, orgid)
## Login to Meraki API, retrieve a list of dictionaries of existing networks and store this as myNetworks, convert this into a CSV file called meraki_nets.csv
    f_nets = open('/home/cumar/scripts/python/v3_6/meraki_nets.csv', "w")
    writer = csv.DictWriter(
        f_nets, fieldnames=["id","organizationId","name","timeZone","tags","type","configTemplateId","disableMyMerakiCom","disableRemoteStatusPage"])
    writer.writeheader()                                                                                                         
    writer.writerows(myNetworks)
    f_nets.close()
    whatStoreNum_s = str(whatStoreNum)
    with open('/home/cumar/scripts/python/v3_6/meraki_nets.csv') as csv_file3:
        existing_nets = csv.reader(csv_file3, delimiter=',') 
        for row in existing_nets:
            id = row[0]
            name = row[2]
            if whatStoreNum_s == name[:3]:
                #print ("\nStore ID is: ",id)
                return id


##### Find MX Network ID #####

def find_mx_network_id(mxName):
    myNetworks = meraki.getnetworklist(apikey, orgid)
    ## Login to Meraki API, retrieve a list of dictionaries of existing networks and store this as myNetworks, convert this into a CSV file called meraki_nets.csv
    f_nets = open('/home/cumar/scripts/python/v3_6/meraki_nets.csv', "w")
    writer = csv.DictWriter(
        f_nets, fieldnames=["id","organizationId","name","timeZone","tags","type","configTemplateId","disableMyMerakiCom","disableRemoteStatusPage"])
    writer.writeheader()                                                                                                         
    writer.writerows(myNetworks)
    f_nets.close()
    mxName_s = str(mxName)
    with open('/home/cumar/scripts/python/v3_6/meraki_nets.csv') as csv_file4:
        existing_nets = csv.reader(csv_file4, delimiter=',')      
        for row in existing_nets:
            id = row[0]
            name = row[2]
            if mxName_s == name:
                #print ("\nMX ID is: ",id)
                return id
    
    

##### Create O2 Wifi #####

def update_ssid_o2wifi(thisNetworkID, theO2MX, theO2Vlan, ssid_number):
    print("\n\nStart Creating O2 Wifi SSID with: ",thisNetworkID, theO2MX, theO2Vlan, ssid_number)
    url_update_ssid = "https://n210.meraki.com/api/v0/networks/%s/ssids/%s" % (thisNetworkID,ssid_number)
    print ("\nUpdate URL is: ",url_update_ssid)
    headers = {'X-Cisco-Meraki-API-Key': apikey, 'Content-Type': 'application/json'}
    #payload = {'name':'O2 Wifi', 'enabled':true, 'splashPage':'None','ssidAdminAccessible':'false','authMode':'open','ipAssignmentMode':'VPN','concentratorNetworkId':theO2MX,'vlanId':theO2Vlan,'minBitrate':12,'bandSelection':'2.4 GHz band only','perClientBandwidthLimitUp':400,'perClientBandwidthLimitDown':3000}
    payload = {
        'name': 'O2 Wifi',
        'enabled': 'true',
        'splashPage': 'None',
        'ssidAdminAccessible': 'false',
        'authMode': 'open',
        'ipAssignmentMode': 'VPN',
        'concentratorNetworkId': theO2MX,
        'vlanId': theO2Vlan,
        'minBitrate': 12,
        'bandSelection': '2.4 GHz band only',
        'perClientBandwidthLimitUp': 400,
        'perClientBandwidthLimitDown': 3000
    }
    result = requests.put(url_update_ssid, json=payload, headers=headers)
    print("\nFinished Creating O2 Wifi SSID\n\n",result,"\n\n##########")    
    
##### Create Yogaowt #####

def update_ssid_yogaowt(thisNetworkID, theYogMX, theYogVlan, ssid_number):
    print("\n\nStart Creating yogaowt SSID with: ",thisNetworkID, theYogMX, theYogVlan, ssid_number)
    url_update_ssid = "https://n210.meraki.com/api/v0/networks/%s/ssids/%s" % (thisNetworkID,ssid_number)
    print ("\nUpdate URL is: ",url_update_ssid)
    headers = {'X-Cisco-Meraki-API-Key': apikey, 'Content-Type': 'application/json'}
    payload = {
        'name': 'yogaowt',
        'enabled': 'true',
        'authMode': '8021x-radius',
        'encryptionMode': 'wpa-eap',
        'wpaEncryptionMode': 'WPA2 only',
        'splashPage': 'None',
        'radiusServers': [
            {
                'host': '10.12.114.11',
                'port': 1812,
                'secret': 'enterprise'
            },
            {
                'host': '10.14.114.11',
                'port': 1812,
                'secret': 'enterprise'
            }
        ],    
        'radiusAttributeForGroupPolicies': 'Airespace-ACL-Name',
        'ipAssignmentMode': 'VPN',
        'concentratorNetworkId': theYogMX,
        'vlanId': theYogVlan,
        'radiusOverride': 'true',
        'minBitrate': 12,
        'bandSelection': '5 GHz band only',
        'perClientBandwidthLimitUp': 0,
        'perClientBandwidthLimitDown': 0
    }
    result = requests.put(url_update_ssid, json=payload, headers=headers)
    print("\nFinished Creating yogaowt SSID\n\n",result,"\n\n##########")    

##### Create jocgitm #####

def update_ssid_jocgitm(thisNetworkID, ssid_number):
    print("\n\nStart Creating jocgitm SSID with: ",thisNetworkID, ssid_number)
    url_update_ssid = "https://n210.meraki.com/api/v0/networks/%s/ssids/%s" % (thisNetworkID,ssid_number)
    print("\nSSID update URL is: ",url_update_ssid)
    headers = {'X-Cisco-Meraki-API-Key': apikey, 'Content-Type': 'application/json'}
    payload = {
        'name': 'jocgitm',
        'enabled': 'true',
        'splashPage': 'None',
        'authMode': '8021x-radius',
        'encryptionMode': 'wpa-eap',
        'wpaEncryptionMode': 'WPA2 only',
        'radiusServers': [{'host': '10.12.114.11','port': 1812,'secret': 'enterprise'},{'host': '10.14.114.11','port': 1812,'secret': 'enterprise'}],
        'radiusAttributeForGroupPolicies': 'Reply-Message',
        'ipAssignmentMode': 'Bridge mode',
        'useVlanTagging': 'true',
        'defaultVlanId': 999,
        'apTagsAndVlanIds': [
            {
                'tags': 'jocgitm_vlan13',
                'vlanId': 13
            },
            {
                'tags': 'jocgitm_vlan21',
                'vlanId': 21
            },
            {
                'tags': 'jocgitm_vlan22',
                'vlanId': 22
            },
            {
                'tags': 'jocgitm_vlan24',
                'vlanId': 24
            },
            {
                'tags': 'jocgitm_vlan25',
                'vlanId': 25
            },
            {
                'tags': 'jocgitm_vlan26',
                'vlanId': 26
            },
            {
                'tags': 'jocgitm_vlan28',
                'vlanId': 28
            }
        ],    
        'radiusOverride': 'true',
        'minBitrate': 12,
        'bandSelection': '5 GHz band only',
        'perClientBandwidthLimitUp': 0,
        'perClientBandwidthLimitDown': 0
    }
    result = requests.put(url_update_ssid, json=payload, headers=headers)
    print("\n\nFinish Creating jocgitm SSID\n\n",result,"\n\n##########")

##### Create habhakk #####

def update_ssid_habhakk(thisNetworkID, ssid_number):
    print("\n\nStart Creating habhakk SSID with: ",thisNetworkID, ssid_number)
    url_update_ssid = "https://n210.meraki.com/api/v0/networks/%s/ssids/%s" % (thisNetworkID,ssid_number)
    print("\nSSID update URL is: ",url_update_ssid)
    headers = {'X-Cisco-Meraki-API-Key': apikey, 'Content-Type': 'application/json'}
    payload = {
        'name': 'habhakk',
        'enabled': 'true',
        'splashPage': 'None',
        'authMode': '8021x-radius',
        'encryptionMode': 'wpa-eap',
        'wpaEncryptionMode': 'WPA2 only',
        'radiusServers': [{'host': '10.12.114.11','port': 1812,'secret': 'enterprise'},{'host': '10.14.114.11','port': 1812,'secret': 'enterprise'}],    
        'radiusAttributeForGroupPolicies': 'Reply-Message',
        'ipAssignmentMode': 'Bridge mode',
        'useVlanTagging': 'true',
        'defaultVlanId': 999,
        'apTagsAndVlanIds': [{'tags': 'habhakk_vlan26','vlanId': 26},{'tags': 'habhakk_vlan27','vlanId': 27}],    
        'radiusOverride': 'true',
        'minBitrate': 12,
        'bandSelection': '5 GHz band only',
        'perClientBandwidthLimitUp': 0,
        'perClientBandwidthLimitDown': 0
    }
    result = requests.put(url_update_ssid, json=payload, headers=headers)
    print("\nFinish Creating habhakk SSID\n\n",result,"\n\n##########")
    
##### Update MR Firewall Policy #####

def update_ssid_firewall_policy(thisNetworkID, ssid_number):
    print ("\n\nStart updating O2 Wifi Firewall Policy\n")
    url_update_l3firewallrules = "https://n210.meraki.com/api/v0/networks/%s/ssids/%s/l3FirewallRules" % (thisNetworkID,ssid_number)
    print("\nSSID update URL is: ",url_update_l3firewallrules)
    headers = {'X-Cisco-Meraki-API-Key': apikey, 'Content-Type': 'application/json'}
    payload = {
        'rules':[
            {
                'comment': 'O2 Wifi Client Range 1',
                'policy': 'allow',
                'protocol': 'any',
                'destPort': 'any',
                'destCidr': '10.26.0.0/16'
            },
            {
                'comment': 'O2 Wifi Client Range 2',
                'policy': 'allow',
                'protocol': 'any',
                'destPort': 'any',
                'destCidr': '10.119.0.0/16'
            },
            {
                'comment': 'O2 Wifi DNS + Captive Portal',
                'policy': 'allow',
                'protocol': 'any',
                'destPort': 'any',
                'destCidr': '10.65.0.0/24'
            },
            {
                'comment': 'Meraki MX Farm - WK',
                'policy': 'allow',
                'protocol': 'any',
                'destPort': 'any',
                'destCidr': '172.17.63.64/28'
            },
            {
                'comment': 'Meraki MX Farm - DC',
                'policy': 'allow',
                'protocol': 'any',
                'destPort': 'any',
                'destCidr': '172.22.63.64/28'
            },
            {
                'comment': 'RFC1918_172.16.0.0/12',
                'policy': 'deny',
                'protocol': 'any',
                'destPort': 'any',
                'destCidr': '172.16.0.0/12'
            },
            {
                'comment': 'RFC1918_192.168.0.0/16',
                'policy': 'deny',
                'protocol': 'any',
                'destPort': 'any',
                'destCidr': '192.168.0.0/16'
            },
            {
                'comment': 'RFC1918_10.0.0.0/8',
                'policy': 'deny',
                'protocol': 'any',
                'destPort': 'any',
                'destCidr': '10.0.0.0/8'
            }
        ]
    }
    result = requests.put(url_update_l3firewallrules, json=payload, headers=headers)
    print("\nFinish Creating firewall policy for O2 Wifi SSID\n\n",result,"\n\n##########")

##### MAIN #####

def main():        
    print ('\n\n Hey there Network person! How are you doing today?\n\n Wanna deploy Meraki Wireless? You are at the right place!\n\n')
    readcsv()

if __name__ == '__main__':
    main()
    
