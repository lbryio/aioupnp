import logging

log = logging.getLogger("aioupnp")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)-15s-%(filename)s:%(lineno)s->%(message)s'))
log.addHandler(handler)
log.setLevel(logging.INFO)
