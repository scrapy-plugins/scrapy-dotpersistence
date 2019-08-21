import pytest
from scrapy.utils.test import get_crawler


@pytest.fixture
def settings():
    """ Returns a dictionary with all required settings defined for the extension to work correctly """
    return {
        "DOTSCRAPY_ENABLED": True,
        "ADDONS_S3_BUCKET": "s3_bucket",
        "ADDONS_AWS_ACCESS_KEY_ID": "s3_access_key_id",
        "ADDONS_AWS_SECRET_ACCESS_KEY": "s3_secret_access_key",
    }


@pytest.fixture
def get_test_crawler():
    def _crawler(settings_dict={}):
        crawler = get_crawler(settings_dict=settings_dict)
        crawler.spider = crawler._create_spider("test_spider")
        return crawler

    return _crawler
