const map = L.map("map").setView([35.67, 139.65], 8);

const osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

const kantoWMS = L.tileLayer(
  "http://localhost:5000/collections/kanto_prefectures/map?f=png&width=256&height=256&bbox={bbox}",
  {
    attribution: "Rendered by MapScript",
  },
);

const layers = {};

let activeCollections = [];

const hotSpringIcon = L.icon({
  iconUrl: "hot_spring.svg",
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -28],
});

fetch("http://localhost:5000/collections?f=json")
  .then((res) => res.json())
  .then((data) => {
    const container = document.getElementById("collections-list");

    data.collections.forEach((col) => {
      const id = col.id;
      const title = col.title || col.id;

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = id;

      const label = document.createElement("label");
      label.htmlFor = id;
      label.textContent = " " + title;

      const br = document.createElement("br");

      container.appendChild(checkbox);
      container.appendChild(label);
      container.appendChild(br);

      checkbox.addEventListener("change", function () {
        if (this.checked) {
          activeCollections.push(id);
          loadCollection(id);
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

function loadCollection(collectionId) {
  const url = buildURL(collectionId);

  fetch(url)
    .then((res) => res.json())
    .then((data) => {
      const layer = L.geoJSON(data, {
        // POINT FEATURES (your hot springs)
        pointToLayer: function (feature, latlng) {
          if (collectionId === "tokyo_hot_springs") {
            return L.marker(latlng, { icon: hotSpringIcon });
          }

          return L.marker(latlng);
        },

        // POLYGONS (your prefectures)
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

function removeCollection(collectionId) {
  if (layers[collectionId]) {
    map.removeLayer(layers[collectionId]);
  }
}

// CQL filter button
document.getElementById("apply-filter").addEventListener("click", () => {
  activeCollections.forEach((id) => {
    removeCollection(id);
    loadCollection(id);
  });
});
