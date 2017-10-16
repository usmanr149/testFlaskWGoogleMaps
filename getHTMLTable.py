from flask import jsonify
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests, json, re, time

def getHospitalWaitTimes():
    url = "http://www12.albertahealthservices.ca/repacPublic/SnapShotController?direct=displayEdmonton"
    page = urlopen(url).read()
    soup = BeautifulSoup(page, "lxml")
    now_time = soup.find_all("div", class_="publicRepacDate")[0].findAll(text=True)[1].replace("\n", "").replace("\r",
                                                                                                                 "").replace(
        " ", "")
    hospital_wait_times = {}
    for hit in soup.find_all("tr"):
        if len(hit.find_all("td", class_="publicRepacSiteCell")) > 0:
            time = ''
            # print(hit.find("td", class_="publicRepacSiteCell").text)
            for img in hit.find_all("img", attrs={"alt": True}):
                # print(img.get("alt"))
                time += img.get("alt")
            hospital_wait_times[hit.find("td", class_="publicRepacSiteCell").text] = time

    return hospital_wait_times, now_time


#fix hospital name
def fixValue(key):
    s = [i.strip() for i in key.splitlines() if len(i.strip()) > 0]
    return s


def getHTML(data, updateTime):

    html = ["<table class='table table-responsive' "
                                                     "style='width: 478.4px; padding-left: 5px;'><thead><tr>"
            "<th style='width:  293px; text-align: center;'><span style='color: #ff0000;'>Hospital</span></th>"
            "<th style='width: 175.4px; text-align: center;'><span style='color: #ff0000;'><br />Wait Times<br />Updated at <p style='display:inline' id = 'update_time'>{0}</p></span></th>"
                "</tr></thead><tbody>".format(str(updateTime[:4]) + " " + str(updateTime[4:]))]
    for key, value in data.items():
        k = fixValue(key)
        html.append("<tr>")
        html.append("<td>")
        html.append("<div class ='radio'>")
        if len(k) > 1:
            html.append("<label> <input type = 'radio' id = 'location_hospital_{0}' name = 'optradio' value = {1},Edmonton>".format(
                k[0].split(" ")[0],  k[0].replace(" ", "+")))
            html.append("{0}</label>".format(k[0]))
            html.append('<div class="add_info"><span style="color: #ff0000;"><label>{0}</label></span></div>'.format(k[1]))
        else:
            html.append("<label> <input type = 'radio' id = 'location_hospital_{0}' name = 'optradio' value = {1},Edmonton>".format(
                k[0].split(" ")[0], k[0].replace(" ", "+")))
            html.append("{0}</label>".format(k[0]))
        html.append("</div>")
        html.append("</td><td><div class ='radiotext' style='text-align: center;'>")
        html.append("<label for='regular' id = '{1}_time'>{0}</label>".format(str(value[:2])+":"+str(value[2:]), k[0].split(" ")[0]))
        html.append("</div></td></tr>")

    html.append("</table>")

    return "\n".join(html)

def getMedicentreData(url= "https://www.medicentres.com/clinic-locations/"):
    payload = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
               "Accept-Encoding": "gzip, deflate, br",
               "Accept-Language": "en-GB,en-US;q=0.8,en;q=0.6",
               "Cache-Control": "max-age=0",
               "Connection": "keep-alive",
               "Content-Length": "103",
               "Content-Type": "application/x-www-form-urlencoded",
               "Cookie": "_ga=GA1.2.1572985675.1506014656; _gid=GA1.2.297042775.1507133010",
               "Host": "www.medicentres.com",
               "Origin": "https://www.medicentres.com",
               "Referer": "https://www.medicentres.com/clinic-locations/",
               "Upgrade-Insecure-Requests": "1",
               "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
               }
    data = {"navigator": "yes",
            "city": "Edmonton, Alberta",
            "clinic": "",
            "waittimes": "all",
            "distancewithin": "all",
            "waittimer-submit": "Submit"}
    r = requests.post(url=url, headers=payload, data=json.dumps(data))

    return BeautifulSoup(r.content, "lxml")


def find_word(text, search):
    result = re.findall('\\b' + search + '\\b', text, flags=re.IGNORECASE)
    if len(result) > 0:
        return True
    else:
        return False

def getMedicentreHTML(url= "https://www.medicentres.com/clinic-locations/"):

    soup = getMedicentreData()
    html = ["""<table style='padding-left: 5px;'>
        <tbody>
        <tr>
        <td style="text-align: center;"  width=60%;><span style="color: #ff0000;">
        <strong>Medicentre</strong></span></td>
        <td style="text-align: center;">
        <span style="color: #ff0000;" width=40%> <strong>Wait Time</strong>
        </span></td></tr><tr>"""]
    for elem in soup.select('div.col-sm-12.medicentre'):
        if "Edmonton," in elem.find(class_='address').get_text() \
                or 'Sherwood Park' in elem.find(class_='address').get_text() \
                or 'St. Albert' in elem.find(class_='address').get_text():
            name = elem.find('a').get_text()
            add = elem.find(class_='address').get_text()
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
            html.append("""<tr>
            <td>
            <div class="radio"><label> <input id="{0}"
            name="optradio" type="radio" value="{1}"  />{2}</label></div>
            </td>
            <td id="{0}_update_time">
            <div class="radiotext" style="text-align: center;">
            <label id="{0}_time" for="regular" data-wait_hr="{3}" 
            data-wait_min="{4}" >{3} hr {4} min</label></div>
            <div class="radiotext" style="text-align: center;">(last updated: {5})</div>
            </td>
            </tr>
            """.format(name.split(" ")[0], add.replace(" ", "+"), name, hr_min(waitTimes, 'hr'),
                       hr_min(waitTimes, 'mins'), lastUpdated))

    html.append("""</tbody></table>""")

    return "".join(html)

def getOtherClinicsHTML(url='http://www.walkinhealth.ca/directory/walk-in-clinic/ab/edmonton/'):
    with open('static/data/walkinClinics.json', 'r') as fp:
        data = json.load(fp)
    return data[time.strftime("%A")]

if __name__ == '__main__':
    print(getOtherClinicsHTML())