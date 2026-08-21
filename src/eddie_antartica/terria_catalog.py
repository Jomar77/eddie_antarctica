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

"""
Builds the TerriaJS catalog served by the /terria-catalog.json endpoint of this EDDIE instance.

The eddie library returns one top-level catalog group per geoserver workspace.
This module nests those workspace groups inside a single "Intermediate Layer" group so the
front-end catalog reads as one collapsed tree instead of several top-level groups.
"""
from eddie.geoserver.terria_catalogs import Catalog, CatalogGroup, Workspaces, get_layers_as_terria_group

# Name of the single top-level group that all geoserver workspace groups are nested inside.
INTERMEDIATE_LAYER_GROUP_NAME = "Intermediate Layer"

# The geoserver workspaces to serve, in the order they are displayed within the intermediate layer group.
NESTED_WORKSPACES = (
    Workspaces.INPUT_LAYERS_WORKSPACE,
    Workspaces.EXTRUDED_LAYERS_WORKSPACE,
    Workspaces.STATIC_FILES_WORKSPACE,
)


def nest_workspace_groups(workspace_groups: list[CatalogGroup]) -> CatalogGroup:
    """
    Nest geoserver workspace catalog groups inside one collapsed "Intermediate Layer" group.

    Parameters
    ----------
    workspace_groups : list[CatalogGroup]
        The Terria catalog groups, one per geoserver workspace, to nest.

    Returns
    -------
    CatalogGroup
        The Terria catalog group holding each workspace group as a collapsed member.
    """
    members = [{**workspace_group, "isOpen": False} for workspace_group in workspace_groups]
    return {
        "type": "group",
        "name": INTERMEDIATE_LAYER_GROUP_NAME,
        "isOpen": False,
        "members": members,
    }


def get_terria_catalog() -> Catalog:
    """
    Query geoserver for the available layers and return them as a Terria catalog for the front-end to read.

    Returns
    -------
    Catalog
        Represents the Terria JSON catalog, with each workspace group nested inside the intermediate layer group.

    Raises
    ------
    HTTPError
        If geoserver responds with anything but OK or NOT_FOUND, raises it as an exception since it is unexpected.
    """
    workspace_groups = [get_layers_as_terria_group(workspace) for workspace in NESTED_WORKSPACES]
    return {"catalog": [nest_workspace_groups(workspace_groups)]}
