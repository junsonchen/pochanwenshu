# -*- coding: utf-8 -*-
from scrapy.cmdline import execute
import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# execute("scrapy crawl instrument".split())  # 人民法院公告网破产文书
# execute("scrapy crawl instrument_update".split())  # 人民法院公告网破产文书
# execute("scrapy crawl national_pochan".split())  # 中华人民共和国最高人民法院破产文书
# execute("scrapy crawl national_pochan_update".split())  # 中华人民共和国最高人民法院破产文书
# execute("scrapy crawl real_court".split())  # 获取全国法院名称
execute("scrapy crawl court_albb".split())  # 获取全国法院名称

# execute("scrapy crawlall".split())
# execute("scrapy crawlall -a deltafetch_reset=1".split())#清空url跑全部任务