import logging

# Enable debug logging for strands library
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('strands').setLevel(logging.DEBUG)