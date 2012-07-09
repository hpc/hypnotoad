from setuptools import setup, find_packages

setup (
    name               = 'hypnotoad',
    version            = '0.1.2',
    author             = 'Jon Bringhurst',
    author_email       = 'jonb@lanl.gov',
    url                = 'https://www.git.lanl.gov/rm/hypnotoad',
    license            = 'LICENSE.txt',
    scripts            = ['hypnotoad/bin/hypnotoad'],

    long_description   = open('README.txt').read(),
    description        = 'A utility that aids in transporting directory ' +
                         'information from one or more data sources to various ' +
                         'applications on a cluster using a standard interface. ' +
                         'Not Zoidberg.',

    packages           = find_packages(),
)

from pylint.lint import Run
Run(['--errors-only', 'hypnotoad']) 

# EOF
