from qgis.core import QgsRasterLayer
from qgis.core import *
from qgis.gui import QgsMapCanvas, QgsMapToolPan
from qgis.PyQt.QtWidgets import *
from shapely import wkt
from pathlib import Path
import subprocess
import json
import os

QGIS_PREFIX = r"C:\Program Files\QGIS 3.40.15\apps\qgis-ltr"

BASE_DIR = Path(__file__).resolve().parent
PYTHON312_EXE = r"C:\Users\Luka\AppData\Local\Programs\Python\Python312\python.exe"
TEMPLES_INPUT_GPKG = BASE_DIR / "temples.gpkg"
TEMPLES_FILTERED_GPKG = BASE_DIR / "temples_filtered.gpkg"
PREPARE_SCRIPT = BASE_DIR / "prepare_some_data.py"

KANTO_GPKG = BASE_DIR / "kanto_tmp.gpkg"
TOKYO_GPKG = BASE_DIR / "tokyo_tmp.gpkg"
DIFF_RASTER_TIF = BASE_DIR / "kanto_without_tokyo.tif"
RASTER_PREPARE_SCRIPT = BASE_DIR / "prepare_raster_data.py"

def run_fiona_filter(search_text):
    clean_env = os.environ.copy()

    clean_env.pop("PYTHONHOME", None)
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("QGIS_PREFIX_PATH", None)
    clean_env.pop("QT_PLUGIN_PATH", None)

    clean_env["PATH"] = (
        r"C:\Users\Luka\AppData\Local\Programs\Python\Python312;"
        r"C:\Users\Luka\AppData\Local\Programs\Python\Python312\Scripts;"
        + os.pathsep +
        clean_env.get("PATH", "")
    )

    result = subprocess.run(
        [
            r"C:\Users\Luka\AppData\Local\Programs\Python\Python312\python.exe",
            str(BASE_DIR / "prepare_some_data.py"),
            str(TEMPLES_INPUT_GPKG),
            str(TEMPLES_FILTERED_GPKG),
            search_text,
        ],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR),
        env=clean_env,
    )

    print("RETURN CODE:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "prepare_some_data.py failed")

    return json.loads(result.stdout)

def save_layer_to_gpkg(layer, path, layer_name):
    if path.exists():
        path.unlink()

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name

    error = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer,
        str(path),
        QgsCoordinateTransformContext(),
        options
    )

    if error[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"Failed to save {layer_name} to {path}: {error}")

def run_rasterio_diff():
    clean_env = os.environ.copy()

    clean_env.pop("PYTHONHOME", None)
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("QGIS_PREFIX_PATH", None)
    clean_env.pop("QT_PLUGIN_PATH", None)

    clean_env["PATH"] = (
        r"C:\Users\Luka\AppData\Local\Programs\Python\Python312;"
        r"C:\Users\Luka\AppData\Local\Programs\Python\Python312\Scripts;"
        + os.pathsep +
        clean_env.get("PATH", "")
    )

    result = subprocess.run(
        [
            PYTHON312_EXE,
            str(RASTER_PREPARE_SCRIPT),
            str(KANTO_GPKG),
            str(TOKYO_GPKG),
            str(DIFF_RASTER_TIF),
        ],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR),
        env=clean_env,
    )

    print("RASTER RETURN CODE:", result.returncode)
    print("RASTER STDOUT:", result.stdout)
    print("RASTER STDERR:", result.stderr)

    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "prepare_raster_data.py failed")

    return json.loads(result.stdout)

def load_tokyo_vector_layer():
    uri = QgsDataSourceUri()
    uri.setConnection("localhost", "5432", "postgres", "postgres", "postgres")
    uri.setDataSource("public", "greater_tokyo", "geom", "", "region_name")

    layer = QgsVectorLayer(uri.uri(False), "GreaterTokyo", "postgres")

    if not layer.isValid():
        print("Failed to load greater tokyo vector layer")
        return None

    return layer


def load_kanto_vector_layer():
    uri = QgsDataSourceUri()
    uri.setConnection("localhost", "5432", "postgres", "postgres", "postgres")
    uri.setDataSource("public", "kanto_region", "geom", "", "region_name")

    layer = QgsVectorLayer(uri.uri(False), "AllKanto", "postgres")

    if not layer.isValid():
        print("Failed to load kanto vector layer")
        return None

    return layer


