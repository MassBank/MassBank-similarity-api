import os
from pathlib import Path

from flask_testing import TestCase


class MyBaseTestCase(TestCase):

    def create_app(self):
        config = {
            "DATA_DIR": str(Path(__file__).with_name("MassBank-test-data")),
            "CONTEXT_PATH": "",
        }
        previous = {key: os.environ.get(key) for key in config}
        os.environ.update(config)
        try:
            # Importing the service app initializes its reference snapshot.
            from similarity_api_impl.app import app
        finally:
            for key, value in previous.items():
                if value is None:
                    del os.environ[key]
                else:
                    os.environ[key] = value
        return app.app
