// Все данные — только из нашего API (наша БД). Внешние порталы не участвуют.

export function deviceId() {
  if (typeof window === "undefined") return null;
  let id = localStorage.getItem("tre_device_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("tre_device_id", id);
  }
  return id;
}

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const id = deviceId();
  if (id) headers["X-Device-Id"] = id;
  const resp = await fetch(path, { ...options, headers });
  if (!resp.ok) throw new Error(`API ${resp.status}`);
  return resp.status === 204 ? null : resp.json();
}

export function fmtPrice(value, currency) {
  if (value == null) return "—";
  return `${Math.round(value).toLocaleString("ru-RU")} ${currency || ""}`.trim();
}

export function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("ru-RU", { dateStyle: "long", timeStyle: "short" });
}

export const STATUS_LABELS = {
  active: "активно",
  possibly_inactive: "возможно снято",
  inactive: "снято с публикации",
};
