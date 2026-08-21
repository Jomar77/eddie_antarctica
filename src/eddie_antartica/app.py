# -*- coding: utf-8 -*-
# Copyright © 2021-2026 Geospatial Research Institute Toi Hangarau
# LICENSE: https://github.com/GeospatialResearch/eddie_antartica/blob/master/LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The main web application that serves the Digital Twin to the web through a Rest API."""
from http.client import OK
import importlib
import logging

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from eddie.check_celery_alive import check_celery_alive
from eddie.digitaltwin.utils import setup_logging
from eddie.discover_plugins import discover_plugins
from eddie.geoserver import get_terria_catalog
from eddie.geoserver.terria_catalogs import Catalog, CatalogGroup
from src.eddie_antartica import blueprint as eddie_antartica_blueprint

setup_logging()

# Initialise flask server object
load_dotenv()
app = Flask(__name__)
CORS(app)

# Serve API documentation
SWAGGER_URL = "/swagger"
API_URL = "/static/api_documentation.yml"
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "EDDIE (Template)"}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

eddie_plugins = discover_plugins()
for name, module in eddie_plugins.items():
    importlib.import_module(f"{name}.blueprint")
    app.register_blueprint(module.blueprint.blueprint)

# Flood Resilience specific blueprint
app.register_blueprint(eddie_antartica_blueprint.blueprint)

# Name of the single top-level catalog group that every geoserver workspace group is nested under.
CATALOG_ROOT_GROUP_NAME = "Antarctic Data Layers"


@app.route('/')
def index() -> Response:
    """
    Ping this endpoint to check that the flask app is running.
    Supported methods: GET

    Returns
    -------
    Response
        The HTTP Response. Expect OK if health check is successful
    """
    return Response("""
    Backend is receiving requests.
    GET /health-check to check if celery workers active.
    GET /swagger to get API documentation.
    """, OK)


@app.route('/health-check')
@check_celery_alive
def health_check() -> Response:
    """
    Ping this endpoint to check that the server is up and running.
    Supported methods: GET

    Returns
    -------
    Response
        The HTTP Response. Expect OK if health check is successful
    """
    return Response("Healthy", OK)


def nest_workspace_groups(catalog: Catalog) -> Catalog:
    """
    Move every top-level workspace group of a terria catalog inside a single parent group.

    Terria merges init files by the path a member sits at, so naming an existing group under a new
    parent in terriajs/catalog.json forks an empty copy instead of moving the group the backend
    serves. Re-parenting therefore has to happen here, where the catalog is built. Display names and
    descriptions stay in terriajs/catalog.json, which can override those traits in place.

    Parameters
    ----------
    catalog : Catalog
        The terria catalog to re-parent, as returned by get_terria_catalog.

    Returns
    -------
    Catalog
        The same catalog with its workspace groups nested inside CATALOG_ROOT_GROUP_NAME.
    """
    root_group: CatalogGroup = {
        "type": "group",
        "name": CATALOG_ROOT_GROUP_NAME,
        "members": catalog["catalog"],
        "isOpen": True,
    }
    return {"catalog": [root_group]}


@app.route('/terria-catalog.json')
def terria_catalog() -> Response:
    """
    Return a terria catalog that includes entries for static files and input layers from geoserver.
    Supported methods: GET

    Returns
    -------
    Response
        The HTTP Response. Expect OK if health check is successful
    """
    catalog = get_terria_catalog()
    return make_response(jsonify(nest_workspace_groups(catalog)), OK)


# Development server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

# Production server
if __name__ != '__main__':
    # Set gunicorn loggers to work with flask
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
