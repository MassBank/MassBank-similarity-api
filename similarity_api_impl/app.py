import os
import sys

# Add the 'gen' directory to the PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../gen'))

import connexion
from flask_cors import CORS
import logging
from similarity_api import encoder
from flask import redirect, request
from waitress import create_server
from waitress.channel import HTTPChannel
from waitress.task import ThreadedTaskDispatcher
from similarity_api_impl.spectra_loader import spectra_loader

VERBOSE = os.environ.get('VERBOSE', "false")
CONTEXT_PATH = os.environ.get('CONTEXT_PATH', '')
logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

app = connexion.App(__name__, specification_dir='..')
app.app.json_encoder = encoder.JSONEncoder
app.add_api('openapi.yaml',
            base_path=CONTEXT_PATH,
            arguments={'title': 'Similarity score api for MassBank'},
            pythonic_params=True)
CORS(app.app)

spectra_loader.load_spectra()

# Enable verbose logging if set
@app.app.before_request
def log_request_info():
    if VERBOSE == "true":
        logging.getLogger('waitress').setLevel(logging.DEBUG)
        app.app.logger.info(f"{request.method} {request.path} from {request.remote_addr}")


@app.app.route(f'{CONTEXT_PATH}/')
def index():
    return redirect(f'{CONTEXT_PATH}/ui/')


class ProbeDispatcher(ThreadedTaskDispatcher):
    def __init__(self, threads, context_path):
        super().__init__()
        prefix = context_path.rstrip("/")
        self.probe_paths = {f"{prefix}/readiness", f"{prefix}/liveness"}
        self.probes = ThreadedTaskDispatcher()
        self.probes.set_thread_count(1)
        self.set_thread_count(threads)

    def add_task(self, task):
        # Waitress 3.0.2 dispatches the channel once per request, including
        # subsequent requests on a keep-alive connection.
        if isinstance(task, HTTPChannel):
            request = task.requests[0]
            if (
                request.error is None
                and request.command in ("GET", "HEAD")
                and request.path in self.probe_paths
            ):
                self.probes.add_task(task)
                return
        super().add_task(task)

    def shutdown(self, cancel_pending=True, timeout=5):
        self.probes.shutdown(cancel_pending, timeout)
        super().shutdown(cancel_pending, timeout)


def create_http_server(app, *, threads, context_path, listen="*:8080"):
    if threads < 1:
        raise ValueError("THREADS must be at least 1")
    dispatcher = ProbeDispatcher(threads, context_path)
    try:
        # Waitress has no public hook for routing requests before queueing.
        return create_server(app, listen=listen, threads=threads, _dispatcher=dispatcher)
    except (OSError, ValueError):
        dispatcher.shutdown()
        raise


def serve_app():
    server = create_http_server(
        app, threads=int(os.environ.get('THREADS', '2')), context_path=CONTEXT_PATH
    )
    server.print_listen("Serving on http://{}:{}")
    server.run()
