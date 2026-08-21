# Copyright © 2021-2026 Geospatial Research Institute Toi Hangarau
# LICENSE: https://github.com/GeospatialResearch/Digital-Twins/blob/master/LICENSE
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



"""" Basic UI test on Terria's Frontend"""
import json

import pytest
import pathlib



CATALOG_PATH = pathlib.Path(__file__).resolve().parent.parent /  "terriajs" / "catalog.json"


def test_catalog_check_home_coords() -> None:
    """terriajs/catalog.json should be pointing towards the Ross Sea bounding box."""
    # flags changes in the home coordinates

    catalog = json.loads(CATALOG_PATH.read_text())

    assert catalog["homeCamera"] == {
        "west": 151.04,
        "south": -78.60,
        "east": 172.98,
        "north": -76.45
    }


# The overlay in terriajs/catalog.json is merged onto the catalog served by /terria-catalog.json.
# Terria matches members by the path of names they sit at, so these names are merge keys: a typo or
# a display label written into "name" silently forks an empty duplicate instead of adding traits.
CATALOG_ROOT_GROUP_NAME = "Antarctic Data Layers"
WORKSPACE_GROUP_NAMES = ["Static Files", "Input Layers", "Extruded Layers"]
STATIC_LAYER_DIR = pathlib.Path(__file__).resolve().parent.parent / "src" / "static" / "geo"


def read_catalog() -> dict:
    """
    Parse terriajs/catalog.json.

    Returns
    -------
    dict
        The parsed contents of terriajs/catalog.json.
    """
    return json.loads(CATALOG_PATH.read_text())


def test_catalog_nests_workspace_groups_under_one_root() -> None:
    """Every workspace group should sit inside a single top-level group, not beside it."""
    catalog = read_catalog()

    assert len(catalog["catalog"]) == 1
    root_group = catalog["catalog"][0]
    assert root_group["name"] == CATALOG_ROOT_GROUP_NAME
    assert [group["name"] for group in root_group["members"]] == WORKSPACE_GROUP_NAMES


def test_catalog_group_names_have_no_stray_whitespace() -> None:
    """Group names are merge keys, so leading or trailing whitespace breaks the merge."""
    catalog = read_catalog()
    root_group = catalog["catalog"][0]

    for group in [root_group, *root_group["members"]]:
        assert group["name"] == group["name"].strip()


def test_static_file_item_names_match_geoserver_layers() -> None:
    """Static Files items should key off the geoserver layer names, with labels in nameInCatalog."""
    catalog = read_catalog()
    static_files_group = catalog["catalog"][0]["members"][0]
    assert static_files_group["name"] == "Static Files"

    expected_layer_names = sorted(path.stem for path in STATIC_LAYER_DIR.glob("*.sld"))
    assert sorted(item["name"] for item in static_files_group["members"]) == expected_layer_names
    for item in static_files_group["members"]:
        assert item["nameInCatalog"]
