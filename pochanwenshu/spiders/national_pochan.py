# -*- coding: utf-8 -*-
import scrapy
from urllib.parse import urljoin
from copy import deepcopy
import logging
import re
from functools import reduce
from pochanwenshu.work_utils.handle_data import get_jcrq_date,deal_chinese_data
logger = logging.getLogger(__name__)


class NationalPochanSpider(scrapy.Spider):
    name = 'national_pochan'
    allowed_domains = ['pccz.court.gov.cn']
    start_urls = ['https://pccz.court.gov.cn/pcajxxw/gkaj/gkaj']
    base_url = 'https://pccz.court.gov.cn/pcajxxw/gkaj/gkajlb'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'pochanwenshu.middlewares.RandomUserAgentMiddlerware': 25,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,  # 禁用默认的代理
            'pochanwenshu.middlewares.RandomCompanyProxyMiddlerware': 15,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'pochanwenshu.middlewares.MyRtryMiddlerware': 95,
        },
        "ITEM_PIPELINES": {
            'pochanwenshu.pipelines.PochanwenshuPipeline': 150,
            'pochanwenshu.pipelines.MongoPipeline': 180,
            # 'pochanwenshu.pipelines.Save2eEsPipeline': 180,
            # 'pochanwenshu.pipelines.RedisPipeline': 180,
            # 'scrapy_redis.pipelines.RedisPipeline':180,
        },
        "SCHEDULER": "scrapy_redis.scheduler.Scheduler",
        "DUPEFILTER_CLASS": "scrapy_redis.dupefilter.RFPDupeFilter",
        "SCHEDULER_QUEUE_CLASS": "scrapy_redis.queue.SpiderPriorityQueue",
        "SCHEDULER_PERSIST": True,

        "REDIRECT_ENABLED": False,
        'COOKIES_ENABLED': False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": '9',
        "DOWNLOAD_TIMEOUT": '30',
        # "CONCURRENT_REQUESTS": '16',  # 并发请求(concurrent requests)的最大值，默认16
        "CONCURRENT_ITEMS": '80',  # 同时处理(每个response的)item的最大值，默认100
        # "CONCURRENT_REQUESTS_PER_DOMAIN": '5',  # 对单个网站进行并发请求的最大值，默认8
        "DOWNLOAD_DELAY": '0.1',
    }

    def parse(self, response):
        # todo 获取总页数并且翻页
        pagecounts = re.search(r'pageinit\((\d+)\,', response.text).group(1)
        # 翻页为了更新，不用过滤
        for page in range(1, int(pagecounts) + 2):
            form_data = {
                    "start":"",
                    "end":"",
                    "cbt":"",
                    "lx": "999",
                    "pageNum": str(page),
                }
            if page <= 100:
                yield scrapy.FormRequest(
                    url=self.base_url,
                    formdata=form_data,
                    callback=self.parse_list_page,
                    dont_filter=True,
                    priority=1,
                )
            else:
                yield scrapy.FormRequest(
                    url=self.base_url,
                    formdata=form_data,
                    callback=self.parse_list_page,
                    priority=1,
                )

    def parse_list_page(self, response):
        item = {}
        selector = scrapy.Selector(text=response.text)
        base_data = selector.xpath('//div[@class="caseList"]/ul/li')
        item['xxly'] = "中华人民共和国最高人民法院-破产案件"
        item['site_id'] = 22313
        item['sj_type'] = '65'
        item['sj_ztxx'] = 1
        for data in base_data:
            links = data.xpath('./div/h4/a/@href').get()
            item['cf_cflb'] = data.xpath('.//span[@class="ajlx"]//text()').get('')
            url = urljoin("http://pccz.court.gov.cn/pcajxxw/", links)
            yield scrapy.Request(
                url=url,
                callback=self.parse_index_page,
                meta={'item': item},
                priority=2,
            )

    def parse_index_page(self, response):
        item = response.meta.get('item')
        re_com = re.compile(r'\r|\n|\t|\s')
        selector = scrapy.Selector(text=response.text)
        # 详情页最上面解析
        item['xq_url'] = response.url
        item['img_url'] = re.search(r'id=(.*?)&', response.url).group(1)
        item['cf_wsh'] = selector.xpath('//h3//text()').get()
        base_data = selector.xpath('//table[@class="tab-ajxx detail_table"]')
        for data in base_data:
            item['cf_xzjg'] = data.xpath('./tr[1]/td[1]//text()').re_first(r'：(.+)')  # 法院
            item['fb_rq'] = data.xpath('./tr[1]/td[2]//text()').re_first(r'：(.+)')  # 公开时间
            oname_data = data.xpath('./tr[2]/td[1]/span/@title').re_first(r':(.+)')  # 被申请人
            if oname_data:
                if ', ' in oname_data:
                    oname_list = oname_data.split(', ')
                    for onames in oname_list:
                        item['oname'] = onames
                else:
                    item['oname'] = oname_data
            else:
                item['oname'] = ''
            item['zckt_sqr'] = data.xpath('./tr[2]/td[2]/span/@title').re_first(r':(.+)', '')  # 申请人
            item['zxfy'] = data.xpath('./tr[3]/td[1]//text()').re_first(r'：(.+)', '')  # 管理人机构
            item['cw_fzrxx'] = data.xpath('./tr[3]/td[2]//text()').re_first(r'：(.+)', '')  # 管理人机构负责人
        # 债务人信息解析，大部分都没有
        bz_list = selector.xpath('//table[@class="detail_table"]//tr/td//text()').getall()
        if bz_list:
            item['bz'] = reduce(lambda x, y: x+y, [re_com.sub(r'', i) for i in bz_list])
        else:
            item['bz'] = ''
        # 获取全部内容链接
        whole_url = selector.xpath('//a[@id="pcgg"]/@onclick').get()
        if whole_url:
            content_data = re.search(r'goToPcgg\((\d)[\,，]\'(.*?)\'[\)）]', whole_url)
            form_data = {
                        "lx": str(content_data.group(1)),
                        "id": str(content_data.group(2)),
                        }
            yield scrapy.FormRequest(
                url='http://pccz.court.gov.cn/pcajxxw/gkaj/gkajindex',
                formdata=form_data,
                callback=self.parse_source_url,
                meta={'item': deepcopy(item)},
                priority=3,
            )
        else:
           yield item

    def parse_source_url(self, response):
        item = response.meta.get('item')
        selector = scrapy.Selector(text=response.text)
        base_data = selector.xpath('//li[@class="clearfix"]')
        for data in base_data:
            links = data.xpath('./div/h4/a/@href').get().strip()
            item['cf_cfmc'] = data.xpath('./div/h4/a/@title').get()
            item['cf_type'] = data.xpath('.//span[@class="ajlx"]//text()').get()  # 案件类型  没设计这个字段
            jdrq = data.xpath('.//span[@class="date"]//text()').get()  # 案件发布日期  没设计这个字段
            if jdrq:
                item['jcrq'] = jdrq

            else:
                item['jcrq'] = ''
            item['bzxr'] = data.xpath('./div[@class="center"]/p/text()').get('')  # 执行的法院  没设计这个字段
            source_url = urljoin('http://pccz.court.gov.cn/pcajxxw/', links)
            yield scrapy.Request(
                url=source_url,
                callback=self.parse_details,
                meta={'item': deepcopy(item)},
                priority=4,
            )

    def parse_details(self, response):
        re_com = re.compile(r'\r|\n|\t|\s')
        item = response.meta.get('item')
        item['zqr'] = response.url
        item['fb_dw'] = response.xpath('//td[contains(text(),"公 开 人：")]//text()').re_first(r'公 开 人：(.+)', '')  # 公开人
        # 文书内容以及其他提取字段
        cf_jg_list = response.xpath('//div[@class="detail_text"]/div//text()').getall()
        if cf_jg_list:
            cf_jg_list_data = cf_jg_list
        else:
            cf_jg_list_data = response.xpath('//div[@class="detail_text"]/p//text()').getall()

        if cf_jg_list_data:
            cf_jg = reduce(lambda x,y: x+y, [re_com.sub(r'', i) for i in cf_jg_list_data])
            item['cf_jg'] = cf_jg
            item['ws_nr_txt'] = cf_jg
            jcrq = get_jcrq_date(cf_jg)
            item['cf_jdrq'] = deal_chinese_data(jcrq)
        else:
            item['cf_jg'] = ''
            item['ws_nr_txt'] = ''
            item['cf_jdrq'] = None

        item['zj_jgxx'] = response.xpath('//li[@class="download"]/a/@href').get('')  # 文件对应得PDF下载链接
        # 附件下载链接
        wbbz_list = response.xpath('//div[@class="detail_bottom_con clearfix"]/div//a/@href').getall()
        if wbbz_list:
            item['wbbz'] = str(wbbz_list)
        else:
            item['wbbz'] = ''
        yield item