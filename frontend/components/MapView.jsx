"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import { api, fmtPrice } from "../lib/api";

// Центр MVP-географии: Аланья.
const CENTER = [36.52, 32.05];

export default function MapView() {
  const ref = useRef(null);
  const mapRef = useRef(null);

  useEffect(() => {
    if (mapRef.current) return;
    const map = L.map(ref.current).setView(CENTER, 12);
    mapRef.current = map;
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    api("/api/map")
      .then((points) => {
        for (const p of points) {
          L.circleMarker([p.latitude, p.longitude], {
            radius: 8, color: "#0e7490", fillColor: "#0e7490", fillOpacity: 0.85,
          })
            .addTo(map)
            .bindPopup(
              `<a href="/listing/${p.id}"><b>${fmtPrice(p.price, p.currency)}</b>${
                p.rooms ? ` · ${p.rooms}` : ""
              }</a>`
            );
        }
      })
      .catch(() => {});

    return () => { map.remove(); mapRef.current = null; };
  }, []);

  return <div ref={ref} style={{ height: "100%", width: "100%" }} />;
}