def diff_layers(layer1, layer2):
    feat1 = next(layer1.getFeatures())
    feat2 = next(layer2.getFeatures())

    geom1 = wkt.loads(feat1.geometry().asWkt())
    geom2 = wkt.loads(feat2.geometry().asWkt())

    diff_geom = geom1.difference(geom2)

    result_layer = QgsVectorLayer(
        f"MultiPolygon?crs={layer1.crs().authid()}",
        "KantoWithoutTokyo",
        "memory"
    )

    provider = result_layer.dataProvider()

    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromWkt(diff_geom.wkt))
    provider.addFeature(feature)

    result_layer.updateExtents()
    return result_layer

def japan_extent_3857():
    wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    webmerc = QgsCoordinateReferenceSystem("EPSG:3857")
    extent_wgs84 = QgsRectangle(122.0, 20.0, 154.0, 46.0)
    transform = QgsCoordinateTransform(wgs84, webmerc, QgsProject.instance())
    return transform.transformBoundingBox(extent_wgs84)

def enable_labels(layer, field_name):
    if layer is None:
        return

    settings = QgsPalLayerSettings()
    settings.enabled = True
    settings.fieldName = field_name

    geom_type = QgsWkbTypes.geometryType(layer.wkbType())
    if geom_type == Qgis.GeometryType.Line:
        settings.placement = Qgis.LabelPlacement.Line
    elif geom_type == Qgis.GeometryType.Polygon:
        settings.placement = Qgis.LabelPlacement.OverPoint
    else:
        settings.placement = Qgis.LabelPlacement.OverPoint

    text_format = QgsTextFormat()
    text_format.setSize(10)

    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(1)
    text_format.setBuffer(buffer)

    settings.setFormat(text_format)

    layer.setLabelsEnabled(True)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.triggerRepaint()


def load_long_tokyo_rivers_layer():
    uri = QgsDataSourceUri()
    uri.setConnection("localhost", "5432", "postgres", "postgres", "postgres")
    uri.setDataSource("public", "long_tokyo_rivers", "geom", "", "name")

    layer = QgsVectorLayer(uri.uri(False), "Long Tokyo Rivers", "postgres")

    if not layer.isValid():
        print("Failed to load long tokyo rivers layer")
        return None

    symbol = layer.renderer().symbol()
    symbol.setWidth(2)

    layer.triggerRepaint()

    return layer


def reproject_layer_to_3857(layer):
    source_crs = layer.crs()
    target_crs = QgsCoordinateReferenceSystem("EPSG:3857")
    transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())

    geometry_type = QgsWkbTypes.displayString(layer.wkbType())
    result_layer = QgsVectorLayer(
        f"{geometry_type}?crs=EPSG:3857",
        f"{layer.name()}_3857",
        "memory"
    )

    provider = result_layer.dataProvider()
    provider.addAttributes(layer.fields())
    result_layer.updateFields()

    new_features = []

    for feat in layer.getFeatures():
        new_feat = QgsFeature(result_layer.fields())
        new_feat.setAttributes(feat.attributes())

        geom = QgsGeometry(feat.geometry())
        geom.transform(transform)
        new_feat.setGeometry(geom)

        new_features.append(new_feat)

    provider.addFeatures(new_features)
    result_layer.updateExtents()

    return result_layer

def load_temples_filtered_layer():
    layer = QgsVectorLayer(str(TEMPLES_FILTERED_GPKG), "FilteredTemples", "ogr")

    if not layer.isValid():
        print("Failed to load FilteredTemples")
        return None

    print([field.name() for field in layer.fields()])  

    return layer

def load_diff_raster_layer():
    layer = QgsRasterLayer(str(DIFF_RASTER_TIF), "KantoWithoutTokyoRaster")
    if not layer.isValid():
        print("Failed to load KantoWithoutTokyoRaster")
        return None
    return layer  

def load_osm_base_layer():
    url = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    layer = QgsRasterLayer(url, "OpenStreetMap", "wms")

    if not layer.isValid():
        print("Failed to load OSM base layer")
        return None

    return layer      

