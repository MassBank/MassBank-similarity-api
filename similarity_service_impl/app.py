import os
import sys
# Add the 'gen' directory to the PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../gen'))

import connexion
import logging
import threading
from similarity_service import encoder
from waitress import serve
from flask import redirect
from similarity_service_impl.spectra_loader import spectra_loader

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

@app.app.route('/')
def index():
    return redirect('/ui/')

def serve_app():# Create and start a thread to run spectra_loader.load_spectra()
    init_thread = threading.Thread(target=spectra_loader.load_spectra)
    init_thread.start()

    if VERBOSE == "true":
        from paste.translogger import TransLogger
        logging.getLogger('waitress').setLevel(logging.DEBUG)
        serve(TransLogger(app, setup_console_handler=False), threads=2, listen='*:8080')
    else:
        serve(app, threads=2, listen='*:8080')
