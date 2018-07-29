from setuptools import setup, find_packages

console_scripts = [
    'test-txupnp = txupnp.tests.test_txupnp:main',
]

setup(
    name="txupnp",
    version="0.0.1",
    author="Jack Robison",
    author_email="jackrobison@lbry.io",
    description="UPnP for twisted",
    license='MIT',
    packages=find_packages(),
    entry_points={'console_scripts': console_scripts},
    install_requires=[
        'Twisted',
        'treq',
        'netifaces',
        'pycryptodome',
        'service-identity'
    ],
)
