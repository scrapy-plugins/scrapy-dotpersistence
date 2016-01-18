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
        if not enabled or 'SCRAPY_JOB' not in os.environ:
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
        self._projectid = os.environ['SCRAPY_PROJECT_ID']
        self._spider = os.environ['SCRAPY_SPIDER']
        self._localpath = os.environ.get(
            'DOTSCRAPY_DIR', os.path.join(os.getcwd(), '.scrapy/'))
        self._env = {
            'HOME': os.getenv('HOME'),
            'PATH': os.getenv('PATH'),
            'AWS_ACCESS_KEY_ID': self.AWS_ACCESS_KEY_ID,
            'AWS_SECRET_ACCESS_KEY': self.AWS_SECRET_ACCESS_KEY
        }
        crawler.signals.connect(self._store_data, signals.engine_stopped)
        self._load_data()

    def _load_data(self):
        if self._bucket_folder:
            self._s3path = 's3://{0}/{1}/{2}/dot-scrapy/{3}/'.format(
                self._bucket, self._bucket_folder, self._projectid,
                self._spider
            )
        else:
            self._s3path = 's3://{0}/{1}/dot-scrapy/{2}/'.format(
                self._bucket, self._projectid, self._spider
            )
        logger.info('Syncing .scrapy directory from %s' % self._s3path)
        # pre-create dest dir as non-existent destination is treated as file
        # by s3cmd (1.1.0)
        if not os.path.isdir(self._localpath):
            os.makedirs(self._localpath)

        cmd = ['s3cmd', 'sync', '--no-preserve', self._s3path, self._localpath]
        self._call(cmd)

    def _store_data(self):
        # check for reason status here?
        logger.info('Syncing .scrapy directory to %s' % self._s3path)
        cmd = ['s3cmd', 'sync', '--no-preserve', '--delete-removed',
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
