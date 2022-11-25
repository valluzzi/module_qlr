# -------------------------------------------------------------------------------
# Licence:
# Copyright (c) 2012-2021 Luzzi Valerio
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#
# Name:        module_qlr.py
# Purpose:
#
# Author:      Luzzi Valerio
#
# Created:     10/12/2021
# -------------------------------------------------------------------------------
import os
import re
import pkg_resources
from datetime import datetime

import jenkspy
import matplotlib
import matplotlib.cm
import numpy as np
from osgeo import ogr
from .filesystem import juststem, justfname, forceext, justext
from gdal2numpy import GDAL2Numpy, GetMetaData, GetSpatialRef, GetExtent, GetMinMax


def GetGeomTypeName(filename):
    """
    GetType
    """
    ds = ogr.OpenShared(filename)
    if ds:
        layer = ds.GetLayer()
        type = layer.GetGeomType()
        ds = None
        return ogr.GeometryTypeToName(type)
    return None


def get_colors(cmapname, n_classes):
    """
    get_colors - get array of colors
    """
    cmap = matplotlib.cm.get_cmap(cmapname)
    if cmap:
        colors = cmap(np.linspace(0, 1, n_classes))
        colors = [matplotlib.colors.rgb2hex(c) for c in colors]
        return colors
    return []


def compute_depth_scale(filepath, n_classes=7, cmapname="viridis"):
    """
    compute_depth_scale - SubOptimal algo for Natural-Breaks classes
    """
    classes = []
    # if n_classes == 7:
    #    colors = ["#440154", "#3a528b", "#20908d", "#5dc962", "#fde725", "#ffa500", "#ff0000"]

    if os.path.isfile(filepath):
        data, _, _ = GDAL2Numpy(filepath)
        data[data < -1e10] = np.nan
        data = np.unique(data.ravel())  # ravel instead of flatten because flatten create a copy
        data = data[~np.isnan(data)]
        if data.size == 0:
            return [{"value": 0, "label": "nodata", "alpha": 255, "color": "#000000"}]

        while data.size > 400 and np.unique(data).size > n_classes:
            data = np.array([data[j] for j in range(0, data.size, 2)])

        # In case n_classes is too high it decreases the number
        values = []
        while n_classes > 2 and len(values) == 0:
            try:
                values = np.round(jenkspy.jenks_breaks(data, n_classes), decimals=1)
            except Exception as ex:
                print(ex)
                n_classes = n_classes - 1

        colors = get_colors(cmapname, n_classes)
        for value, color in zip(values[:-1], colors):
            classes.append({"value": value, "label": f'{value}', "alpha": 255, "color": color})

    return classes


