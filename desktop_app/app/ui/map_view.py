from PyQt5.QtWebEngineWidgets import QWebEngineView

_MAP_HTML = """<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>body, html, #map { height: 100%; margin: 0; padding: 0; background: #121212; }</style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map', {zoomControl: false}).setView([47.150476, 27.636506], 16);

        var layers = {
            'Default Layout': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'),
            'Satelit Layout': L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                                           {maxZoom: 20, subdomains: ['mt0','mt1','mt2','mt3']}),
            'Terrain Layout': L.tileLayer('http://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
                                           {maxZoom: 20, subdomains: ['mt0','mt1','mt2','mt3']})
        };

        var currentLayer = layers['Default Layout'];
        currentLayer.addTo(map);

        var flightPath  = L.polyline([], {color: '#00E676', weight: 4}).addTo(map);
        var droneMarker = L.circleMarker([0, 0],
            {color: '#FF1744', fillColor: '#FF1744', fillOpacity: 1, radius: 6});

        function updateDronePosition(lat, lon) {
            var ll = [lat, lon];
            flightPath.addLatLng(ll);
            if (!map.hasLayer(droneMarker)) droneMarker.addTo(map);
            droneMarker.setLatLng(ll);
            map.setView(ll, map.getZoom(), {animate: false});
        }

        function drawFullPath(points) {
            flightPath.setLatLngs(points);
            if (points.length === 0) return;
            var last = points[points.length - 1];
            if (!map.hasLayer(droneMarker)) droneMarker.addTo(map);
            droneMarker.setLatLng(last);
            map.setView(last, map.getZoom(), {animate: false});
        }

        function resetPath() {
            flightPath.setLatLngs([]);
            if (map.hasLayer(droneMarker)) map.removeLayer(droneMarker);
        }

        function setMapStyle(name) {
            map.removeLayer(currentLayer);
            currentLayer = layers[name] || layers['Default Layout'];
            currentLayer.addTo(map);
        }
    </script>
</body>
</html>"""


class MapView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHtml(_MAP_HTML)
        self._counter = 0

    def update_position(self, lat: float, lon: float):
        self._counter += 1
        if self._counter % 6 == 0:
            self.page().runJavaScript(f"updateDronePosition({lat}, {lon});")

    def draw_path(self, points: list):
        js_points = str([[lat, lon] for lat, lon in points])
        self.page().runJavaScript(f"drawFullPath({js_points});")

    def reset_path(self):
        self._counter = 0
        self.page().runJavaScript("resetPath();")

    def set_style(self, style_name: str):
        self.page().runJavaScript(f"setMapStyle('{style_name}');")
