import logging

import connexion
from flask_testing import TestCase

from similarity_api.encoder import JSONEncoder


class MyBaseTestCase(TestCase):

    def create_app(self):
        logging.getLogger('connexion.operation').setLevel('ERROR')
        app = connexion.App(__name__, specification_dir='..')
        app.app.json_encoder = JSONEncoder
        app.add_api('openapi.yaml',
                    arguments={'title': 'Similarity score api for MassBank'},
                    pythonic_params=True)
        return app.app
