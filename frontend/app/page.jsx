"use client";

import { useCallback, useEffect, useState } from "react";
import ListingCard from "../components/ListingCard";
import { api } from "../lib/api";

const ROOMS = ["1+0", "1+1", "2+1", "3+1", "4+1"];

export default function SearchPage() {
  const [locations, setLocations] = useState([]);
  const [filters, setFilters] = useState({
    transaction_type: "sale",
    property_type: "",
    district: "",
    neighbourhood: "",
    rooms: "",
    min_price: "",
    max_price: "",
    min_m2: "",
    max_m2: "",
    furnished: false,
    pool: false,
    parking: false,
    balcony: false,
    only_price_drops: false,
    sort: "newest",
  });
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api("/api/locations").then(setLocations).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    const params = new URLSearchParams({ page: String(page), per_page: "20" });
    for (const [k, v] of Object.entries(filters)) {
      if (v === "" || v === false) continue;
      params.append(k, String(v));
    }
    try {
      setData(await api(`/api/listings?${params}`));
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  }, [filters, page]);

  useEffect(() => { load(); }, [load]);

  const set = (k) => (e) =>
    setFilters((f) => ({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  const country = locations[0];
  const districts = (country?.children || []).flatMap((p) => p.children || []);
  const hoods = districts.flatMap((d) => (d.children || []).map((n) => ({ ...n, district: d.slug })));

  return (
    <>
      <div className="filters">
        <div>
          <label>Сделка</label>
          <select value={filters.transaction_type} onChange={set("transaction_type")}>
            <option value="">любая</option>
            <option value="sale">покупка</option>
            <option value="rent_long">аренда</option>
            <option value="rent_short">краткосрочная</option>
          </select>
        </div>
        <div>
          <label>Тип</label>
          <select value={filters.property_type} onChange={set("property_type")}>
            <option value="">любой</option>
            <option value="apartment">квартира</option>
            <option value="house">дом</option>
            <option value="villa">вилла</option>
            <option value="commercial">коммерческая</option>
          </select>
        </div>
        <div>
          <label>Район</label>
          <select value={filters.district} onChange={set("district")}>
            <option value="">все</option>
            {districts.map((d) => <option key={d.slug} value={d.slug}>{d.name}</option>)}
          </select>
        </div>
        <div>
          <label>Микрорайон</label>
          <select value={filters.neighbourhood} onChange={set("neighbourhood")}>
            <option value="">все</option>
            {hoods
              .filter((n) => !filters.district || n.district === filters.district)
              .map((n) => <option key={n.slug} value={n.slug}>{n.name}</option>)}
          </select>
        </div>
        <div>
          <label>Комнаты</label>
          <select value={filters.rooms} onChange={set("rooms")}>
            <option value="">любые</option>
            {ROOMS.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        <div><label>Цена от</label><input type="number" value={filters.min_price} onChange={set("min_price")} /></div>
        <div><label>Цена до</label><input type="number" value={filters.max_price} onChange={set("max_price")} /></div>
        <div><label>m² от</label><input type="number" value={filters.min_m2} onChange={set("min_m2")} /></div>
        <div><label>m² до</label><input type="number" value={filters.max_m2} onChange={set("max_m2")} /></div>
        <div>
          <label>Сортировка</label>
          <select value={filters.sort} onChange={set("sort")}>
            <option value="newest">сначала новые</option>
            <option value="price_asc">дешевле</option>
            <option value="price_desc">дороже</option>
            <option value="ppm2_asc">по цене за m²</option>
          </select>
        </div>
        <div className="checks">
          <label><input type="checkbox" checked={filters.furnished} onChange={set("furnished")} /> мебель</label>
          <label><input type="checkbox" checked={filters.pool} onChange={set("pool")} /> бассейн</label>
          <label><input type="checkbox" checked={filters.parking} onChange={set("parking")} /> парковка</label>
          <label><input type="checkbox" checked={filters.balcony} onChange={set("balcony")} /> балкон</label>
          <label><input type="checkbox" checked={filters.only_price_drops} onChange={set("only_price_drops")} /> цена снижалась</label>
        </div>
      </div>

      {error && <p className="muted">Ошибка загрузки: {error}</p>}
      {data && (
        <>
          <p className="muted">Найдено: {data.total}</p>
          <div className="grid">
            {data.items.map((l) => <ListingCard key={l.id} l={l} />)}
          </div>
          <div className="pager">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>← Назад</button>
            <span>стр. {page}</span>
            <button disabled={page * data.per_page >= data.total} onClick={() => setPage(page + 1)}>Вперёд →</button>
          </div>
        </>
      )}
    </>
  );
}
