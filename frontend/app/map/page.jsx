"use client";

import dynamic from "next/dynamic";

const MapView = dynamic(() => import("../../components/MapView"), { ssr: false });

export default function MapPage() {
  return (
    <>
      <p className="muted">Активные объявления на карте (данные — только из нашей базы).</p>
      <div className="map-wrap">
        <MapView />
      </div>
    </>
  );
}
