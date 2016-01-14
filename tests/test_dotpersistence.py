import os
import mock
from unittest import TestCase
from scrapy.settings import Settings
from scrapy.exceptions import NotConfigured

from scrapy_dotpersistence import DotScrapyPersistence

class DotScrapyPersisitenceTestCase(TestCase):

    def setUp(self):
        self.mocked_proc = mock.Mock()
        self.mocked_proc.communicate.return_value = ([], None)
        self.mocked_proc.wait.return_value = 0
        mocked_popen = mock.Mock()
        mocked_popen.return_value = self.mocked_proc
        self.patch = mock.patch('subprocess.Popen', mocked_popen)
        crawler_mock = mock.Mock()
        crawler_mock.settings = Settings({
            'DOTSCRAPY_ENABLED': True,
            'DOTSCRAPY_DIR': '/tmp/.scrapy',
            'ADDONS_S3_BUCKET': 'test-bucket',
            'ADDONS_AWS_ACCESS_KEY_ID': 'access-key',
            'ADDONS_AWS_SECRET_ACCESS_KEY': 'secret-key',
            'ADDONS_AWS_USERNAME': 'test-user',
        })
        os.environ.update({
            'SCRAPY_JOB': '123/45/67',
            'SCRAPY_PROJECT_ID': '123',
            'SCRAPY_SPIDER': 'testspider',
            'HOME': '/home/user'
        })
        self.patch.start()
        self.instance = DotScrapyPersistence.from_crawler(crawler_mock)

    def test_from_crawler(self):
        crawler_mock = mock.Mock()
        crawler_mock.settings = Settings()
        self.assertRaises(NotConfigured,
                          DotScrapyPersistence.from_crawler,
                          crawler_mock)
        # add needed settings for from_crawler()
        crawler_mock.settings.set('DOTSCRAPY_ENABLED', True)
        crawler_mock.settings.set('ADDONS_S3_BUCKET', 's3-test-bucket')
        instance = DotScrapyPersistence.from_crawler(crawler_mock)
        assert isinstance(instance, DotScrapyPersistence)
    
    def test_init(self):
        assert self.instance.AWS_ACCESS_KEY_ID == 'access-key'
        assert self.instance.AWS_SECRET_ACCESS_KEY == 'secret-key'
        assert self.instance._bucket == 'test-bucket'
        assert self.instance._bucket_folder == 'test-user'
        assert self.instance._projectid == '123'
        assert self.instance._spider == 'testspider'
        assert self.instance._localpath == '/tmp/.scrapy'
        assert self.instance._env == {
            'HOME': '/home/user',
            'AWS_ACCESS_KEY_ID': 'access-key',
            'AWS_SECRET_ACCESS_KEY': 'secret-key',
        }

    def tearDown(self):
        self.patch.stop()
