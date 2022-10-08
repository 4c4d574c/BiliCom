import re
import time
from .util import getResp
from .ProcessBar import ProgressBar
from bs4 import BeautifulSoup


def get_channel_url(url: str) -> dict:
    url_index = dict()
    soup = BeautifulSoup(getResp(url).content.decode(), features="lxml")

    spm_prefix = soup.find(attrs={'name': 'spm_prefix'}).get("content")
    if spm_prefix is None:
        with open("error.html", "w") as fl:
            fl.write(soup.prettify())
    tag_div = soup.find('div', attrs={'class': 'channel-items__left'})
    if tag_div is None:
        with open("error.html", "w") as fl:
            fl.write(soup.prettify())
    channel_link = tag_div.find_all('a', attrs={'class': 'channel-link'})
    if channel_link is None:
        with open("error.html", "w") as fl:
            fl.write(soup.prettify())
    for ele in channel_link:
        url_index["{}".format(ele.get_text().strip())] = {
            "channel": "".join(["https:", ele.get("href").strip(), "?spm_id_from={}.0.0".format(spm_prefix)]),
            "field": {}
        }

    return url_index


class Get_Field(object):
    def __init__(self, url_index: dict) -> None:
        self.url_index = url_index

    def get(self) -> None:
        print("获取全站分区分类链接索引...")
        progress = ProgressBar(len(self.url_index.keys()), fmt=ProgressBar.FULL)
        for channel in self.url_index.keys():
            time.sleep(1)
            url = self.url_index[channel]["channel"]
            # print("{}: {}".format(channel, url))
            m = re.search("(?<=/)\w+(?=/?\?)", url)
            if m is None:
                continue
            if m.group() in ["anime", "guochuang"]:
                self.get_field_type1(channel, url, "bangumi-home-crumb")
            elif m.group() in ["movie", "tv", "variety", "documentary", "mooc"]:
                continue
            else:
                self.get_field_type2(channel, url, "clearfix")
            progress.current += 1
            progress()
        progress.done()

    def get_field_type1(self, channel: str, url: str, div_id: str) -> None:
        soup = BeautifulSoup(getResp(url).content.decode(), features="lxml")

        tag_div = soup.find("div", attrs={'id': div_id})
        field_link = tag_div.find_all('a')
        for ele in field_link[1:]:
            self.url_index[channel]["field"]["{}".format(ele.get_text().strip())] = {"url": "".join(["https:", ele.get("href")])}
    
    def get_field_type2(self, channel: str, url: str, ul_class: str) -> None:
        soup = BeautifulSoup(getResp(url).content.decode(), features="lxml")

        tag_ul = soup.find('ul', attrs={'class': ul_class})
        tag_a = tag_ul.find_all('a')
        for ele in tag_a[1:]:
            self.url_index[channel]["field"]["{}".format(ele.get_text().strip())] = {"url": "".join(["https://www.bilibili.com", ele.get("href")])}
    