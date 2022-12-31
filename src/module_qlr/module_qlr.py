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
from .filesystem import juststem, justfname, forceext, justext, israster, isshape
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


def compute_depth_scale(filename, n_classes=7, cmapname="viridis"):
    """
    compute_depth_scale - SubOptimal algo for Natural-Breaks classes
    """
    classes = []
    # if n_classes == 7:
    #    colors = ["#440154", "#3a528b", "#20908d", "#5dc962", "#fde725", "#ffa500", "#ff0000"]

    if os.path.isfile(filename):
        data, _, _ = GDAL2Numpy(filename)
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

def EqualIntervals(minValue, maxValue, n_classes):
    """
    EqualIntervals
    """
    return np.linspace(minValue, maxValue, n_classes+1)
    #for j in range(n_classes):
    #    lower, upper = classes[j], classes[j+1]
    #    ranges.append(f"""<range symbol="{j}" label="{lower} - {upper}" lower="{lower}" upper="{upper}" render="true"/>""")


def SimpleFillSymbol(color="#ffffff", outline_color="#000000"):
    return f"""<symbol name="0" force_rhr="0" alpha="1" type="fill" clip_to_extent="1">
        <layer locked="0" pass="0" class="SimpleFill" enabled="1">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="{color}"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="{outline_color}"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
        </layer>
      </symbol>"""

def compute_graduate_scale(minValue, maxValue, n_classes=7, cmapname="viridis"):
    """
    compute_graduate_scale for ESRI_ShapeFile <ranges...>/
    """

    """
    <ranges>
      <range symbol="0" label="0 - 20" lower="0.000000000000000" upper="20.000000000000000" render="true"/>
      <range symbol="1" label="20 - 40" lower="20.000000000000000" upper="40.000000000000000" render="true"/>
      <range symbol="2" label="40 - 60" lower="40.000000000000000" upper="60.000000000000000" render="true"/>
      <range symbol="3" label="60 - 80" lower="60.000000000000000" upper="80.000000000000000" render="true"/>
      <range symbol="4" label="80 - 100" lower="80.000000000000000" upper="100.000000000000000" render="true"/>
    </ranges>
    
    <symbols>
      <symbol name="0" force_rhr="0" alpha="1" type="fill" clip_to_extent="1">
        <layer locked="0" pass="0" class="SimpleFill" enabled="1">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="255,255,255,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
        </layer>
      </symbol>
      ...
    </symbols>
    """
    colors = get_colors(cmapname, n_classes)
    symbols = [SimpleFillSymbol(color) for color in colors]
    classes = EqualIntervals(minValue, maxValue, n_classes)
    ranges = [f"""<range symbol="{j}" label="{classes[j]} - {classes[j+1]}" lower="{classes[j]}" upper="{classes[j+1]}" render="true"/>""" for j in range(classes-1)]
    ranges = "\n\t".join(ranges)
    symbols = "\n\t".join(symbols)
    return f"""<ranges>\n\t{ranges}</ranges>\n<symbols>{symbols}</symbols>\n"""


