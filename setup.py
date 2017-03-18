# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='eldam',
    version='1.0.1',
    description="Elastic Search transaction based data manager.",
    long_description="Elastic Search data manger with zope transaction support. *****SAMMY***** 133740 wants to put his name",
    url="https://github.com/bemineni/edm",
    author='Srikanth Bemineni',
    author_email='srikanth.bemineni@gmail.com',
    license='MIT',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
           'Development Status :: 5 - Production/Stable',
            # Indicate who your project is intended for
           'Intended Audience :: Developers',
           'Topic :: Database',
           # Pick your license as you wish (should match "license" above)
           'License :: OSI Approved :: MIT License',
           # Specify the Python versions you support here. In particular, ensure
           # that you indicate whether you support Python 2, Python 3 or both.
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5'
          ],
    keywords='ElasticSearch Data manager Development',
    packages=find_packages(exclude=['test']),
    install_requires=['elasticsearch>=5.0.0,<6.0.0',
                      'transaction',
                      'zope.interface',
                      'pyyaml']
    )