def load_layers():
    layers = []
    filtering_layers = []

    temples_layer = load_temples_filtered_layer()
    if temples_layer is not None:
        temples_3857 = reproject_layer_to_3857(temples_layer)
        enable_labels(temples_3857, "religion")
        filtering_layers.append(temples_3857)

    long_tokyo_rivers_layer = load_long_tokyo_rivers_layer()
    if long_tokyo_rivers_layer is not None:
        rivers_3857 = reproject_layer_to_3857(long_tokyo_rivers_layer)
        enable_labels(rivers_3857, "name")
        filtering_layers.append(rivers_3857)

    tokyo_layer = load_tokyo_vector_layer()
    if tokyo_layer is not None:
        layers.append(tokyo_layer)

    kanto_layer = load_kanto_vector_layer()
    if kanto_layer is not None:
        layers.append(kanto_layer)

    if kanto_layer is not None and tokyo_layer is not None:
        diff_layer = diff_layers(kanto_layer, tokyo_layer)
        if diff_layer is not None:
            layers.append(diff_layer)

        try:
            save_layer_to_gpkg(kanto_layer, KANTO_GPKG, "kanto_layer")
            save_layer_to_gpkg(tokyo_layer, TOKYO_GPKG, "tokyo_layer")

            raster_info = run_rasterio_diff()
            print("Raster worker result:", raster_info)

            raster_layer = load_diff_raster_layer()
            if raster_layer is not None:
                renderer = raster_layer.renderer()

                if renderer:
                    renderer.setOpacity(0.6)
                raster_layer.triggerRepaint()

                layers.append(raster_layer)

        except Exception as e:
            print("Rasterio worker failed:", e)

    osm_base_layer = load_osm_base_layer()
    if osm_base_layer is not None:
        layers.append(osm_base_layer)

    return layers, filtering_layers


