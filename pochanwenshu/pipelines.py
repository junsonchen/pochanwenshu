# -*- coding: utf-8 -*-
import time

import logging
import pymongo
import redis
from scrapy.exceptions import DropItem

from pochanwenshu import settings
from pochanwenshu.work_utils.filter_fact import filter_factory
from pochanwenshu.work_utils.es_fact import EsObject

logger = logging.getLogger(__name__)


class PochanwenshuPipeline(object):
    def process_item(self, item, spider):
        # 添加时间戳
        item['cj_sj'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        # # 添加主键去重id
        ws_pc_id = filter_factory(item)
        if ws_pc_id:
            item['ws_pc_id'] = ws_pc_id
        else:
            DropItem(item)
        return item


#  存储到mongodb的类
class MongoPipeline(object):

    def __init__(self, mongo_uri, mongo_db):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[mongo_db]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATA_BASE')
        )

    def open_spider(self, spider):  # 爬虫一旦开启，就会实现这个方法，连接到数据库
        self.collection = self.db[spider.name]  # 连表

    def process_item(self, item, spider):
        if item:
            # self.collection.insert(dict(item))
            self.collection.update({'ws_pc_id': item['ws_pc_id']}, dict(item), True)
            # logger.info("数据插入成功:%s"%item)
            return item

    def close_spider(self, spider):
        self.client.close()


class Save2eEsPipeline(object):
    def __init__(self):
        self.es = EsObject(index_name=settings.INDEX_NAME, index_type=settings.INDEX_TYPE, host=settings.ES_HOST, port=settings.ES_PORT)

    def process_item(self, item, spider):
        if item:
            # 获取唯一ID
            _id = item['ws_pc_id']
            res1 = self.es.get_data_by_id(_id)
            if res1.get('found') == True:
                logger.debug("该数据已存在%s" % _id)
            else:
                self.es.insert_data(dict(item), _id)
                logger.debug("----------抓取成功,开始插入数据%s" % _id)
                return item


class RedisPipeline(object):
    def __init__(self, redis_db, redis_port):
        self.pool = redis.ConnectionPool(host=redis_db, port=redis_port, db=3, password='axy@2019')
        self.client = redis.Redis(connection_pool=self.pool, decode_responses=True)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_db=crawler.settings.get('REDIS_HOST'),
            redis_port=crawler.settings.get('REDIS_PORT'),
        )

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.insert_item(item)
        return item

    def insert_item(self, item):
        if isinstance(item, dict):
            results = item.get('name')
            self.client.sadd('court:name', results)  # 淘宝拍卖法院名称
            # for i in results:
            #     # self.client.rpush('court:name', i)  # 存list
            #     self.client.sadd('court:name', i)  # 存集合，去重