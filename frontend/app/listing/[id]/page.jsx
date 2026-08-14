"use client";

import { use, useEffect, useState } from "react";
import { api, fmtDate, fmtPrice, STATUS_LABELS } from "../../../lib/api";

const BOOL = (v) => (v == null ? "—" : v ? "да" : "нет");

export default function ListingPage({ params }) {
  const { id } = use(params);
  const [l, setL] = useState(null);
  const [fav, setFav] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/api/listings/${id}`).then(setL).catch((e) => setError(String(e)));
    api("/api/favorites")
      .then((favs) => setFav(favs.some((f) => f.id === Number(id))))
      .catch(() => {});
  }, [id]);

  if (error) return <p className="muted">Объект не найден. {error}</p>;
  if (!l) return <p className="muted">Загрузка…</p>;

  const pi = l.price_info || {};
  const fresh = l.freshness || {};
  const loc = [l.district?.name, l.neighbourhood?.name].filter(Boolean).join(" · ");

  const toggleFav = async () => {
    if (fav) {
      await api(`/api/favorites/${l.id}`, { method: "DELETE" });
      setFav(false);
    } else {
      await api("/api/favorites", { method: "POST", body: JSON.stringify({ listing_id: l.id }) });
      setFav(true);
    }
  };

  return (
    <div className="detail">
      <div className="loc">{loc}</div>
      <h1>{l.rooms ? `${l.rooms} · ` : ""}{l.title || l.property_type}</h1>
      {(l.images || []).length > 0 && (
        <div className="gallery">
          {l.images.map((im) => (
            <img key={im.url} src={im.url} alt="" loading="lazy" />
          ))}
        </div>
      )}
      <div className="price">{fmtPrice(l.price, l.currency)}</div>
      {Object.keys(pi.converted || {}).length > 0 && (
        <div className="approx">
          ≈ {Object.entries(pi.converted).map(([c, v]) => fmtPrice(v, c)).join(" · ")} (приблизительно)
        </div>
      )}
      <div className="ppm2">
        {l.price_per_gross_m2 && <>gross: {fmtPrice(l.price_per_gross_m2, l.currency)}/m² · </>}
        {l.price_per_net_m2 && <>net: {fmtPrice(l.price_per_net_m2, l.currency)}/m²</>}
      </div>
      {pi.change_abs != null && pi.change_abs !== 0 && (
        <div className="badge-drop">
          {pi.change_abs < 0 ? "▼ снижение" : "▲ рост"} {fmtPrice(Math.abs(pi.change_abs), l.currency)}
          {" "}({pi.change_pct}%) · изменений цены: {pi.price_changes_count}
        </div>
      )}

      <button className={`fav ${fav ? "on" : ""}`} onClick={toggleFav}>
        {fav ? "★ В избранном" : "☆ В избранное"}
      </button>

      <table>
        <tbody>
          <tr><td>Площадь (gross / net)</td><td>{l.gross_area_m2 ?? "—"} / {l.net_area_m2 ?? "—"} m²</td></tr>
          <tr><td>Этаж</td><td>{l.floor ?? "—"}{l.total_floors ? ` / ${l.total_floors}` : ""}</td></tr>
          <tr><td>Возраст здания</td><td>{l.building_age ?? "—"}</td></tr>
          <tr><td>Отопление</td><td>{l.heating ?? "—"}</td></tr>
          <tr><td>Мебель</td><td>{BOOL(l.furnished)}</td></tr>
          <tr><td>Бассейн</td><td>{BOOL(l.pool)}</td></tr>
          <tr><td>Балкон</td><td>{BOOL(l.balcony)}</td></tr>
          <tr><td>Лифт</td><td>{BOOL(l.elevator)}</td></tr>
          <tr><td>Парковка</td><td>{BOOL(l.parking)}</td></tr>
          {l.distance_to_sea_m != null && <tr><td>До моря</td><td>{l.distance_to_sea_m} м</td></tr>}
          <tr><td>Продавец</td><td>{l.seller_type ?? "—"}{l.agency_name ? ` (${l.agency_name})` : ""}</td></tr>
          <tr><td>Источник</td><td>{l.source_code} · ID {l.external_id}</td></tr>
        </tbody>
      </table>

      {(l.description || "").length > 0 && <p>{l.description}</p>}

      <PriceHistory id={l.id} currency={l.currency} />

      <div className="freshbox">
        <div>В базе с: <b>{fmtDate(fresh.first_seen_at)}</b> ({pi.days_in_db ?? 0} дн.)</div>
        <div>Последняя проверка: <b>{fmtDate(fresh.last_checked_at)}</b></div>
        {fresh.last_changed_at && <div>Данные менялись: {fmtDate(fresh.last_changed_at)}</div>}
        <div>Статус: <b className={`status-${fresh.status}`}>{STATUS_LABELS[fresh.status] || fresh.status}</b></div>
      </div>
    </div>
  );
}

function PriceHistory({ id, currency }) {
  const [history, setHistory] = useState([]);
  useEffect(() => {
    api(`/api/listings/${id}/history`).then(setHistory).catch(() => {});
  }, [id]);
  if (history.length < 2) return null;
  return (
    <div className="history">
      <h2>История цены</h2>
      <ul>
        {history.map((h, i) => (
          <li key={i}>
            {new Date(h.observed_at).toLocaleDateString("ru-RU")} — {fmtPrice(h.price, h.currency || currency)}
            {h.status && h.status !== "active" ? ` (${STATUS_LABELS[h.status] || h.status})` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}
