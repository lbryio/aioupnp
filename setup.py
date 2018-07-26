from setuptools import setup, find_packages

setup(
    name="txupnp",
    version="0.0.1",
    author="Jack Robison",
    author_email="jackrobison@lbry.io",
    description="UPnP for twisted",
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'Twisted',
        'treq',
        'netifaces'
    ],
)
