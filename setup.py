import setuptools
import sys

assert sys.version_info >= (2, 7), 'Requires Python 2.7+'

setuptools.setup(
  name='op_service',
  version='1.0.0',
  author='Alex Exarhos',
  author_email='alexexarhos@gmail.com',
  packages=[
    'op_service'
  ],
  install_requires=[
    'flask >= 0.11.1',
    'flask-cors >= 3.0.2'
  ]
)
