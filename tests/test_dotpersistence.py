import os
from unittest import TestCase

import mock
import pytest
from scrapy.exceptions import NotConfigured
from scrapy.settings import Settings

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
            'AWS_SESSION_TOKEN': 'test-token'
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
        crawler_mock.settings.set('ADDONS_AWS_ACCESS_KEY_ID', 's3-acess-key')
        crawler_mock.settings.set('ADDONS_AWS_SECRET_ACCESS_KEY', 's3-secret-key')
        crawler_mock.settings.set('ADDONS_AWS_SESSION_TOKEN', 'test-token')
        instance = DotScrapyPersistence.from_crawler(crawler_mock)
        assert isinstance(instance, DotScrapyPersistence)

    def test_init(self):
        assert self.instance._bucket == 'test-bucket'
        assert self.instance._aws_username == 'test-user'
        assert self.instance._projectid == '123'
        assert self.instance._spider == 'testspider'
        assert self.instance._localpath == '/tmp/.scrapy'
        assert self.instance._env == {
            'HOME': '/home/user',
            'PATH': os.environ['PATH'],
            'AWS_ACCESS_KEY_ID': 'access-key',
            'AWS_SECRET_ACCESS_KEY': 'secret-key',
            'AWS_SESSION_TOKEN': 'test-token'
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
        mocked_call.assert_called_with(
            ['aws', 's3', 'sync', s3_path1, '/tmp/.scrapy'])

        # test other s3_path w/o bucket_folder
        mocked_call.reset()
        self.instance._aws_username = None
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
                 'AWS_SECRET_ACCESS_KEY': 'secret-key',
                 'AWS_SESSION_TOKEN': 'test-token'})
        self.mocked_proc.communicate.assert_called_with()
        self.mocked_proc.wait.assert_called_with()

    def tearDown(self):
        self.patch.stop()
        del os.environ['SCRAPY_JOB']
        del os.environ['SCRAPY_PROJECT_ID']
        del os.environ['SCRAPY_SPIDER']
        del os.environ['HOME']
        del os.environ['DOTSCRAPY_DIR']


@pytest.mark.parametrize(
    "enable_setting", ["DOTSCRAPY_ENABLED", "DOTSCRAPYPERSISTENCE_ENABLED"]
)
def test_extension_enabled(mocker, get_test_crawler, enable_setting, settings):
    mocker.patch.object(DotScrapyPersistence, "_load_data", autospec=True)
    del settings["DOTSCRAPY_ENABLED"]

    settings[enable_setting] = True

    crawler = get_test_crawler(settings_dict=settings)
    try:
        extension = DotScrapyPersistence.from_crawler(crawler)  # noqa
    except NotConfigured as excinfo:
        pytest.fail(excinfo)


@pytest.mark.parametrize(
    "disable_setting", ["DOTSCRAPY_ENABLED", "DOTSCRAPYPERSISTENCE_ENABLED"]
)
def test_extension_disabled(mocker, get_test_crawler, disable_setting, settings):
    mocker.patch.object(DotScrapyPersistence, "_load_data", autospec=True)
    del settings["DOTSCRAPY_ENABLED"]

    settings[disable_setting] = False

    crawler = get_test_crawler(settings_dict=settings)
    with pytest.raises(NotConfigured):
        extension = DotScrapyPersistence.from_crawler(crawler)  # noqa


@pytest.mark.parametrize(
    "missing_setting",
    ["ADDONS_S3_BUCKET", "ADDONS_AWS_ACCESS_KEY_ID", "ADDONS_AWS_SECRET_ACCESS_KEY"],
)
def test_aws_required_settings(mocker, get_test_crawler, settings, missing_setting):
    mocker.patch.object(DotScrapyPersistence, "_load_data", autospec=True)

    del settings[missing_setting]

    crawler = get_test_crawler(settings_dict=settings)
    with pytest.raises(NotConfigured):
        extension = DotScrapyPersistence.from_crawler(crawler)  # noqa


def test_s3path_in_scrapy_cloud_without_aws_username(
    mocker, monkeypatch, get_test_crawler, settings
):
    mocker.patch.object(DotScrapyPersistence, "_load_data", autospec=True)
    monkeypatch.setenv("SCRAPY_PROJECT_ID", "123")
    monkeypatch.setenv("SCRAPY_SPIDER", "test_spider")
    crawler = get_test_crawler(settings)
    extension = DotScrapyPersistence.from_crawler(crawler)

    assert extension._s3path == "s3://s3_bucket/123/dot-scrapy/test_spider/"


def test_s3path_in_scrapy_cloud_with_aws_username(
    mocker, monkeypatch, get_test_crawler, settings
):
    mocker.patch.object(DotScrapyPersistence, "_load_data", autospec=True)
    monkeypatch.setenv("SCRAPY_PROJECT_ID", "123")
    monkeypatch.setenv("SCRAPY_SPIDER", "test_spider")

    settings["ADDONS_AWS_USERNAME"] = "username"
    crawler = get_test_crawler(settings)
    extension = DotScrapyPersistence.from_crawler(crawler)

    assert extension._s3path == "s3://s3_bucket/username/123/dot-scrapy/test_spider/"


def test_s3path_running_locally_without_aws_username(
    mocker, get_test_crawler, settings
):
    mocker.patch.object(DotScrapyPersistence, "_load_data", autospec=True)

    crawler = get_test_crawler(settings)
    extension = DotScrapyPersistence.from_crawler(crawler)

    assert extension._s3path == "s3://s3_bucket/dot-scrapy/test_spider/"


def test_s3path_running_locally_with_aws_username(mocker, get_test_crawler, settings):
    mocker.patch.object(DotScrapyPersistence, "_load_data", autospec=True)

    settings["ADDONS_AWS_USERNAME"] = "username"
    crawler = get_test_crawler(settings)
    extension = DotScrapyPersistence.from_crawler(crawler)

    assert extension._s3path == "s3://s3_bucket/username/dot-scrapy/test_spider/"
