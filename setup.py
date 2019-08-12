from setuptools import setup, find_packages

setup(
    name='scrapy-dotpersistence',
    version='0.3.0',
    url='https://github.com/scrapy-plugins/scrapy-dotpersistence',
    description='Scrapy extension to sync `.scrapy` folder to an S3 bucket',
    long_description=open('README.rst').read(),
    author='Scrapy developers',
    license='BSD',
    py_modules=['scrapy_dotpersistence'],
    zip_safe=False,
    author_email='opensource@scrapinghub.com',
    platforms=['Any'],
    classifiers=[
        'Framework :: Scrapy',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    install_requires=[
        'Scrapy>=1.0.3',
        'awscli>=1.10.51',
    ],
)
