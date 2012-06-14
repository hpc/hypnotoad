from distutils.core import setup

setup (
    name             = 'Hypnotoad',
    version          = '0.1.0',
    author           = 'Jon Bringhurst',
    author_email     = 'jonb@lanl.gov',
    packages         = ['hypnotoad'],
    url              = 'https://www.git.lanl.gov/rm/hypnotoad',
    license          = 'LICENSE.txt',

    description      = 'A utility that aids in transporting directory ' +
                       'information from one or more data sources to various ' +
                       'applications on a cluster using a standard interface. ' +
                       'Not Zoidberg.',

    long_description = open('README.txt').read(),

    entry_points = {
        'console_scripts' : [
            'release = hypnotoad.releaser.release:main',
            'prerelease = hypnotoad.releaser.prerelease:main',
        ]
    }
)

# EOF
