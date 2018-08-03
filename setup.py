import os
from setuptools import setup, find_packages
from txupnp import __version__, __name__, __email__, __author__, __license__

console_scripts = [
    'txupnp-cli = txupnp.cli:main',
]

package_name = "txupnp"
base_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(base_dir, 'README.md'), 'rb') as f:
    long_description = f.read().decode('utf-8')

setup(
    name=__name__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    description="UPnP for twisted",
    keywords="upnp twisted",
    long_description=long_description,
    url="https://github.com/lbryio/txupnp",
    license=__license__,
    packages=find_packages(),
    entry_points={'console_scripts': console_scripts},
    install_requires=[
        'twisted[tls]',
        'treq',
        'netifaces',
    ],
)
