import os
from setuptools import setup, find_packages  # type: ignore
from aioupnp import __version__, __name__, __email__, __author__, __license__

console_scripts = [
    'aioupnp = aioupnp.__main__:main',
]

package_name = "aioupnp"
base_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(base_dir, 'README.md'), 'rb') as f:
    long_description = f.read().decode('utf-8')

setup(
    name=__name__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    description="UPnP for asyncio",
    keywords="upnp asyncio",
    long_description=long_description,
    url="https://github.com/lbryio/aioupnp",
    license=__license__,
    packages=find_packages(),
    entry_points={'console_scripts': console_scripts},
    install_requires=[
        'netifaces',
    ],
)
