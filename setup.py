#!/usr/bin/env python3

import os
from distutils.core import setup
from setuptools import find_packages
from oflex.version import __version__

setup(
  name='oflex',
  version= __version__,
  description="Opinionated flask extensions for login & connection pooling",
  author="Abe Winter",
  author_email="awinter.public+oflex@gmail.com",
  url="https://github.com/abe-winter/oflex",
  packages=find_packages(include=['oflex', 'oflex.*']),
  keywords=['flask', 'pooling', 'login', 'auth'],
  install_requires=[
    'flask==1.*',
    'psycopg2-binary==2.*',
    'pyyaml==5.4.*',
    'redis==3.5.*',
    'scrypt==0.8.*',
  ],
  extras_require={
    'sms': ['twilio', 'phonenumbers'],
  },
  python_requires='>=3.6', # for format strings
  long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
  long_description_content_type='text/markdown',
  include_package_data=True,
)
