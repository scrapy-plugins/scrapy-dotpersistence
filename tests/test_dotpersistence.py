import os
import mock
from unittest import TestCase
from scrapy.settings import Settings
from scrapy.exceptions import NotConfigured

from scrapy_dotpersistence import DotScrapyPersistence


class DotScrapyPersisitenceTestCase(TestCase):

    def setUp(self):
        self.mocked_proc = mock.MagicMock()
        self.mocked_proc.communicate.return_value = ([], None)
        self.mocked_proc.wait.return_value = 0
        self.mocked_popen = mock.Mock()
        self.mocked_popen.return_value = self.mocked_proc
        self.patch = mock.patch('subprocess.Popen', self.mocked_popen)
        crawler_mock = mock.Mock()
        crawler_mock.settings = Settings({
            'DOTSCRAPY_ENABLED': True,
            'ADDONS_S3_BUCKET': 'test-bucket',
            'ADDONS_AWS_ACCESS_KEY_ID': 'access-key',
            'ADDONS_AWS_SECRET_ACCESS_KEY': 'secret-key',
            'ADDONS_AWS_USERNAME': 'test-user',
        })
        os.environ.update({
            'SCRAPY_JOB': '123/45/67',
            'SCRAPY_PROJECT_ID': '123',
            'SCRAPY_SPIDER': 'testspider',
            'HOME': '/home/user',
            'DOTSCRAPY_DIR': '/tmp/.scrapy',
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
            'PATH': os.environ['PATH'],
            'AWS_ACCESS_KEY_ID': 'access-key',
            'AWS_SECRET_ACCESS_KEY': 'secret-key',
        }
        # short checks that init called _load_data
        self.assertEqual(
            self.instance._s3path,
            's3://test-bucket/test-user/123/dot-scrapy/testspider/')
        assert self.mocked_popen.called

    def test_load_data(self):
        mocked_call = mock.Mock()
        self.instance._call = mocked_call

        self.instance._load_data()
        s3_path1 = 's3://test-bucket/test-user/123/dot-scrapy/testspider/'
        self.assertEqual(self.instance._s3path, s3_path1)
        assert os.path.exists(self.instance._localpath)
        mocked_call.assert_called_with(
            ['aws', 's3', 'sync', s3_path1, '/tmp/.scrapy'])

        # test other s3_path w/o bucket_folder
        mocked_call.reset()
        self.instance._bucket_folder = None
        self.instance._load_data()
        s3_path2 = 's3://test-bucket/123/dot-scrapy/testspider/'
        self.assertEqual(self.instance._s3path, s3_path2)
        mocked_call.assert_called_with(
            ['aws', 's3', 'sync', s3_path2, '/tmp/.scrapy'])

    def test_store_data(self):
        mocked_call = mock.Mock()
        self.instance._call = mocked_call
        self.instance._store_data()
        mocked_call.assert_called_with(
            ['aws', 's3', 'sync', '--delete', '/tmp/.scrapy',
             's3://test-bucket/test-user/123/dot-scrapy/testspider/'])

    def test_call(self):
        # reset mocks after init-related call
        self.mocked_popen.reset()
        self.mocked_proc.reset()
        self.instance._call(["test", "cmd"])
        self.mocked_popen.assert_called_with(
            ['test', 'cmd'], stderr=-2, stdout=-1,
            env={'HOME': '/home/user',
                 'PATH': os.environ['PATH'],
                 'AWS_ACCESS_KEY_ID': 'access-key',
                 'AWS_SECRET_ACCESS_KEY': 'secret-key'})
        self.mocked_proc.communicate.assert_called_with()
        self.mocked_proc.wait.assert_called_with()

    def tearDown(self):
        self.patch.stop()
