#!/usr/bin/env python3

from flask import redirect
import similarity_service_impl.app

@similarity_service_impl.app.app.route('/')
def index():
    return redirect('/ui/')

if __name__ == '__main__':

    similarity_service_impl.app.serve_app()