def create_qlr(filename, fileqlr="", cmapname=None, fieldname=""):
    """
    create_qlr - from template
    """

    if os.path.isfile(filename):
        filetpl = ""
        fileqlr = fileqlr if fileqlr else forceext(filename, "qlr")
        minValue, maxValue = GetMinMax(filename, fieldname)

        srs = GetSpatialRef(filename)
        minx, miny, maxx, maxy = GetExtent(filename)
        items, symbols, customproperties = "", "", ""
        fill_color = "#ffffff"

        metadata = GetMetaData(filename)
        metadata = metadata["metadata"] if metadata and "metadata" in metadata else {}

        # Redefine sand, silt, clay cmap
        if israster(filename):
            # assert that "type" is a valid key
            if "type" not in metadata:
                metadata["type"] = "viridis"
            cmapname = cmapname if cmapname else metadata["type"]
            fieldname = cmapname

            filetpl = pkg_resources.resource_filename(__name__, "data/raster.qlr")
            if cmapname == "dtm":  # dtm
                metadata.update({"um": "m", "type": "dtm"})
                classes = compute_depth_scale(filename, n_classes=8, cmapname="viridis")
            elif cmapname == "waterdepth":  # water_depth
                metadata.update({"um": "m", "type": "waterdepth"})
                classes = [
                    {"color": "#431be9", "label": 0.0, "value": 0, "alpha": 255},
                    {"color": "#3254de", "label": 0.75, "value": 0.75, "alpha": 255},
                    {"color": "#218dd3", "label": 1.5, "value": 1.5, "alpha": 255},
                    {"color": "#10c6c8", "label": 2.25, "value": 2.25, "alpha": 255},
                    {"color": "#00ffbd", "label": 3.0, "value": 3.0, "alpha": 255},
                ]
            elif cmapname == "sand":  # sabbia
                metadata.update({"um": "%", "type": "sand"})
                classes = compute_depth_scale(filename, n_classes=8, cmapname="copper")
            elif cmapname == "clay":  # argilla
                metadata.update({"um": "%", "type": "clay"})
                classes = compute_depth_scale(filename, n_classes=8, cmapname="gist_heat")
            elif cmapname == "silt":  # limo
                metadata.update({"um": "%", "type": "silt"})
                classes = compute_depth_scale(filename, n_classes=8, cmapname="bone")
            elif cmapname == "infiltration_rate":  # landuse
                metadata.update({"type": "landuse"})
                classes = compute_depth_scale(filename, n_classes=8, cmapname="bone")
            elif cmapname in ("rain", "rainfall"):  # rain
                metadata.update({"um": "mm", "type": "rain"})
                classes = [
                    {"color": "#c2fbfa", "label": 0.25, "value": 0.25, "alpha": 255},
                    {"color": "#9df9f6", "label": 1.0, "value": 1.0, "alpha": 255},
                    {"color": "#87a9fd", "label": 2.0, "value": 2.0, "alpha": 255},
                    {"color": "#7b95f9", "label": 4.0, "value": 4.0, "alpha": 255},
                    {"color": "#3496fe", "label": 6.0, "value": 6.0, "alpha": 255},
                    {"color": "#3586dd", "label": 10.0, "value": 10.0, "alpha": 255},
                    {"color": "#35ac9f", "label": 15.0, "value": 15.0, "alpha": 255},
                    {"color": "#35d14d", "label": 20.0, "value": 20.0, "alpha": 255},
                    {"color": "#beff35", "label": 30.0, "value": 30.0, "alpha": 255},
                    {"color": "#e1ff5d", "label": 50.0, "value": 50.0, "alpha": 255},
                    {"color": "#ffbd35", "label": 70.0, "value": 70.0, "alpha": 255},
                    {"color": "#ff8134", "label": 100.0, "value": 100.0, "alpha": 255},
                    {"color": "#fd6335", "label": 150.0, "value": 150.0, "alpha": 255},
                    {"color": "#fc4335", "label": 200.0, "value": 200.0, "alpha": 255},
                ]
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
        #---------------------------------------------------------------------------------------------------------------
        # Vector
        # ---------------------------------------------------------------------------------------------------------------
        elif isshape(filename):
            # assert that "type" is a valid key
            if "type" not in metadata:
                metadata["type"] = cmapname
            cmapname = cmapname if cmapname else metadata["type"]
            fieldname = fieldname if fieldname else cmapname

            geomtype = GetGeomTypeName(filename)
            filetpl = pkg_resources.resource_filename(__name__, f"data/{geomtype}.qlr")

            if cmapname == "infiltration_rate":
                metadata.update({"um": ""})
                symbols = compute_graduate_scale(0, 1.0, n_classes=8, cmapname="greens")
                filetpl = pkg_resources.resource_filename(__name__, f"data/PolygonGraduate.qlr")
                #filetpl = pkg_resources.resource_filename(__name__, f"data/infiltration_rate.qlr")
                #fieldname = "PERM"
            elif cmapname == "sand":
                metadata.update({"um": "%"})
                symbols = compute_graduate_scale(0, 100, n_classes=8, cmapname="copper")
                filetpl = pkg_resources.resource_filename(__name__, f"data/PolygonGraduate.qlr")
            elif cmapname == "clay":
                metadata.update({"um": "%"})
                symbols = compute_graduate_scale(0, 100, n_classes=8, cmapname="copper")
                filetpl = pkg_resources.resource_filename(__name__, f"data/PolygonGraduate.qlr")
            elif cmapname == "buildings":
                fill_color = "#888888"
            elif cmapname == "bluespots":
                metadata.update({"um": "m³"})
                fill_color = "#358ab8"
            elif cmapname == "watersheds":
                metadata.update({"um": "m³"})
                fill_color = "#cae1e9"
            elif cmapname == "streams":
                metadata.update({"um": "m³"})
                fill_color = "#127db9"
            elif cmapname == "barrier":
                metadata.update({"um": "m"})
                filetpl = pkg_resources.resource_filename(__name__, f"data/{cmapname}.qlr")
                fill_color = "#127db9"
                fieldname = "height"
            elif cmapname == "storagetank":
                metadata.update({"um": "m³"})
                filetpl = pkg_resources.resource_filename(__name__, f"data/{cmapname}.qlr")
                fill_color = "#127db9"
                #fieldname = "v"
            elif cmapname == "riverevent":
                metadata.update({"um": "m³"})
                filetpl = pkg_resources.resource_filename(__name__, f"data/{cmapname}.qlr")
                fill_color = "#ff7db9"
                #fieldname = "v"
            elif cmapname in ("rain", "rainfall"):
                metadata.update({"um": "mm"})
                filetpl = pkg_resources.resource_filename(__name__, f"data/rainfall.qlr")
                fill_color = "#0000ff"
                fieldname = "rain"  #graduate field attribute
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
            "symbols": symbols,
            "customproperties": customproperties,
            "fill_color": fill_color,
            "fieldname": fieldname
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
