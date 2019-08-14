import pytest
from scrapy.utils.test import get_crawler


@pytest.fixture
def get_test_crawler():
    def _crawler(settings_dict={}):
        crawler = get_crawler(settings_dict=settings_dict)
        crawler.spider = crawler._create_spider("test_spider")
        return crawler

    return _crawler
