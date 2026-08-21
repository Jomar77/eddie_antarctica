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

"""Tests for the terria catalog served by the /terria-catalog.json backend endpoint."""
import os

import pytest

# The eddie library reads these when imported, so give them values in case the environment does not have them.
for _required_env_variable in ("STATSNZ_API_KEY", "LINZ_API_KEY", "MFE_API_KEY",
                               "DATA_DIR", "DATA_DIR_GEOSERVER", "POSTGRES_PASSWORD"):
    os.environ.setdefault(_required_env_variable, "unused-by-these-tests")

pytest.importorskip("eddie.geoserver.terria_catalogs", reason="The eddie library is not installed.")

from src.eddie_antartica import terria_catalog  # noqa: E402  # Imported after the environment is populated.


def _fake_workspace_group(workspace_name: str) -> dict:
    """Stand in for a geoserver-backed workspace group, without querying geoserver."""
    return {
        "type": "group",
        "name": workspace_name.replace("_", " ").title(),
        "members": [{"type": "wms", "name": f"{workspace_name}_layer"}],
        "isOpen": True,
    }


def test_catalog_has_single_intermediate_layer_group(monkeypatch: pytest.MonkeyPatch) -> None:
    """The catalog should be a single closed group holding one closed group per geoserver workspace."""
    monkeypatch.setattr(terria_catalog, "get_layers_as_terria_group", _fake_workspace_group)

    catalog = terria_catalog.get_terria_catalog()

    assert len(catalog["catalog"]) == 1
    intermediate_layer_group = catalog["catalog"][0]
    assert intermediate_layer_group["type"] == "group"
    assert intermediate_layer_group["name"] == "Intermediate Layer"
    assert intermediate_layer_group["isOpen"] is False
    assert [member["name"] for member in intermediate_layer_group["members"]] == [
        "Input Layers", "Extruded Layers", "Static Files"
    ]
    assert all(member["isOpen"] is False for member in intermediate_layer_group["members"])


def test_catalog_keeps_workspace_layers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nesting the workspace groups should not drop the layers fetched from geoserver."""
    monkeypatch.setattr(terria_catalog, "get_layers_as_terria_group", _fake_workspace_group)

    members = terria_catalog.get_terria_catalog()["catalog"][0]["members"]

    assert [member["members"][0]["name"] for member in members] == [
        "input_layers_layer", "extruded_layers_layer", "static_files_layer"
    ]
