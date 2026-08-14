export function fmtPrice(value: number | null | undefined, currency: string | null | undefined): string {
  if (value == null) return '—';
  return `${Math.round(value).toLocaleString('ru-RU')} ${currency ?? ''}`.trim();
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'long', timeStyle: 'short' });
}

export const STATUS_LABELS: Record<string, string> = {
  active: 'активно',
  possibly_inactive: 'возможно снято',
  inactive: 'снято с публикации',
};
