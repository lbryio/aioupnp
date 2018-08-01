__version__ = "0.0.1a3"
__name__ = "txupnp"
__author__ = "Jack Robison"
__maintainer__ = "Jack Robison"
__license__ = "MIT"
__email__ = "jackrobison@lbry.io"


import logging
log = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)-15s-%(filename)s:%(lineno)s->%(message)s'))
log.addHandler(handler)
log.setLevel(logging.INFO)
