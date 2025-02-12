import os
import sys
# Add the 'gen' directory to the PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../gen'))

import connexion
import logging

from similarity_service import encoder
from waitress import serve

VERBOSE = os.environ.get('VERBOSE', "false")
logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

app = connexion.App(__name__, specification_dir='..')
app.app.json_encoder = encoder.JSONEncoder
app.add_api('openapi.yaml',
            arguments={'title': 'Similarity score api for MassBank3'},
            pythonic_params=True)

def serve_app():
    if VERBOSE == "true":
        from paste.translogger import TransLogger
        logging.getLogger('waitress').setLevel(logging.DEBUG)
        serve(TransLogger(app, setup_console_handler=False), listen='*:8080')
    else:
        serve(app, threads=8, listen='*:8080')
