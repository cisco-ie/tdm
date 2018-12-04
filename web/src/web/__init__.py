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
from flask import Flask
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
# Disabled JSON ordering, see views.search_deep_api
app.config.update(
	WTF_CSRF_ENABLED=True,
	WTF_CSRF_SECRET_KEY="abcd1234",
	SECRET_KEY="1234abcd",
	JSON_SORT_KEYS=False
)
from . import views

@app.before_first_request
def initialize():
	pass

@app.before_request
def validate_request():
	pass

@app.teardown_appcontext
def cleanup(exception=None):
	pass

logging.info('Application fully loaded and running.')
