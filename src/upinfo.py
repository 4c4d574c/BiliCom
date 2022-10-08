import re
import json
import uuid
import time
from .util import getResp
from .config import *
from .ProcessBar import ProgressBar
from bs4 import  BeautifulSoup
from requests.cookies import RequestsCookieJar
from urllib.parse import quote


class Get_Up_Info(object):
    def __init__(self) -> None:
        self.cookies = RequestsCookieJar()

    def set_headers(self, mid):
        headers = HEAD
        headers["referer"] = "{}/{}/fans/fans".format(UP_URL, mid)

        return headers

    def get(self, mid):
        self.set_cookies()
        self.get_all_fans(mid)

    def set_cookies(self):
        uid = "{}".format(uuid.uuid1()).split("-")[0]
        time_ms = hex(int(round(time.time()*1000)))
        self.cookies.set("b_lsid", "{}_{}".format(uid.upper(), str(time_ms)[2:].upper()), domain=".bilibili.com")
        self.cookies.set("_uuid", "{}infoc".format(uuid.uuid1()), domain=".bilibili.com")
        self.cookies.set("buvid3", "{}infoc".format(uuid.uuid1()), domain=".bilibili.com")
        self.cookies.set("b_nut", "{}".format(int(time.time())), domain=".bilibili.com")
        self.cookies.set("buvid_fp", "{}".format(uuid.uuid1().hex), domain=".bilibili.com")
        r = getResp(SPI_URL, self.cookies)
        buvid4 = quote(r.json()["data"]["b_4"], "/+", "utf8")
        self.cookies.set("buvid4", "{}".format(buvid4), domain=".bilibili.com")
    
    def get_all_fans(self, mid):
        url = FOLLOWER_API.format(mid, 1, 1)
        headers = self.set_headers(mid)
        r = getResp(url, headers, self.cookies)
        jsp = json.loads(re.search("(?<=\(){.*}(?=\))", r.content.decode()).group())
        pagenum = jsp["data"]["total"] / 20
        for pgnum in range(2, pagenum+1):
            fans = self.get_one_page_fans(self, pgnum, mid, pgnum)
        # print(r.content.decode())
    
    def get_one_page_fans(self, pgnum, mid, seq):
        max_try = 0
        url = FOLLOWER_API.format(mid, pgnum, seq)
        headers = self.set_cookies(mid)
        while (max_try < MAX_TRY):
            try:
                r = getResp(url, headers, self.cookies)
            except Exception as e:
                max_try += 1
                print("获取第{}页粉丝失败，已尝试次数{}次，{}秒后重新尝试...".format(pgnum, max_try, max_try*3))
                time.sleep(max_try*3)
            else:
                jsp = json.loads(re.search("(?<=\(){.*}(?=\))", r.content.decode()).group())
                return jsp["data"]["list"]
        
        raise Exception("获取{}的第{}页粉丝失败！".format(mid, pgnum))


if __name__ == "__main__":
    upinfo = Get_Up_Info()
    upinfo.get("1338715561")