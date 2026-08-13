"use client";

import { useEffect, useState } from "react";
import ListingCard from "../../components/ListingCard";
import { api } from "../../lib/api";

export default function FavoritesPage() {
  const [items, setItems] = useState(null);

  useEffect(() => {
    api("/api/favorites").then(setItems).catch(() => setItems([]));
  }, []);

  if (items === null) return <p className="muted">Загрузка…</p>;
  if (items.length === 0) return <p className="muted">В избранном пока пусто.</p>;
  return (
    <div className="grid">
      {items.map((l) => <ListingCard key={l.id} l={l} />)}
    </div>
  );
}
