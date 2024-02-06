import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] %(name)s-%(levelname)s: %(message)s', '%H:%M:%S')
stdout_handler.setFormatter(formatter)
