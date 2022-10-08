import os
import re
import json
import time
import uuid
import math
from requests.cookies import RequestsCookieJar
from urllib.parse import quote
from bs4 import BeautifulSoup
from .util import getResp
from .ProcessBar import ProgressBar
from .config import *


class Get_Video_Comm(object):
    def __init__(self) -> None:
        self.cookies = RequestsCookieJar()
        self.olddir = os.getcwd()

    def get(self, url: str, bvid: str) -> None:
        dirname = os.path.join(self.olddir, "Video_Comm")
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        os.chdir(dirname)
        print("获取'{}'的评论...".format(bvid))
        # flname = "{}_comm.json".format(bvid)
        oid, cid = self.get_ids(url)
        if not (oid and cid):
            return
        if not self.cookies.items():
            self.set_cookies(oid, cid)
        comm = self.get_comm(oid)
        return comm
    
    def get_ids(self, url: str) -> str:
        r = getResp(url)
        self.cookies.update(r.cookies)
        soup = BeautifulSoup(r.content.decode(), features="lxml")
        script = soup.find("script", string=re.compile("window.__INITIAL_STATE__.*"))
        if script is None:
            with open("error_soup.json", "w") as fl:
                fl.write(soup.prettify())
        jsp = json.loads(re.search("{.*}(?=;)", script.string).group())
        if "error" in jsp:
            error = jsp["error"]
            if "code" in error and error["code"] == 404:
                print("{}".format(jsp["error"]["message"]))
                return None, None
        videodata = jsp["videoData"]
        oid = videodata["aid"]
        cid = videodata["cid"]

        return oid, cid

    def set_cookies(self, aid, cid) -> None:
        self.cookies.set("CURRENT_FNVAL", "4048", domain=".bilibili.com")
        # spm_prefix = soup.find("meta", attrs={"name": "spm_prefix"}).get("content")
        player_api = PLAYER_API.format(aid, cid)
        r = getResp(player_api, self.cookies)
        self.cookies.update(r.cookies)
        uid = "{}".format(uuid.uuid1()).split("-")[0]
        time_ms = hex(int(round(time.time()*1000)))
        self.cookies.set("b_lsid", "{}_{}".format(uid.upper(), str(time_ms)[2:].upper()), domain=".bilibili.com")
        self.cookies.set("_uuid", "{}infoc".format(uuid.uuid1()), domain=".bilibili.com")
        r = getResp(SPI_URL, self.cookies)
        buvid4 = quote(r.json()["data"]["b_4"], "/+", "utf8")
        self.cookies.set("buvid4", "{}".format(buvid4), domain=".bilibili.com")
        self.cookies.set("buvid_fp", "{}".format(uuid.uuid1().hex), domain=".bilibili.com")
        # buvid3 = self.cookies["buvid3"].split("-")[0]
        time_ms = hex(int(round(time.time()*1000)))
        # b_timer = '{"ffp":{"{}.fp.risk_{}".format(spm_prefix.upper(), buvid3.upper()):"{}".format(str(time_ms)[2:].upper())}}'
        # self.cookies.set("b_timer", quote(b_timer, "utf8"), domain=".bilibili.com")
    
    def get_comm(self, oid: str) -> list:
        pagenum = 0
        is_end = False
        comm = list()

        # 获取评论
        main_comm = self.get_main_comm(pagenum, oid)
        if main_comm is None:
            return
        if "replies" in main_comm:
            if main_comm["replies"] is not None:
                comm.extend(main_comm["replies"])
            else:
                return
        if "top_replies" in main_comm and main_comm["top_replies"] is not None:
            comm.extend(main_comm["top_replies"])
        cursor = main_comm["cursor"]
        all_count = cursor["all_count"]
        is_end = cursor["is_end"]
        pagenum = cursor["next"]
        progress = ProgressBar(all_count, fmt=ProgressBar.FULL)
        progress.current += len(comm)
        progress()
        while (not is_end):
            main_comm = self.get_main_comm(pagenum, oid)
            if "replies" in main_comm and main_comm["replies"] is not None:
                progress.current += len(main_comm["replies"])
                comm.extend(main_comm["replies"])
            is_end = main_comm["cursor"]["is_end"]
            pagenum = main_comm["cursor"]["next"]
            progress()
            time.sleep(0.5)

        # 获取评论的回复
        for ele in comm:
            replies = ele["replies"]
            if replies:
                rcount = ele["rcount"]
                pagenum = math.ceil(rcount/10)
                root = ele["rpid"]
                comm_index = comm.index(ele)
                comm[comm_index]["replies"].clear()
                for pgnum in range(1, pagenum+1):
                    reply = self.get_reply_comm(oid, pgnum, root)
                    if "replies" in reply and reply["replies"] is not None:
                        progress.current += len(reply["replies"])
                        comm[comm_index]["replies"].extend(reply["replies"])
                    else:
                        print("第{}页回复为空！")
                    progress()
                    time.sleep(0.5)
        progress.done()
        
        # 去除所有不必要的字段
        comm_save_key = ["content", "member", "replies", "ctime", "like"]
        content_save_key = ["message", "members"]
        member_save_key = ["uname", "sign", "sex", "mid"]
        for i in range(len(comm)):
            for key in comm[i].keys()-comm_save_key:
                del comm[i][key]
            for key in comm[i]["content"].keys()-content_save_key:
                del comm[i]["content"][key]
            for key in comm[i]["member"].keys()-member_save_key:
                del comm[i]["member"][key]
            replies = comm[i]["replies"]
            if replies:
                for j in range(len(replies)):
                    for key in replies[j].keys()-comm_save_key:
                        del comm[i]["replies"][j][key]
                    for key in replies[j]["content"].keys()-content_save_key:
                        del comm[i]["replies"][j]["content"][key]
                    for key in replies[j]["member"].keys()-member_save_key:
                        del comm[i]["replies"][j]["member"][key]
                    content = replies[j]["content"]
                    if "members" in content and content["members"]:
                        for k in range(len(content["members"])):
                            for key in content["members"][k].keys()-member_save_key:
                                del comm[i]["replies"][j]["content"]["members"][k][key]

        return comm
        # with open(flname, "w") as fl:
        #     fl.write(json.dumps(comm, indent=4, ensure_ascii=False))

    def get_main_comm(self, pagenum: int, oid: str) -> list:
        max_try = 0
        main_url = COMM_API.format(pagenum, oid)
        while (max_try < MAX_TRY):
            try:
                r = getResp(main_url, self.cookies)
            except Exception as e:
                max_try += 1
                print("获取第{}页评论失败，已尝试次数{}次, {}秒后重新尝试...".format(pagenum, max_try, max_try*3))
                time.sleep(max_try*3)
            else:
                if r.json()["code"] != 0:
                    return
                # print(r.json())
                jsp = r.json()["data"]
                return jsp
        raise Exception("获取第{}页评论失败！".format(pagenum))
    
    def get_reply_comm(self, oid: str, pagenum: int, root: str) -> list:
        max_try = 0
        reply_url = REPLY_API.format(oid, pagenum, root)
        while (max_try < MAX_TRY):
            try:
                r = getResp(reply_url, self.cookies)
            except Exception as e:
                max_try += 1
                print("获取评论{}失败，已尝试次数{}次，{}秒后重新尝试...".format(root, max_try, max_try*3))
                time.sleep(max_try*3)
            else:
                jsp = r.json()["data"]
                if jsp is None:
                    with open("reply_comm.json", "w") as fl:
                        fl.write(json.dumps(r.json(), indent=4, ensure_ascii=False))
                    exit(-1)
                return jsp
        raise Exception("获取{}的第{}页失败！".format(root, pagenum))

if __name__ == "__main__":
    url = "http://www.bilibili.com/video/BV18t4y1J7Qg"
    comm = Get_Video_Comm()
    comm = comm.get(url, "BV18t4y1J7Qg")
    if comm:
        print(json.dumps(comm, indent=4, ensure_ascii=False))
    else:
        print(comm)