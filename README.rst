=====================
scrapy-dotpersistence
=====================

Scrapy extension to sync `.scrapy` folder to an S3 bucket.

Installation
============

You can install scrapy-dotpersistence using pip::

    pip install scrapy-dotpersistence

You can then enable the extension in your `settings.py`::

    EXTENSIONS = {
        ...
        'scrapy_dotpersistence.DotScrapyPersistence': 0
    }

How to use it
=============

Enable extension through `settings.py`::

    DOTSCRAPY_ENABLED = True

Configure the exension through `settings.py`::

    ADDONS_AWS_ACCESS_KEY_ID = "ABC"
    ADDONS_AWS_SECRET_ACCESS_KEY = "DEF"
    ADDONS_AWS_USERNAME = "username"
    ADDONS_S3_BUCKET = "test-bucket-name"
