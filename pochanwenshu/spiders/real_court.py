# -*- coding: utf-8 -*-
import scrapy
from urllib.parse import urljoin


class RealCourtSpider(scrapy.Spider):
    name = 'real_court'
    allowed_domains = ['rmfysszc.gov.cn']
    start_urls = ['https://www.rmfysszc.gov.cn/']
    post_url = 'https://www1.rmfysszc.gov.cn/News/Handler.aspx'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'pochanwenshu.middlewares.RandomUserAgentMiddlerware': 25,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,  # 禁用默认的代理
            'pochanwenshu.middlewares.RandomCompanyProxyMiddlerware': 15,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'pochanwenshu.middlewares.MyRtryMiddlerware': 95,
        },
        "ITEM_PIPELINES": {
            'pochanwenshu.pipelines.RedisPipeline': 180,
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

    def parse(self, response):
        dq_url_list = response.xpath('//table[@class="region"]//a/@href').getall()
        for link in dq_url_list[:-3]:   # 去掉港澳台地区 高级法院
            url = urljoin(response.url,link)
            yield scrapy.Request(
                url=url,
                callback=self.parse_next_page,
            )

    def parse_next_page(self, response):
        # todo 获取法院的url
        item = {}
        base_data_list = response.xpath('//div[@class="div_link_zy"]')
        for data in base_data_list:
            fid2_url_list = data.xpath('./a/@href').getall()  # 中级法院
            fid2_name_list = data.xpath('./a/@title').getall()
            base_data_url_list = data.xpath('./div//a/@href').getall()  # 基层法院
            base_name_list = data.xpath('./div//span/@title').getall()
            name = fid2_name_list + base_name_list
            url = fid2_url_list + base_data_url_list
            item['name'] = name
            item['url'] = url
            # print(item)
            yield item
