import sys
import json
import http.client
import os
import time
import shutil
"""
 This script does the following things:

 * Takes a json format as input.
 * Gets a new access token
 * Reads a list of ULBs from the ulbs.dat
 * ulbs.dat has to be created and kept in the same folder as the script
 * Updates the RoleActionCreate request in the json format with ULBs one at a time and with the access token
 * Calls newman with the updated json
 * Stores the output of newman in a timestamped file

 How to use the script:
  * create a file with the collection names like: "AccessControle copy copy.postman_collection.json"
  * The jsons must be in the same folder as the script
  * create a file with the list of ULBs
  * The ULB file must be in the same file as the script
  * Run the script like this:
    $ AccessControl_RoleAction.py jsonlist.dat ulbs.dat


"""


def file2list(file):

    #This function will convert a file which has tenantIds into a pythonic list

    listofitems = []
    fileofitems = open(file, 'r')
    for line in fileofitems.readlines():
        listofitems.append(line.rstrip())
    return(listofitems)


def updatejson(collectionsjson,tenantId,aToken):
    #This function will update the json with the access_token and tenantId

    jsonfile = open(collectionsjson,'r')
    data = json.load(jsonfile)
    for i in range(len(data['order'])):
        #we are looping through requests
        nameofreq = (data["requests"][i]["name"])
        rawModeData = (data["requests"][i]["rawModeData"])

        try:
            d = json.loads(rawModeData)
        except ValueError as err:
            print("the rawModeData in request number: {} is corrupt".format(i))
            print(err)
            continue
        d['RequestInfo']['authToken'] = aToken
        if nameofreq == 'RoleActionCreate':
            print("Updating {0} Req with tenantId: {1}".format(nameofreq,tenantId))
            d['tenantId'] = tenantId

        data["requests"][i]["rawModeData"] = str(d)
        #updating the buffer with the latest access_token and tenantId
        #print("Role: {}".format(d['role']['code']))
        #print("Action: {}".format(d['actions'][0]['name']))




    #using a tmp file to create the updated json
    #So that the original json will be untampered
    tmpfile = os.path.splitext(collectionsjson)[0] + tenantId + '.json'
    tmpjsonfile = open(tmpfile,'w')
    tmpjsonfile.write(json.dumps(data,sort_keys=True, indent=4, separators=(',', ': ')))
    #tmpjsonfile = open('tmp.json','w')
    #tmpjsonfile.write(json.dumps(data))
    tmpjsonfile.close()
    jsonfile.close()







def get_access_token():

    conn = http.client.HTTPConnection("egov-micro-dev.egovernments.org")
    payload = "username=narasappa&password=demo&grant_type=password&scope=read&tenantId=default"
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'authorization': "Basic ZWdvdi11c2VyLWNsaWVudDplZ292LXVzZXItc2VjcmV0",
        'cache-control': "no-cache",
        'postman-token': "d6c51f99-9f35-8390-6da3-c52ccc8bef34"
    }
    conn.request("POST", "/user/oauth/token?username=narasappa&password=demo&grant_type=password&scope=read&tenantId=default", payload, headers)

    res = conn.getresponse()
    data = res.read()
    parsed_json = json.loads(data)
    return(parsed_json['access_token'])




if __name__ == '__main__':

    listofjsons = file2list(sys.argv[1])
    print("This is the list of JSONS we are processing from {}".format(sys.argv[1]))
    print(listofjsons)
    print("This is the list of ULBs we are processing from {}".format(sys.argv[2]))
    ulblist = file2list(sys.argv[2])
    print(ulblist)


    aToken = get_access_token()
    #create a directory with timestamp
    timestr = time.strftime("%Y%m%d-%H%M%S")
    dirpath = os.path.join(os.getcwd(),timestr)
    os.mkdir(dirpath)
    os.chdir(dirpath)
    print("Creating a log dir: {} ".format(os.getcwd()))




    for collectionsjson in listofjsons:
        shutil.copy2(("../" + collectionsjson),dirpath)
        logfile = os.path.splitext(collectionsjson)[0] + '.log'
        #construct the newman command


        print("Running the Collection: {}".format(collectionsjson))
        for name in ulblist:

            hlogfile = open(logfile,'a')
            hlogfile.write("Sending request for ULB: {} \n".format(name))
            hlogfile.close()
            updatejson(collectionsjson,name,aToken)
            cmd = 'newman run ' + os.path.splitext(collectionsjson)[0] + name + '.json' + '>>' + logfile
            os.system(cmd)
