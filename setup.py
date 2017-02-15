import setuptools
import sys

assert sys.version_info >= (3, 4)

setuptools.setup(
  name='op-service',
  version='1.0.3',
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
