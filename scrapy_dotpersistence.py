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
        if bucket is None:
            raise NotConfigured("ADDONS_S3_BUCKET is required")

        aws_access_key_id = settings.get('ADDONS_AWS_ACCESS_KEY_ID')
        if aws_access_key_id is None:
            raise NotConfigured("ADDONS_AWS_ACCESS_KEY_ID is required")

        aws_secret_access_key = settings.get('ADDONS_AWS_SECRET_ACCESS_KEY')
        if aws_secret_access_key is None:
            raise NotConfigured("ADDONS_AWS_SECRET_ACCESS_KEY is required")

        return cls(crawler, bucket, aws_access_key_id, aws_secret_access_key)

    def __init__(self, crawler, bucket, aws_access_key_id, aws_secret_access_key):
        self._bucket = bucket
        self.AWS_ACCESS_KEY_ID = aws_access_key_id
        self.AWS_SECRET_ACCESS_KEY = aws_secret_access_key

        self._aws_username = crawler.settings.get('ADDONS_AWS_USERNAME')
        self._projectid = os.environ.get('SCRAPY_PROJECT_ID')
        self._spider = os.environ.get('SCRAPY_SPIDER', "all_spiders")
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
        path = "/".join(
            filter(None, [self._bucket, self._aws_username, self._projectid])
        )
        return "s3://{0}/dot-scrapy/{1}/".format(path, self._spider)

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
