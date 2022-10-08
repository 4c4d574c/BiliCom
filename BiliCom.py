import csv
import json
from src.config import *
from src.util import dateRange, getResp
from src.getfield import get_channel_url, Get_Field
from src.videoinfo import Get_Video_List
from src.videocomm import Get_Video_Comm


if __name__ == "__main__":
    url = "https://www.bilibili.com"
    field_url = Get_Field(get_channel_url(url))
    field_url.get()
    video_list = Get_Video_List(field_url.url_index)
    csv_flname = video_list.get("游戏", "单机游戏", "20220820", "20220820")

    reader = csv.DictReader(open(csv_flname, newline=""))
    video_comm = Get_Video_Comm()
    for ele in reader:
        url = ele["arcurl"]
        bvid = ele["bvid"]
        comm = video_comm.get(url, bvid)
        if comm is not None:
            with open("{}_comm.json".format(bvid), "w") as fl:
                fl.write(json.dumps(comm, indent=4, ensure_ascii=False))
        else:
            print("{}无评论!".format(bvid))
    # print(video_comm.cookies.get_dict())