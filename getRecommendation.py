import geocoder
import pandas as pd

import requests
import urllib

from datetime import datetime

from bs4 import BeautifulSoup

def readAdresses():
    df = pd.read_csv("static/data/addresses.csv")

    return df.set_index('address').T.to_dict('list')

#based on the given address find the nearest clinic with the smallest wait time
def getTravellingTime(address, mode='TRANSIT'):
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    g = geocoder.google(address)
    if isinstance(g.latlng, list) and len(g.latlng) > 1:
        print(address)
        medicentre_response = requests.get("http://127.0.0.1:7000/updateMedicentreWaitTimes").json()
        hospital_response = requests.get("http://127.0.0.1:7000/updateHospitalWaitTimes").json()
        bestTIme = None
        recomendation=None
        typeofrecommendation = None
        time_ = datetime.now()
        for k, v in readAdresses().items():
            url = """http://0.0.0.0:8080/otp/routers/default/plan?fromPlace={0}&toPlace={1}&time={2}&date={3}&mode={4},WALK&maxWalkDistance=804.672&arriveBy=false&wheelchair=false&locale=en""".format(urllib.parse.quote(str(g.latlng[0]) + "," + str(g.latlng[1])),
                                                                                                                                                                                                                        urllib.parse.quote(str(v[0]) + "," + str(v[1])),
                                                                                                                                                                                                                        urllib.parse.quote(time_.strftime("%I:%M%p")),
                                                                                                                                                                                                                        urllib.parse.quote(time_.strftime("%m-%d-%Y")),
                                                                mode)
            print(url)
            print(k)
            try:
                response = requests.get(url).json()
                arrTime = float(response["plan"]["itineraries"][0]["endTime"])
                if "Hospital" in k:
                    arrTime += getHospitalWaitTimes(k, hospital_response)
                    print('hospital = ', k)
                    print("waitTime = ", getHospitalWaitTimes(k, hospital_response))
                    print(arrTime)
                    print("Estimated time to being seen: ", datetime.fromtimestamp(arrTime/1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
                    if bestTIme == None or arrTime < bestTIme:
                        bestTIme = arrTime
                        recomendation = k
                        typeofrecommendation = 'hospitals'
                elif "Medicentre" in k:
                    arrTime += getMedicentreWaitTime(k, medicentre_response)
                    print("medicentre = ", k)
                    print("waitTime = ", getHospitalWaitTimes(k, medicentre_response))
                    print("Estimated time to being seen: ", datetime.fromtimestamp(arrTime / 1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
                    if bestTIme == None or arrTime < bestTIme:
                        bestTIme = arrTime
                        recomendation = k
                        typeofrecommendation = 'medicentres'
                else:
                    arrTime += getMedicentreWaitTime(k, medicentre_response) + 1000000
                    print('other = ', k)
                    print(arrTime)
                    print("Estimated time to being seen: ", datetime.fromtimestamp(arrTime / 1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
                    if bestTIme == None or arrTime < bestTIme:
                        bestTIme = arrTime
                        recomendation = k
                        typeofrecommendation = 'other'
            except KeyError:
                print("PATH_NOT_FOUND")

        return bestTIme,recomendation, typeofrecommendation
    return 0,0,0

#get wait time in milliseconds to add to the unix timestamp
def getMedicentreWaitTime(loc, medicentre_response):
    key = loc.split(" ")[0]
    r = BeautifulSoup(medicentre_response['result']['{0}_update_time'.format(key)], "lxml")
    wait_hour = float(r.find(id="{0}_time".format(key)).get("data-wait_hr"))
    wait_min = float(r.find(id="{0}_time".format(key)).get("data-wait_min"))
    return wait_hour*3600*1000+wait_min*60*1000


#get wait time in milliseconds to add to the unix timestamp
def getHospitalWaitTimes(loc, hospital_response):
    key = loc.split(" ")[0]
    wait_hour = float(hospital_response['result']["{0}_time".format(key)].split(":")[0])
    wait_min = float(hospital_response['result']["{0}_time".format(key)].split(":")[1])
    return wait_hour*3600*1000+wait_min*60*1000

if __name__ == '__main__':
    #print(readAdresses())
    #time_ = datetime.now()
    #print(time_.strftime('%Y-%m-%d %H:%M:%S'))
    #print(datetime.now().strftime('%I:%M %p'))
    bestTime, where = getTravellingTime("9803 - 105 St NW, Edmonton, Alberta")
    print(bestTime)
    print(datetime.fromtimestamp(bestTime / 1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
    #print(where)
    #getHospitalWaitTimes("University of Alberta Hospital")
