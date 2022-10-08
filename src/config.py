HEAD = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
B_API = "https://s.search.bilibili.com/cate/search?main_ver=v3&search_type=video&view_type=hot_rank&order=click&copy_right=-1&cate_id={}&page={}&pagesize=20&jsonp=jsonp&time_from={}&time_to={}&callback=jsonCallback_bili_{}"
PLAYER_API = "https://api.bilibili.com/x/player/v2?aid={}&cid={}"
SPI_URL = "https://api.bilibili.com/x/frontend/finger/spi"
COMM_API = "https://api.bilibili.com/x/v2/reply/main?mode=3&next={}&oid={}&plat=1&type=1"
REPLY_API = "https://api.bilibili.com/x/v2/reply/reply?oid={}&pn={}&ps=10&root={}&type=1"
UP_URL = "https://space.bilibili.com/{}"
FOLLOWER_API = "https://api.bilibili.com/x/relation/followers?vmid={}&pn={}&ps=20&order=desc&jsonp=jsonp&callback=__jp{}"
MAX_TRY = 5