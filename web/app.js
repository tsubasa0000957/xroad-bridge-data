const map = L.map("map");
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

function bindBridgePopup(feature, layer) {
    const popup = document.createElement("span");

    const bridgeName = feature.properties["橋梁名"] || "名称不明";
    const routeName = feature.properties["路線名"] || "路線名不明";

    popup.textContent = `${bridgeName} / ${routeName}`;

    layer.bindPopup(popup);
}

async function loadBridgeData() {
    const response = await fetch("../data/processed/processed.geojson");
    const geojson = await response.json();

    const bridgeLayer = L.geoJSON(geojson, {
        onEachFeature: bindBridgePopup,
    }).addTo(map);

    const bounds = bridgeLayer.getBounds();
    if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [10, 10] });
    }
}

loadBridgeData();
