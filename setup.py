import os

from setuptools import setup

def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(
    name='hypnotoad',
    version='0.1.6',
    description='A utility that aids in transporting directory '+
                'information from one or more data sources to various '+
                'applications on a cluster using a standard interface. '+
                'Not Zoidberg.',
    long_description=open('README.txt').read(),
    url='http://github.com/hpc/hypnotoad/',
    license='3-clause BSD',
    author='Jon Bringhurst',
    author_email='jon@bringhurst.org',
    py_modules=['hypnotoad'],
    include_package_data=True,
    scripts=['hypnotoad/bin/hypnotoad'],
    packages=find_packages(exclude=[]),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: 3-clause BSD',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

# EOF
