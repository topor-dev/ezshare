from os.path import dirname, join

from setuptools import find_packages, setup

import ezshare

with open(join(dirname(__file__), 'README.md')) as f:
    long_description = f.read()

setup(
    name='ezshare',
    version=ezshare.__version__,
    description='Easy way to share files through net',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/topor-dev/ezshare',
    author='Vadim Tokarev',
    license='MIT',
    packages=find_packages(),
    python_requires='~=3.5',
    entry_points={
        'console_scripts': [
            'ezshare=ezshare:main',
        ],
    },
)
