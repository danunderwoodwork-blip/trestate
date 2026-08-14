import Link from "next/link";
import { fmtPrice } from "../lib/api";

export default function ListingCard({ l }) {
  const loc = [l.district?.name, l.neighbourhood?.name].filter(Boolean).join(" · ");
  return (
    <Link href={`/listing/${l.id}`} className="card">
      {l.images?.[0] && <img className="thumb" src={l.images[0].url} alt="" loading="lazy" />}
      <div className="loc">{loc || "Турция"}</div>
      <h3>{l.rooms ? `${l.rooms} · ` : ""}{l.title || `${l.property_type}`}</h3>
      <div className="price">{fmtPrice(l.price, l.currency)}</div>
      <div className="ppm2">
        {l.price_per_net_m2 ? `${fmtPrice(l.price_per_net_m2, l.currency)}/m² (net)` : ""}
        {l.net_area_m2 ? ` · ${l.net_area_m2} m²` : ""}
      </div>
      <div className="specs">
        {l.floor != null && <span>этаж {l.floor}{l.total_floors ? `/${l.total_floors}` : ""}</span>}
        {l.building_age != null && <span>возраст {l.building_age}</span>}
        {l.furnished && <span>мебель</span>}
        {l.pool && <span>бассейн</span>}
        {l.balcony && <span>балкон</span>}
        {l.parking && <span>парковка</span>}
      </div>
      <div className="fresh">
        проверено {new Date(l.last_checked_at).toLocaleDateString("ru-RU")} ·{" "}
        <span className={`status-${l.status}`}>{l.status === "active" ? "активно" : l.status}</span>
      </div>
    </Link>
  );
}
