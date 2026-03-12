const map = L.map("map").setView([35.67, 139.65], 8);

const osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

const layers = {};
let activeCollections = [];
const mapLayerUrls = {};

const hotSpringIcon = L.icon({
  iconUrl: "hot_spring.svg",
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -28],
});

fetch("http://localhost:5000/collections?f=json")
  .then((res) => res.json())
  .then((data) => {
    const featureContainer = document.getElementById("feature-layers");
    const mapContainer = document.getElementById("map-layers");

    data.collections.forEach((col) => {
      const id = col.id;
      const title = col.title || id;

      let isFeatureLayer = col.itemType === "feature";

      let mapLink = col.links?.find(
        (l) => l.rel === "http://www.opengis.net/def/rel/ogc/1.0/map",
      );

      let isMapLayer = !!mapLink;
      if (isMapLayer) {
        mapLayerUrls[id] = mapLink.href;
      }

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = id;

      const label = document.createElement("label");
      label.htmlFor = id;
      label.textContent = " " + title;

      const br = document.createElement("br");

      const container = isFeatureLayer
        ? featureContainer
        : isMapLayer
          ? mapContainer
          : null;

      if (!container) return;

      container.appendChild(checkbox);
      container.appendChild(label);
      container.appendChild(br);

      checkbox.addEventListener("change", function () {
        if (this.checked) {
          activeCollections.push(id);

          if (isFeatureLayer) {
            loadFeatureCollection(id);
          }

          if (isMapLayer) {
            console.log(mapLink.href);
            loadMapLayer(id, mapLink.href);
          }
        } else {
          activeCollections = activeCollections.filter((c) => c !== id);
          removeCollection(id);
        }
      });
    });
  });

function buildURL(collectionId) {
  let filterValue = document.getElementById("tokyo-filter").value;

  let url = `http://localhost:5000/collections/${collectionId}/items?f=json`;

  if (filterValue !== "all") {
    url += `&filter=is_part_of_tokyo=${filterValue}`;
  }

  return url;
}

function loadFeatureCollection(collectionId) {
  const url = buildURL(collectionId);

  fetch(url)
    .then((res) => res.json())
    .then((data) => {
      const layer = L.geoJSON(data, {
        pointToLayer: function (feature, latlng) {
          if (collectionId === "tokyo_hot_springs") {
            return L.marker(latlng, { icon: hotSpringIcon });
          }

          return L.marker(latlng);
        },

        style: function (feature) {
          if (
            feature.properties &&
            feature.properties.is_part_of_tokyo !== undefined
          ) {
            return {
              color: feature.properties.is_part_of_tokyo ? "red" : "blue",
              weight: 2,
              fillOpacity: 0.3,
            };
          }

          return {
            color: "#3388ff",
            weight: 2,
            fillOpacity: 0.3,
          };
        },

        onEachFeature: function (feature, layer) {
          let popup = Object.entries(feature.properties)
            .map(([k, v]) => `<b>${k}</b>: ${v}`)
            .join("<br>");

          layer.bindPopup(popup);
        },
      });

      layers[collectionId] = layer;
      layer.addTo(map);
    });
}

function loadMapLayer(collectionId, baseUrl) {
  if (layers[collectionId]) {
    map.removeLayer(layers[collectionId]);
  }

  const bounds = map.getBounds();
  const bbox = [
    bounds.getWest(),
    bounds.getSouth(),
    bounds.getEast(),
    bounds.getNorth(),
  ];

  const size = map.getSize();
  const url = `http://localhost:5000/collections/${collectionId}/map?bbox=${bbox.join(",")}&width=${size.x}&height=${size.y}&f=png`;

  const leafletBounds = [
    [bbox[1], bbox[0]],
    [bbox[3], bbox[2]],
  ];

  const overlay = L.imageOverlay(url, leafletBounds, {
    opacity: 1,
    interactive: false,
  });

  overlay.addTo(map);
  layers[collectionId] = overlay;
}

function removeCollection(collectionId) {
  if (layers[collectionId]) {
    map.removeLayer(layers[collectionId]);
  }
}

document.getElementById("apply-filter").addEventListener("click", () => {
  activeCollections.forEach((id) => {
    removeCollection(id);
    loadFeatureCollection(id);
  });
});

map.on("moveend", function () {
  activeCollections.forEach((id) => {
    // Only reload map layers, not feature layers
    const checkbox = document.getElementById(id);
    if (checkbox && checkbox.checked && layers[id] instanceof L.ImageOverlay) {
      const mapLink =
        /* you need access to mapLink here */
        loadMapLayer(id, null);
    }
  });
});
