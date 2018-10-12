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
