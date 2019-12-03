# -*- coding: utf-8 -*-
import scrapy


class CourtAlbbSpider(scrapy.Spider):
    name = 'court_albb'
    allowed_domains = ['sf.taobao.com']
    start_urls = ['https://sf.taobao.com/court_list.htm?spm=a213w.3064813.sfhead2014.7.6e295dadVjIVbZ']

    def parse(self, response):
        item = {}
        courts = response.xpath('//dl[@class="city"]//dd//span/a')
        for data in courts:
            result = data.xpath('normalize-space(.)').get()
            item['name'] = result
            # print(item)
            yield item