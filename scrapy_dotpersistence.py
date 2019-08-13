import os
import logging
import subprocess
from scrapy.exceptions import NotConfigured
from scrapy import signals


logger = logging.getLogger(__name__)


class DotScrapyPersistence(object):

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        enabled = (settings.getbool('DOTSCRAPY_ENABLED') or
                   settings.get('DOTSCRAPYPERSISTENCE_ENABLED'))
        if not enabled:
            raise NotConfigured
        bucket = settings.get('ADDONS_S3_BUCKET')
        return cls(crawler, bucket)

    def __init__(self, crawler, bucket):
        self.AWS_ACCESS_KEY_ID = crawler.settings.get(
            'ADDONS_AWS_ACCESS_KEY_ID')
        self.AWS_SECRET_ACCESS_KEY = crawler.settings.get(
            'ADDONS_AWS_SECRET_ACCESS_KEY')
        self._bucket = bucket
        self._bucket_folder = crawler.settings.get('ADDONS_AWS_USERNAME', '')
        self._projectid = os.environ.get('SCRAPY_PROJECT_ID')
        self._spider = os.environ.get('SCRAPY_SPIDER')
        self._localpath = os.environ.get(
            'DOTSCRAPY_DIR', os.path.join(os.getcwd(), '.scrapy/'))
        self._env = {
            'HOME': os.getenv('HOME'),
            'PATH': os.getenv('PATH'),
            'AWS_ACCESS_KEY_ID': self.AWS_ACCESS_KEY_ID,
            'AWS_SECRET_ACCESS_KEY': self.AWS_SECRET_ACCESS_KEY
        }
        self._load_data()
        crawler.signals.connect(self._store_data, signals.engine_stopped)

    @property
    def _s3path(self):
        if self._bucket_folder:
            return 's3://{0}/{1}/{2}/dot-scrapy/{3}/'.format(
                self._bucket, self._bucket_folder, self._projectid,
                self._spider
            )
        else:
            return 's3://{0}/{1}/dot-scrapy/{2}/'.format(
                self._bucket, self._projectid, self._spider)

    def _load_data(self):
        logger.info('Syncing .scrapy directory from %s' % self._s3path)
        cmd = ['aws', 's3', 'sync', self._s3path, self._localpath]
        self._call(cmd)

    def _store_data(self):
        # check for reason status here?
        logger.info('Syncing .scrapy directory to %s' % self._s3path)
        cmd = ['aws', 's3', 'sync', '--delete',
               self._localpath, self._s3path]
        self._call(cmd)

    def _call(self, cmd):
        p = subprocess.Popen(cmd, env=self._env,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        stdout, _ = p.communicate()
        retcode = p.wait()
        if retcode != 0:
            msg = ('Failed to sync .scrapy: %(cmd)s\n%(stdout)s' %
                   {'cmd': cmd, 'stdout': stdout[-1000:]})
            logger.error(msg)