class MainWindow(QMainWindow):
    def __init__(self, layers, filtering_layers):
        super().__init__()

        self.setWindowTitle("PyQGIS Viewer")
        self.resize(1200, 800)

        self.all_layers = layers
        self.all_filtering_layers = filtering_layers
        self.visible_layers = list(layers)
        self.visible_filtering_layers = list(filtering_layers)

        self.layer_checkboxes = {}
        self.filtering_layer_checkboxes = {}

        self.temples_filtered_layer = self.all_filtering_layers[0] if self.all_filtering_layers else None
        self.river_layer = self.all_filtering_layers[1] if len(self.all_filtering_layers) > 1 else None

        for layer in self.all_layers:
            QgsProject.instance().addMapLayer(layer)

        for layer in self.all_filtering_layers:
            QgsProject.instance().addMapLayer(layer)

        self.canvas = QgsMapCanvas()
        self.canvas.setLayers(self.visible_filtering_layers + self.visible_layers)
        self.canvas.setExtent(japan_extent_3857())

        self.pan_tool = QgsMapToolPan(self.canvas)
        self.canvas.setMapTool(self.pan_tool)

        self.build_ui()

    def build_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.canvas)
        left_panel.setLayout(left_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout()

        layers_group = QGroupBox("Base Layers")
        layers_layout = QVBoxLayout()

        for layer in self.all_layers:
            checkbox = QCheckBox(layer.name())
            checkbox.setChecked(True)
            checkbox.toggled.connect(self.update_visible_layers)
            self.layer_checkboxes[layer.id()] = (checkbox, layer)
            layers_layout.addWidget(checkbox)

        layers_group.setLayout(layers_layout)

        other_group = QGroupBox("Filtering Layers")
        other_group_layout = QVBoxLayout()

        for layer in self.all_filtering_layers:
            checkbox = QCheckBox(layer.name())
            checkbox.setChecked(True)
            checkbox.toggled.connect(self.update_visible_layers)
            self.filtering_layer_checkboxes[layer.id()] = (checkbox, layer)
            other_group_layout.addWidget(checkbox)

        other_group_layout.addWidget(QLabel("River name:"))
        self.river_name_input = QLineEdit()
        self.river_name_input.textChanged.connect(self.apply_river_name_filter)
        other_group_layout.addWidget(self.river_name_input)

        other_group_layout.addWidget(QLabel("Min length:"))
        self.river_min_length_input = QLineEdit()
        self.river_min_length_input.textChanged.connect(self.apply_river_min_length_filter)
        other_group_layout.addWidget(self.river_min_length_input)

        other_group_layout.addWidget(QLabel("Temple name contains:"))
        self.temple_name_input = QLineEdit()
        other_group_layout.addWidget(self.temple_name_input)

        run_fiona_btn = QPushButton("Run Fiona Filter")
        run_fiona_btn.clicked.connect(self.run_fiona_filter_and_load)
        other_group_layout.addWidget(run_fiona_btn)

        other_group.setLayout(other_group_layout)

        right_layout.addWidget(layers_group)
        right_layout.addWidget(other_group)
        right_layout.addStretch()

        right_panel.setLayout(right_layout)
        right_panel.setMaximumWidth(280)

        main_layout.addWidget(left_panel, 4)
        main_layout.addWidget(right_panel, 1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_visible_layers(self):
        self.visible_layers = []
        self.visible_filtering_layers = []

        for checkbox, layer in self.layer_checkboxes.values():
            if checkbox.isChecked():
                self.visible_layers.append(layer)

        for checkbox, layer in self.filtering_layer_checkboxes.values():
            if checkbox.isChecked():
                self.visible_filtering_layers.append(layer)

        self.canvas.setLayers(self.visible_filtering_layers + self.visible_layers)
        self.canvas.setExtent(japan_extent_3857())
        self.canvas.refresh()

    def apply_river_name_filter(self):
        if self.river_layer is None:
            return

        name_value = self.river_name_input.text().strip()

        if not name_value:
            self.river_layer.setSubsetString("")
        else:
            safe_name = name_value.replace("'", "''")
            self.river_layer.setSubsetString(f"\"name\" ILIKE '%{safe_name}%'")

        self.river_layer.triggerRepaint()
        self.canvas.refresh()

    def apply_river_min_length_filter(self):
        if self.river_layer is None:
            return

        min_length_text = self.river_min_length_input.text().strip()

        if not min_length_text:
            self.river_layer.setSubsetString("")
            self.river_layer.triggerRepaint()
            self.canvas.refresh()
            return

        try:
            min_length = float(min_length_text)
        except ValueError:
            return

        matching_ids = []

        for feat in self.river_layer.getFeatures():
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue

            shapely_geom = wkt.loads(geom.asWkt())
            river_length = shapely_geom.length

            if river_length >= min_length:
                matching_ids.append(str(feat["id"]))

        if matching_ids:
            subset = f"\"id\" IN ({','.join(matching_ids)})"
        else:
            subset = "\"id\" IN (-1)"

        self.river_layer.setSubsetString(subset)
        self.river_layer.triggerRepaint()
        self.canvas.refresh()

    def run_fiona_filter_and_load(self):
        search_text = self.temple_name_input.text().strip()

        if self.temples_filtered_layer is not None:
            if self.temples_filtered_layer in self.visible_filtering_layers:
                self.visible_filtering_layers.remove(self.temples_filtered_layer)

            QgsProject.instance().removeMapLayer(self.temples_filtered_layer.id())
            self.temples_filtered_layer = None

        self.canvas.setLayers(self.visible_filtering_layers + self.visible_layers)
        self.canvas.refresh()

        try:
            info = run_fiona_filter(search_text)
            print("Fiona worker result:", info)
        except Exception as e:
            QMessageBox.critical(self, "Fiona filter error", str(e))
            return

        new_layer = reproject_layer_to_3857(load_temples_filtered_layer())
        if new_layer is None:
            QMessageBox.critical(self, "Load error", "Filtered temples layer could not be loaded")
            return
        enable_labels(new_layer, "religion")

        self.temples_filtered_layer = new_layer
        QgsProject.instance().addMapLayer(self.temples_filtered_layer)

        self.visible_filtering_layers.append(self.temples_filtered_layer)

        self.canvas.setLayers(self.visible_filtering_layers + self.visible_layers)

        self.canvas.refreshAllLayers()
        self.canvas.refresh()     

def main():
    QgsApplication.setPrefixPath(QGIS_PREFIX, True)

    qgs = QgsApplication([], True)
    qgs.initQgis()

    layers, filtering_layers = load_layers()

    window = MainWindow(layers, filtering_layers)
    window.show()

    qgs.exec()
    qgs.exitQgis()


if __name__ == "__main__":
    main()