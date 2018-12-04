#!/usr/bin/env python
"""
Copyright 2018 Cisco Systems

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
from gevent.pywsgi import WSGIServer
from web import app

def start_prod():
    http_server = WSGIServer(('', 80), app)
    http_server.serve_forever()

def start_dev():
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)

if __name__ == '__main__':
    if 'FLASK_ENV' not in os.environ:
        start_prod()
    elif os.environ['FLASK_ENV'] == 'development':
        start_dev()
    else:
        start_prod()
