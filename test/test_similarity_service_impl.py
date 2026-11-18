import os
import sys
# Add the 'gen' directory to the PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../gen'))

import unittest
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from threading import Event, Thread

from flask import json
from similarity_api.models import Peak, SimilarityCalculation
from test import MyBaseTestCase


class TestSimilarityApiImplController(MyBaseTestCase):

    def setUp(self):
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def test_probes_bypass_busy_waitress_worker_on_same_port(self):
        from similarity_api_impl.app import create_http_server

        worker_busy, release_worker, stop_server = Event(), Event(), Event()

        def application(environ, start_response):
            if environ["PATH_INFO"] == "/similarity":
                worker_busy.set()
                if not release_worker.wait(10):
                    raise TimeoutError("Test did not release the regular worker")
            return self.app(environ, start_response)

        server = create_http_server(
            application, threads=1, context_path="", listen="127.0.0.1:0"
        )

        def run_server():
            try:
                while not stop_server.is_set():
                    server.asyncore.loop(timeout=0.05, map=server._map, count=1)
            finally:
                server.task_dispatcher.shutdown()
                server.asyncore.close_all(server._map)

        def request(method, path, body=None, headers=None):
            connection = HTTPConnection("127.0.0.1", server.effective_port, timeout=5)
            try:
                connection.request(method, path, body=body, headers=headers or {})
                response = connection.getresponse()
                return response.status, response.read()
            finally:
                connection.close()

        thread = Thread(target=run_server, daemon=True)
        thread.start()
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                similarity = pool.submit(
                    request, "POST", "/similarity",
                    '{"peak_list":[{"mz":147.063,"intensity":121.684}]}',
                    self.headers,
                )
                try:
                    self.assertTrue(worker_busy.wait(3))
                    self.assertEqual(request("GET", "/readiness"), (200, b""))
                    self.assertEqual(request("GET", "/liveness"), (200, b""))
                    self.assertFalse(similarity.done())
                finally:
                    release_worker.set()
                self.assertEqual(similarity.result()[0], 200)
        finally:
            stop_server.set()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())

    def test_similarity_post_with_reference_spectra_list(self):
        """Test case for similarity_post with a reference spectra list
        """
        similarity_calculation = SimilarityCalculation(
            peak_list=[
                Peak(mz=147.063, intensity=121.684),
                Peak(mz=303.050, intensity=10000.000),
                Peak(mz=449.108, intensity=657.368),
                Peak(mz=465.102, intensity=5884.210),
                Peak(mz=611.161, intensity=6700.000)],
            reference_spectra_list=[
                "MSBNK-IPB_Halle-PB001341",
                "MSBNK-IPB_Halle-PB001342",
                "MSBNK-IPB_Halle-PB001343",
                "MSBNK-IPB_Halle-PB006202",
                "MSBNK-IPB_Halle-PB006203"],
            similarity_fn="cosine")
        response = self.client.open(
            '/similarity',
            method='POST',
            headers=self.headers,
            data=json.dumps(similarity_calculation),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))
        self.assertEqual(
            first=response.json,
            second={'similarity_score_list': [
                {'accession': 'MSBNK-IPB_Halle-PB001341', 'similarity_score': 0.9999987337877411},
                {'accession': 'MSBNK-IPB_Halle-PB001342', 'similarity_score': 0.9997024900194288},
                {'accession': 'MSBNK-IPB_Halle-PB006202', 'similarity_score': 0.7797803260380126},
                {'accession': 'MSBNK-IPB_Halle-PB001343', 'similarity_score': 0.7453832548137632},
                {'accession': 'MSBNK-IPB_Halle-PB006203', 'similarity_score': 0.7448505386345436}
            ]})

    def test_similarity_post_with_empty_reference_spectra_list(self):
        """Test case for similarity_post with an empty reference spectra list
        """
        similarity_calculation = SimilarityCalculation(
            peak_list=[
                Peak(mz=147.063, intensity=121.684),
                Peak(mz=303.050, intensity=10000.000),
                Peak(mz=449.108, intensity=657.368),
                Peak(mz=465.102, intensity=5884.210),
                Peak(mz=611.161, intensity=6700.000)],
            reference_spectra_list=[],
            similarity_fn="cosine")
        response = self.client.open(
            '/similarity',
            method='POST',
            headers=self.headers,
            data=json.dumps(similarity_calculation),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))
        self.assertEqual(
            first=response.json['similarity_score_list'][0:5],
            second=[
                {'accession': 'MSBNK-IPB_Halle-PB001341', 'similarity_score': 0.9999987337877411},
                {'accession': 'MSBNK-IPB_Halle-PB001342', 'similarity_score': 0.9997024900194288},
                {'accession': 'MSBNK-IPB_Halle-PB006201', 'similarity_score': 0.8742310139566003},
                {'accession': 'MSBNK-IPB_Halle-PB006202', 'similarity_score': 0.7797803260380126},
                {'accession': 'MSBNK-IPB_Halle-PB001343', 'similarity_score': 0.7453832548137632}
            ])
        self.assertTrue(len(response.json['similarity_score_list']) > 5)

    def test_similarity_post_with_only_peaklist(self):
        """Test case for similarity_post with only peaklist given
        """
        similarity_calculation = SimilarityCalculation(
            peak_list=[
                Peak(mz=147.063, intensity=121.684),
                Peak(mz=303.050, intensity=10000.000),
                Peak(mz=449.108, intensity=657.368),
                Peak(mz=465.102, intensity=5884.210),
                Peak(mz=611.161, intensity=6700.000)])
        response = self.client.open(
            '/similarity',
            method='POST',
            headers=self.headers,
            data=json.dumps(similarity_calculation),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))
        self.assertEqual(
            first=response.json['similarity_score_list'][0:5],
            second=[
                {'accession': 'MSBNK-IPB_Halle-PB001341', 'similarity_score': 0.9999987337877411},
                {'accession': 'MSBNK-IPB_Halle-PB001342', 'similarity_score': 0.9997024900194288},
                {'accession': 'MSBNK-IPB_Halle-PB006201', 'similarity_score': 0.8742310139566003},
                {'accession': 'MSBNK-IPB_Halle-PB006202', 'similarity_score': 0.7797803260380126},
                {'accession': 'MSBNK-IPB_Halle-PB001343', 'similarity_score': 0.7453832548137632}
            ])
        self.assertTrue(len(response.json['similarity_score_list']) > 5)

    def test_version_get(self):
        """Test case for version_get
        """
        response = self.client.open(
            '/version',
            method='GET',
            headers=self.headers)
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))
        self.assertTrue(response.json.startswith('similarity api'))


if __name__ == '__main__':
    unittest.main()
