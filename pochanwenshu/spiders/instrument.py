# -*- coding: utf-8 -*-
"""
根据法院名称进行搜索
"""
import re
import scrapy,json,logging
from copy import deepcopy
import redis
import jsonpath
logger = logging.getLogger(__name__)
#  redis连接池
pool = redis.ConnectionPool(host="114.115.201.98",port=6379, db=3, password='axy@2019')
#  从池子里面取除值
redis_client = redis.Redis(connection_pool=pool, decode_responses=True)


class InstrumentSpider(scrapy.Spider):
    name = 'instrument'
    allowed_domains = ['rmfygg.court.gov.cn']
    post_url = 'https://rmfygg.court.gov.cn/web/rmfyportal/noticeinfo?p_p_id=noticelist_WAR_rmfynoticeListportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=initNoticeList&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1'

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

# def start_requests(self):
    #     # 获取法院名称，存储到redis，用于后面搜索
    #     url = 'https://rmfygg.court.gov.cn/court-service-data/staticpage.json'
    #     yield scrapy.FormRequest(
    #         url=url,
    #         callback=self.parse_search_data,
    #     )
    #
    # def parse_search_data(self, response):
    #     item = {}
    #     post_url = 'https://rmfygg.court.gov.cn/web/rmfyportal/noticeinfo?p_p_id=noticelist_WAR_rmfynoticeListportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=initNoticeList&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1'
    #     results = json.loads(response.text)
    #     realCourt = jsonpath.jsonpath(results, expr='$..realCourt')
    #     list_court = list(set(realCourt))
    #     item['name'] = list_court
    #     yield item
    def start_requests(self):
        list_court = redis_client.smembers('court:name')
        handle_list = [
            {"name": "sEcho", "value": 1},
            {"name": "iColumns", "value": 6},
            {"name": "sColumns", "value": ",,,,,"},
            {"name": "iDisplayStart", "value": 0},
            {"name": "iDisplayLength", "value": 15},
            {"name": "mDataProp_0", "value": "null"},
            {"name": "mDataProp_1", "value": "null"},
            {"name": "mDataProp_2", "value": "null"},
            {"name": "mDataProp_3", "value": "null"},
            {"name": "mDataProp_4", "value": "null"},
            {"name": "mDataProp_5", "value": "null"},
        ]
        for court in list_court:
            court = court.decode('utf-8')
            form_data = {
                '_noticelist_WAR_rmfynoticeListportlet_content': '',
                '_noticelist_WAR_rmfynoticeListportlet_searchContent': '',
                '_noticelist_WAR_rmfynoticeListportlet_courtParam': str(court),
                '_noticelist_WAR_rmfynoticeListportlet_IEVersion': 'ie',
                '_noticelist_WAR_rmfynoticeListportlet_flag': 'click',
                '_noticelist_WAR_rmfynoticeListportlet_noticeTypeVal': '破产文书',
                '_noticelist_WAR_rmfynoticeListportlet_aoData': str(handle_list),
            }
            yield scrapy.FormRequest(
                url=self.post_url,
                formdata=form_data,
                callback=self.get_page_counts,
                meta={'form_data': form_data},
                priority=1,
            )

    def get_page_counts(self, response):
        #  解析跟翻页
        form_data = response.meta.get('form_data')
        results = json.loads(response.text)
        page_count = jsonpath.jsonpath(results, expr='$..iTotalRecords')
        if page_count:
            counts = int(int(page_count[0]) / 15) + 2
        else:
            logger.debug('该地区没有数据')
            return

        for page in range(1, counts):
            handle_list = [
                {"name": "sEcho", "value": page},
                {"name": "iColumns", "value": 6},
                {"name": "sColumns", "value": ",,,,,"},
                {"name": "iDisplayStart", "value": 15 * (page - 1)},
                {"name": "iDisplayLength", "value": 15},
                {"name": "mDataProp_0", "value": "null"},
                {"name": "mDataProp_1", "value": "null"},
                {"name": "mDataProp_2", "value": "null"},
                {"name": "mDataProp_3", "value": "null"},
                {"name": "mDataProp_4", "value": "null"},
                {"name": "mDataProp_5", "value": "null"}
            ]
            form_data['_noticelist_WAR_rmfynoticeListportlet_aoData'] = str(handle_list)
            yield scrapy.FormRequest(
                url=self.post_url,
                formdata=form_data,
                callback=self.parse_list_page,
                dont_filter=True,  # 不过滤，已经请求了第一页算页码数，不设置将获取不到第一页得数据
                priority=2,
            )

    def parse_list_page(self, response):
        item = {}
        results = json.loads(response.text)
        data_list = results.get('data')
        for data in data_list:
            item['cf_xzjg'] = data.get('court')  # 列表页法院名称
            # noticeCode = data.get('noticeCode')  # 不知道含义  pdf得位置
            # noticeCodeEnc = data.get('noticeCodeEnc')  # 不知道含义  pdf下载参数
            item['ws_nr_txt'] = data.get('noticeContent')  # 内容
            item['cf_cflb'] = data.get('noticeType')  # 类型
            # tosendPeople = data.get('tosendPeople')  # 当事人
            item['fb_rq'] = data.get('publishDate')  # 发布日期
            uuid = data.get('uuid')  # 详情页参数
            item['xq_url'] = 'https://rmfygg.court.gov.cn/web/rmfyportal/noticedetail?paramStr={}'.format(uuid)
            form_data = {'_noticedetail_WAR_rmfynoticeDetailportlet_uuid': str(uuid)}
            url = 'https://rmfygg.court.gov.cn/web/rmfyportal/noticedetail?p_p_id=noticedetail_WAR_rmfynoticeDetailportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=noticeDetail&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1'
            yield scrapy.FormRequest(
                url=url,
                formdata=form_data,
                callback=self.parse_index_page,
                meta={'item': deepcopy(item)},
                priority=3,
            )

    def parse_index_page(self, response):
        item = response.meta.get('item')
        results = json.loads(response.text)
        item['sf_sl'] = results.get('court')  # 法院名称
        item['cf_jg'] = results.get('noticeContent')  # 文书内容
        item['cf_type'] = results.get('noticeType')  # 文书类型
        item['sf'] = results.get('province')  # 省份
        item['cf_jdrq'] = results.get('publishDate')  # 决定日期
        item['cf_zt'] = results.get('publishPage')  # 刊登版面
        onames = results.get('tosendPeople')  # 当事人
        if onames == "" or onames == " " or onames == "无 " or onames == "无" or onames == "-" or onames == "- " or onames == "111":
            item['oname'] = get_oname_from_cfjg(item['cf_jg'])
        else:
            item['oname'] = onames
        item['sj_type'] = '65'
        item['site_id'] = 15176
        item['xxly'] = '人民法院公告网-破产文书'
        item['sj_ztxx'] = 1
        uploadDate = results.get('uploadDate')  # 上传文件得日期
        yield item


def get_oname_from_cfjg(txt):
    if txt:
        data = re.search(r'(裁定受理|依法受理|申请人：|关于|申请人)(.*?公司)', txt)
        if data:
            return data.group(2)
        data = re.search(r'(申请人|裁定受理)(.*?)(的申请|强制清算)', txt)
        if data:
            return data.group(2)
        return ''
    return ''