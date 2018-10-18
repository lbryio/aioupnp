set -x

rm -rf /tmp/.wine-*

apt-get -qq update
apt-get -qq install -y git

pip install setuptools_scm

cd aioupnp
pip install -e .
pyinstaller -F -n aioupnp aioupnp/__main__.py