def create_qlr(filename, fileqlr="", cmapname=None):
    """
    create_qlr - from template
    """

    if os.path.isfile(filename):
        filetpl = ""
        fileqlr = fileqlr if fileqlr else forceext(filename, "qlr")
        minValue, maxValue = GetMinMax(filename) if justext(filename) == "tif" else 0, 0

        srs = GetSpatialRef(filename)
        minx, miny, maxx, maxy = GetExtent(filename)
        items = ""
        customproperties = ""
        fill_color = "#ffffff"
        ext = justext(filename).lower()

        metadata = GetMetaData(filename)
        metadata = metadata if metadata else {}
        print(filename, metadata)
        print("================================")

        # Redefine sand, silt, clay cmap
        if ext == "tif":
            # assert that "type" is a valid key
            if "type" not in metadata:
                metadata["type"] = "viridis"

            cmapname = cmapname if cmapname else metadata["type"]

            filetpl = pkg_resources.resource_filename(__name__, "data/raster.qlr")
            if cmapname == "dtm":  # dtm
                metadata = {"um": "m", "type": "dtm"}
                classes = compute_depth_scale(filename, n_classes=8, cmapname="viridis")
            elif cmapname == "waterdepth":  # water_depth
                metadata = {"um": "m", "type": "waterdepth"}
                classes = [
                    {"color": "#431be9", "label": 0.0, "value": 0, "alpha": 255},
                    {"color": "#3254de", "label": 0.75, "value": 0.75, "alpha": 255},
                    {"color": "#218dd3", "label": 1.5, "value": 1.5, "alpha": 255},
                    {"color": "#10c6c8", "label": 2.25, "value": 2.25, "alpha": 255},
                    {"color": "#00ffbd", "label": 3.0, "value": 3.0, "alpha": 255},
                ]
            elif cmapname == "sand":  # sabbia
                metadata = {"um": "%", "type": "sand"}
                classes = compute_depth_scale(filename, n_classes=8, cmapname="copper")
            elif cmapname == "clay":  # argilla
                metadata = {"um": "%", "type": "clay"}
                classes = compute_depth_scale(filename, n_classes=8, cmapname="gist_heat")
            elif cmapname == "silt":  # limo
                metadata = {"um": "%", "type": "silt"}
                classes = compute_depth_scale(filename, n_classes=8, cmapname="bone")
            elif cmapname == "infiltration_rate":  # landuse
                metadata = {"type": "landuse"}
                classes = compute_depth_scale(filename, n_classes=8, cmapname="bone")
            else:
                # Generic GTiff
                cmapname = cmapname if cmapname else "viridis"
                metadata = GetMetaData(filename)
                metadata = metadata["metadata"] if "metadata" in metadata else {}
                classes = compute_depth_scale(filename, n_classes=8, cmapname=cmapname)
                """
                <item color="#431be9" label="0,0000" value="0" alpha="255"/>
                <item color="#3254de" label="0,7500" value="0.75" alpha="255"/>
                <item color="#218dd3" label="1,5000" value="1.5" alpha="255"/>
                <item color="#10c6c8" label="2,2500" value="2.25" alpha="255"/>
                <item color="#00ffbd" label="3,0000" value="3" alpha="255"/>
                """
            # for all tif
            for item in classes:
                items += f"""<item color="{item["color"]}" label="{item["label"]}" value="{item["value"]}" alpha="{item["alpha"]}"/>\n"""
        # Vector
        elif ext == "shp":

            # assert that "type" is a valid key
            if "type" not in metadata:
                metadata["type"] = "Polygon"

            cmapname = cmapname if cmapname else metadata["type"]
            geomtype = GetGeomTypeName(filename)
            filetpl = pkg_resources.resource_filename(__name__, f"data/{geomtype}.qlr")

            if cmapname == "infiltration_rate":
                filetpl = pkg_resources.resource_filename(__name__, f"data/{cmapname}.qlr")
            elif cmapname == "buildings":
                fill_color = "#888888"
            elif cmapname == "bluespots":
                fill_color = "#358ab8"
            elif cmapname == "watersheds":
                fill_color = "#cae1e9"
            elif cmapname == "streams":
                fill_color = "#127db9"
            elif cmapname == "barrier":
                filetpl = pkg_resources.resource_filename(__name__, f"data/{cmapname}.qlr")
                fill_color = "#127db9"
            elif cmapname == "storagetank":
                filetpl = pkg_resources.resource_filename(__name__, f"data/{cmapname}.qlr")
                fill_color = "#127db9"
        else:
            return None

        # Metadata in customproperties
        for key in metadata:
            customproperties += f"""\t\t<property key="{key}" value="{metadata[key]}"/>\n"""

        params = {
            "id": juststem(filename) + datetime.now().strftime("_%Y%m%d%H%M%S"),
            "layername": juststem(filename),
            "source": justfname(filename),
            "xmin": minx,
            "ymin": miny,
            "xmax": maxx,
            "ymax": maxy,
            "wkt": srs.ExportToWkt(),
            "proj4": srs.ExportToProj4(),
            "srsid": 0,
            "srid": srs.GetAuthorityCode(None),
            "authid": f"{srs.GetAuthorityName(None)}:{srs.GetAuthorityCode(None)}",
            "description": srs.GetName(),
            "projectionacronym": "utm",
            "ellipsoidacronym": "EPSG:7030",
            "geographicflag": "true" if srs.IsGeographic() else "false",
            "minValue": minValue,
            "maxValue": maxValue,
            "itemList": items,
            "customproperties": customproperties,
            "fill_color": fill_color
        }

        # read the template .qlr
        text = ""
        with open(filetpl, "r", encoding="utf-8") as stream:
            text = stream.read()

            for key in params:
                text = re.sub(r'\{\{' + key + '\}\}', f"{params[key]}", text)

            with open(fileqlr, 'w') as ostream:
                ostream.write(text)

        return fileqlr
    return None
