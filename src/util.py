import calendar
import requests
from requests.cookies import RequestsCookieJar

from .config import HEAD

def dateRange(year: int, month: int):
    cal = calendar.Calendar()
    for date in cal.itermonthdates(year, month):
        if (date.month == month):
            yield date.strftime("%Y%m%d")

def getResp(url: str, headers=HEAD, cookies = RequestsCookieJar()) -> requests.Response:
    r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
    if r.status_code == 200:
        return r
    else:
        raise Exception("Response Failed!")

if __name__ == "__main__":
    for date in dateRange(2022, 8):
        print(date)