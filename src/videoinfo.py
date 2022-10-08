import os
import re
import csv
import time
import json
import uuid
import random
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar
from .util import  getResp
from .config import B_API, MAX_TRY
from .ProcessBar import ProgressBar


class Get_Video_List(object):
    def __init__(self, url_index: dict) -> None:
        self.url_index = url_index
        self.cookies = RequestsCookieJar()

    def get(self, channel: str, field: str, startdate: str, enddate: str) -> str:
        dirname = os.path.join(channel, field, "Video_Info")
        # dirname = "{}/{}/Video_Info".format(channel, field)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        os.chdir(dirname)
        self.get_field_tid()
        self.set_cookies(channel, field)
        flname = os.path.join(os.getcwd(), self.get_all_page_list(channel, field, startdate, enddate))
        os.chdir("..")
        return flname

    def get_field_tid(self) -> None:
        print("获取分类id...")
        progress = ProgressBar(len(self.url_index.keys()), fmt=ProgressBar.FULL)
        for channel in self.url_index.keys():
            time.sleep(1)
            keys = list(self.url_index[channel]["field"].keys())
            if keys:
                url = self.url_index[channel]["field"][keys[0]]["url"]
                soup = BeautifulSoup(getResp(url).content.decode(), features="lxml")

                script = soup.find("script", string=re.compile("window.__INITIAL_STATE__.*"))
                if script is None:
                    print("{}\t获取分类id失败".format(url))
                    with open("error.json", "w") as fl:
                        fl.write(soup.prettify())
                jsp = json.loads(re.search("{.*}(?=;)", script.string).group())
                for ele in jsp["config"]["sub"]:
                    # print(ele)
                    if "tid" in ele:
                        self.url_index[channel]["field"][ele["name"]]["tid"] = ele["tid"]
            progress.current += 1
            progress()
        progress.done()
    
    def set_cookies(
        self, 
        channel: str = None, 
        field: str = None
        ) -> None:
        if channel and field:
            url = self.url_index[channel]["field"][field]["url"]
            r = getResp(url)
            self.cookies = r.cookies
        self.cookies.set("b_lsid", "9FC1310310_18285BFD12F", domain=".bilibili.com")
        self.cookies.set("_uuid", "{}infoc".format(uuid.uuid1()), domain=".bilibili.com")

    def to_csv(self, dwriter: csv.DictWriter, data: list) -> None:
        for ele in data:
            dwriter.writerow(ele)
    
    def get_all_page_list(
        self, 
        channel: str, 
        field: str, 
        startdate: str, 
        enddate: str
        ) -> str:
        print("获取'{}->{}'所有视频信息...".format(channel, field))
        max_try = 0
        flname = ".".join(["_".join([channel, field, startdate, enddate]), "csv"])
        if os.path.exists(flname):
            return flname
        tid = self.url_index[channel]["field"][field]["tid"]
        url = B_API.format(tid, 1, startdate, enddate, str(random.random())[2:])
        while (max_try < MAX_TRY):
            try:
                r = getResp(url, self.cookies)
            except Exception as e:
                print("获取页数失败，已尝试{}次，{}后重新尝试...".format(max_try, max_try*3))
                max_try += 1
                time.sleep(max_try*3)
            else:
                break
        if MAX_TRY <= max_try :
            raise Exception("获取页数失败！")
        jsp = json.loads(re.search("{.*}(?=\))", r.content.decode()).group())
        pn = jsp["numPages"]
        data = jsp["result"]
        fl = open(flname, "w", newline="")
        dwriter = csv.DictWriter(fl, fieldnames=data[0].keys())
        dwriter.writeheader()
        self.to_csv(dwriter, data)
        progress = ProgressBar(pn, fmt=ProgressBar.FULL)
        for pagenum in range(2, progress.total+1):
            data = self.get_one_page_list(tid, pagenum, startdate, enddate)
            self.to_csv(dwriter, data)
            progress.current += 1
            progress()
            time.sleep(0.5)
        progress.done()
        
        return flname
        # print(jsp)
        
    def get_one_page_list(self, tid, pagenum, startdate, enddate) -> list:
        max_try = 0
        url = B_API.format(tid, pagenum, startdate, enddate, str(random.random())[2:])
        self.set_cookies()
        while (max_try < MAX_TRY):
            try:
                r = getResp(url, self.cookies)
            except Exception as e:
                max_try += 1
                print("获取{}页失败, 已尝试次数{}...".format(pagenum, max_try))
                time.sleep(max_try)
            else:
                jsp = json.loads(re.search("{.*}(?=\))", r.content.decode()).group())
                return jsp["result"]
        raise Exception("获取{}页失败！".format(pagenum))