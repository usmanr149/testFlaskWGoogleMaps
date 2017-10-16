from flask import Flask, render_template, flash, request,redirect, url_for, jsonify

from bs4 import BeautifulSoup
from urllib.request import urlopen

from getHTMLTable import getHospitalWaitTimes, getHTML, fixValue, getMedicentreHTML, getMedicentreData, find_word, getOtherClinicsHTML
import re

import configparser

config = configparser.ConfigParser()
config.read("./.properties")

api = config['SECTION_HEADER']['api']

app = Flask(__name__)

@app.route('/')
def index():
    hospital_wait_times, time = getHospitalWaitTimes()
    table = getHTML(hospital_wait_times, time)
    return render_template('mapView.html', table=table)

@app.route('/updateTimes')
def updateTimes(url="http://www12.albertahealthservices.ca/repacPublic/SnapShotController?direct=displayEdmonton"):
    hospital_wait_times, time = getHospitalWaitTimes()
    table = getHTML(hospital_wait_times, time)
    return jsonify(table=table)

@app.route('/updateHospitalWaitTimes')
def updateHospitalWaitTimes(url="http://www12.albertahealthservices.ca/repacPublic/SnapShotController?direct=displayEdmonton"):
    hospital_wait_times, now_time = getHospitalWaitTimes()
    keys = [k for k in hospital_wait_times.keys()]
    for k in keys:
        hospital_wait_times[k] = hospital_wait_times[k][:2] + ":" + hospital_wait_times[k][2:]
        hospital_wait_times[fixValue(k)[0].split(" ")[0] + "_time"] = hospital_wait_times.pop(k)
    hospital_wait_times['update_time'] = str(now_time[:4]) + " " + str(now_time[4:])
    return jsonify(result=hospital_wait_times)

@app.route('/updateMedicentreWaitTimes')
def updateMedicentreWaitTimes():
    soup = getMedicentreData()

    medicenter_wait_times = {}

    for elem in soup.select('div.col-sm-12.medicentre'):
        if "Edmonton," in elem.find(class_='address').get_text() \
                or 'Sherwood Park' in elem.find(class_='address').get_text() \
                or 'St. Albert' in elem.find(class_='address').get_text():
            name = elem.find('a').get_text()
            s1 = re.findall(r'\d+', elem.find(class_='waittime').get_text())

            waitTimes = {}
            for t in s1[:-2]:
                waitTimes[elem.find(class_='waittime').get_text().split(" ")[elem.find(class_=
                                                                                       'waittime').get_text().split(" ")
                                                                                 .index(t) + 1]] = t
            if len(s1) > 1:
                lastUpdated = str(s1[-2]) + ":" + str(s1[-1])
                if find_word(elem.find(class_='waittime').get_text(), 'am'):
                    lastUpdated += ' am'
                else:
                    lastUpdated += ' pm'

            else:
                lastUpdated = "Clinic Closed"

            hr_min = lambda y, x: y[x] if x in y.keys() else "00"
            medicenter_wait_times[name.split(" ")[0] + "_update_time"] = """<div class="radiotext" style="text-align: center;">
            <label id="{0}_time" for="regular" data-wait_hr="{1}" 
            data-wait_min="{2}" >{1} hr {2} min</label></div>
            <div class="radiotext" style="text-align: center;">(last updated: {3})</div>""".format(name.split(" ")[0],
                                                                                                   hr_min(waitTimes, 'hr'),
                                                                                                   hr_min(waitTimes, 'min'),
                                                                                                   lastUpdated).replace("\n", "")

    return jsonify(result=medicenter_wait_times)

@app.route('/medicentreWaitTimes')
def medicentreWaitTimes():
    medicentreWaitTimes_ = getMedicentreHTML()
    return jsonify(table=medicentreWaitTimes_)

@app.route('/otherClinics')
def otherClinics():
    return jsonify(table=getOtherClinicsHTML())

@app.route("/test")
def test():
    hospital_wait_times, time = getHospitalWaitTimes()
    table = getHTML(hospital_wait_times, time)
    return render_template("test.html", table=table, api=api)


if __name__ == '__main__':
   app.run(debug=True)