import setuptools
import sys

assert sys.version_info >= (2, 7), 'Requires Python 2.7+'

setuptools.setup(
  name='op_service',
  version='1.0.0',
  packages=['op_service'],
  author='Alex Exarhos',
  author_email='alexexarhos@gmail.com'
)
