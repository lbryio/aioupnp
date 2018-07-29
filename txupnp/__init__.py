import logging
# from twisted.python import log
# observer = log.PythonLoggingObserver(loggerName=__name__)
# observer.start()
log = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)-15s-%(filename)s:%(lineno)s->%(message)s'))
log.addHandler(handler)
log.setLevel(logging.INFO)
