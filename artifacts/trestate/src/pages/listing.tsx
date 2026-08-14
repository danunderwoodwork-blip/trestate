import { useState, useEffect } from "react";
import { useParams } from "wouter";
import { 
  useGetListing, 
  getGetListingQueryKey,
  useGetListingHistory,
  getGetListingHistoryQueryKey,
  useAddFavorite,
  useRemoveFavorite,
  useGetFavorites
} from '@workspace/api-client-react';
import { fmtPrice, fmtDate, STATUS_LABELS } from "@/lib/utils-tre";
import { 
  MapPin, 
  Heart, 
  Share2, 
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  TrendingDown,
  TrendingUp,
  Info,
  Calendar,
  Building,
  Maximize
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const BOOL = (v: boolean | null | undefined) => (v == null ? "—" : v ? "Да" : "Нет");

export default function ListingPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);

  const { data: listing, isLoading, isError, error } = useGetListing(id, {
    query: { enabled: !!id, retry: 1, queryKey: getGetListingQueryKey(id) }
  });
  
  const { data: history = [] } = useGetListingHistory(id, {
    query: { enabled: !!id, queryKey: getGetListingHistoryQueryKey(id) }
  });

  const { data: favorites = [] } = useGetFavorites();
  
  const isFavorite = favorites.some((f) => f.id === id);
  const addFavorite = useAddFavorite();
  const removeFavorite = useRemoveFavorite();

  const handleToggleFavorite = () => {
    if (isFavorite) {
      removeFavorite.mutate({ listingId: id });
    } else {
      addFavorite.mutate({ data: { listing_id: id } });
    }
  };

  const [activeImageIdx, setActiveImageIdx] = useState(0);

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Info className="w-12 h-12 text-destructive mb-4" />
        <h2 className="text-2xl font-bold mb-2">Объект не найден</h2>
        <p className="text-muted-foreground">{error?.message || "Возможно, объявление было удалено."}</p>
      </div>
    );
  }

  if (isLoading || !listing) {
    return (
      <div className="space-y-6">
        <Skeleton className="w-3/4 h-10" />
        <Skeleton className="w-1/2 h-6" />
        <div className="aspect-video sm:aspect-[21/9] w-full rounded-2xl overflow-hidden">
          <Skeleton className="w-full h-full" />
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="md:col-span-2 space-y-6">
            <Skeleton className="w-full h-32" />
            <Skeleton className="w-full h-64" />
          </div>
          <div className="space-y-4">
            <Skeleton className="w-full h-48" />
          </div>
        </div>
      </div>
    );
  }

  const pi = listing.price_info || {};
  const fresh = listing.freshness || { status: 'unknown', first_seen_at: '', last_seen_at: '', last_checked_at: '' };
  const location = [listing.district?.name, listing.neighbourhood?.name].filter(Boolean).join(" · ");
  
  const isInactive = listing.status === 'inactive';
  const isPossiblyInactive = listing.status === 'possibly_inactive';

  return (
    <div className="max-w-6xl mx-auto pb-12">
      {/* Header section */}
      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground mb-3 font-medium">
          <Badge variant="outline" className="capitalize bg-secondary/10 text-secondary-foreground border-secondary/20">
            {listing.transaction_type === 'sale' ? 'Продажа' : 'Аренда'}
          </Badge>
          <Badge variant="outline" className="capitalize bg-primary/10 text-primary border-primary/20">
            {listing.property_type}
          </Badge>
          <span className="flex items-center gap-1 ml-2">
            <MapPin className="w-4 h-4" />
            {location || "Турция"}
          </span>
        </div>

        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <h1 className="text-3xl md:text-4xl font-bold text-foreground leading-tight max-w-4xl">
            {listing.rooms ? <span className="text-primary">{listing.rooms}</span> : null}
            {listing.rooms ? ' · ' : ''}
            {listing.title || listing.property_type}
          </h1>

          <div className="flex items-center gap-2 flex-shrink-0">
            <Button 
              variant="outline" 
              size="icon" 
              onClick={handleToggleFavorite}
              className={isFavorite ? "text-destructive border-destructive/50 bg-destructive/10" : ""}
            >
              <Heart className={`w-5 h-5 ${isFavorite ? "fill-current" : ""}`} />
            </Button>
            {listing.original_url && (
              <Button variant="outline" size="icon" asChild>
                <a href={listing.original_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="w-5 h-5 text-muted-foreground" />
                </a>
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Gallery */}
      {listing.images && listing.images.length > 0 ? (
        <div className="mb-8 space-y-3">
          <div className="relative aspect-[16/10] md:aspect-[21/9] w-full rounded-2xl overflow-hidden bg-muted group">
            <img 
              src={listing.images[activeImageIdx].url} 
              alt={listing.title || 'Property image'} 
              className="w-full h-full object-contain md:object-cover bg-black/5 backdrop-blur-sm"
            />
            
            {/* Status Overlays */}
            <div className="absolute top-4 left-4 flex flex-col gap-2">
              {isInactive ? (
                <Badge variant="destructive" className="text-sm px-3 py-1 font-bold shadow-sm">
                  {STATUS_LABELS[listing.status]}
                </Badge>
              ) : isPossiblyInactive ? (
                <Badge className="bg-amber-500 text-white hover:bg-amber-600 text-sm px-3 py-1 font-bold shadow-sm">
                  {STATUS_LABELS[listing.status]}
                </Badge>
              ) : null}
            </div>

            {listing.images.length > 1 && (
              <>
                <Button 
                  variant="secondary" 
                  size="icon" 
                  className="absolute left-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity rounded-full h-10 w-10 shadow-md"
                  onClick={() => setActiveImageIdx((prev) => (prev > 0 ? prev - 1 : listing.images.length - 1))}
                >
                  <ChevronLeft className="h-6 w-6" />
                </Button>
                <Button 
                  variant="secondary" 
                  size="icon" 
                  className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity rounded-full h-10 w-10 shadow-md"
                  onClick={() => setActiveImageIdx((prev) => (prev < listing.images.length - 1 ? prev + 1 : 0))}
                >
                  <ChevronRight className="h-6 w-6" />
                </Button>
                <div className="absolute bottom-4 right-4 bg-background/80 backdrop-blur-md px-3 py-1 rounded-full text-sm font-medium shadow-sm">
                  {activeImageIdx + 1} / {listing.images.length}
                </div>
              </>
            )}
          </div>
          
          {/* Thumbnails */}
          {listing.images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
              {listing.images.map((img, idx) => (
                <button 
                  key={idx}
                  onClick={() => setActiveImageIdx(idx)}
                  className={`relative h-20 w-32 flex-shrink-0 rounded-lg overflow-hidden border-2 transition-all ${
                    idx === activeImageIdx ? 'border-primary shadow-sm' : 'border-transparent opacity-60 hover:opacity-100'
                  }`}
                >
                  <img src={img.url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="aspect-[21/9] w-full rounded-2xl bg-muted flex items-center justify-center mb-8 border border-dashed">
          <div className="text-center text-muted-foreground">
            <Building className="w-12 h-12 mx-auto mb-2 opacity-20" />
            <p>Нет фотографий</p>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-8">
        {/* Main Info */}
        <div className="md:col-span-2 space-y-8">
          
          {/* Price Block */}
          <div className="bg-card rounded-2xl border p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-4">
              <div>
                <p className="text-sm text-muted-foreground font-medium mb-1">Стоимость</p>
                <div className="text-4xl font-bold tracking-tight text-foreground">
                  {fmtPrice(listing.price, listing.currency)}
                </div>
              </div>
              
              <div className="text-right">
                {listing.price_per_net_m2 && (
                  <div className="text-lg font-medium text-foreground/80">
                    {fmtPrice(listing.price_per_net_m2, listing.currency)} <span className="text-sm font-normal text-muted-foreground">/ м² (net)</span>
                  </div>
                )}
                {listing.price_per_gross_m2 && (
                  <div className="text-sm text-muted-foreground">
                    {fmtPrice(listing.price_per_gross_m2, listing.currency)} / м² (gross)
                  </div>
                )}
              </div>
            </div>

            {/* Converted Prices */}
            {pi.converted && Object.keys(pi.converted).length > 0 && (
              <div className="flex flex-wrap gap-x-4 gap-y-2 py-3 px-4 bg-muted/50 rounded-lg text-sm text-muted-foreground mb-4">
                <span className="font-medium mr-1">≈</span>
                {Object.entries(pi.converted).map(([c, v]) => (
                  <span key={c}>{fmtPrice(v, c)}</span>
                ))}
              </div>
            )}

            {/* Price Drop Badge */}
            {pi.change_abs != null && pi.change_abs !== 0 && (
              <div className={`flex items-center gap-2 p-3 rounded-lg border ${pi.change_abs < 0 ? 'bg-emerald-50/50 border-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:border-emerald-900/50 dark:text-emerald-400' : 'bg-destructive/5 border-destructive/10 text-destructive'}`}>
                {pi.change_abs < 0 ? <TrendingDown className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" />}
                <div>
                  <span className="font-bold">{pi.change_abs < 0 ? "Снижение" : "Рост"} цены: </span>
                  {fmtPrice(Math.abs(pi.change_abs), listing.currency)} ({pi.change_pct}%)
                  <div className="text-xs opacity-80 mt-0.5">Количество изменений: {pi.price_changes_count}</div>
                </div>
              </div>
            )}
          </div>

          {/* Details Table */}
          <div>
            <h2 className="text-xl font-bold mb-4">Характеристики</h2>
            <div className="bg-card rounded-2xl border overflow-hidden shadow-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-border">
                <div className="divide-y divide-border">
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Площадь (net/gross)</span>
                    <span className="font-medium">{listing.net_area_m2 ?? "—"} / {listing.gross_area_m2 ?? "—"} м²</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Комнаты</span>
                    <span className="font-medium">{listing.rooms ?? "—"}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Этаж / Всего</span>
                    <span className="font-medium">{listing.floor ?? "—"} / {listing.total_floors ?? "—"}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Возраст здания</span>
                    <span className="font-medium">{listing.building_age != null ? `${listing.building_age} лет` : "—"}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Отопление</span>
                    <span className="font-medium">{listing.heating ?? "—"}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Ванные комнаты</span>
                    <span className="font-medium">{listing.bathrooms ?? "—"}</span>
                  </div>
                </div>
                
                <div className="divide-y divide-border">
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Мебель</span>
                    <span className="font-medium">{BOOL(listing.furnished)}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Бассейн</span>
                    <span className="font-medium">{BOOL(listing.pool)}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Балкон</span>
                    <span className="font-medium">{BOOL(listing.balcony)}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Лифт</span>
                    <span className="font-medium">{BOOL(listing.elevator)}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">Парковка</span>
                    <span className="font-medium">{BOOL(listing.parking)}</span>
                  </div>
                  <div className="flex justify-between py-3 px-4">
                    <span className="text-muted-foreground">До моря</span>
                    <span className="font-medium">{listing.distance_to_sea_m != null ? `${listing.distance_to_sea_m} м` : "—"}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Description */}
          {listing.description && (
            <div>
              <h2 className="text-xl font-bold mb-4">Описание</h2>
              <div className="bg-card rounded-2xl border p-6 shadow-sm">
                <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none whitespace-pre-wrap leading-relaxed text-muted-foreground">
                  {listing.description}
                </div>
              </div>
            </div>
          )}
          
          {/* Price History */}
          {history.length >= 2 && (
            <div>
              <h2 className="text-xl font-bold mb-4">История цены</h2>
              <div className="bg-card rounded-2xl border overflow-hidden shadow-sm">
                <div className="divide-y divide-border">
                  {history.map((h, i) => (
                    <div key={i} className="flex justify-between items-center py-3 px-4">
                      <div className="flex items-center gap-3">
                        <Calendar className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm font-medium">{new Date(h.observed_at).toLocaleDateString("ru-RU")}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-bold">{fmtPrice(h.price, h.currency || listing.currency)}</span>
                        {h.status && h.status !== "active" && (
                          <Badge variant="outline" className="text-[10px]">
                            {STATUS_LABELS[h.status] || h.status}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          {/* Contact / Agency Info */}
          <div className="bg-card rounded-2xl border p-5 shadow-sm">
            <h3 className="font-bold text-lg mb-4">Продавец</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Тип продавца</p>
                <p className="font-medium">{listing.seller_type ?? "Не указан"}</p>
              </div>
              
              {listing.agency_name && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Агентство</p>
                  <p className="font-medium">{listing.agency_name}</p>
                </div>
              )}
              
              <Separator />
              
              <div className="pt-2">
                <p className="text-xs text-muted-foreground mb-2">Источник</p>
                <div className="flex items-center justify-between">
                  <Badge variant="secondary">{listing.source_code}</Badge>
                  <span className="text-xs text-muted-foreground font-mono">ID: {listing.external_id}</span>
                </div>
              </div>
              
              {listing.original_url && (
                <Button className="w-full mt-4 gap-2" asChild>
                  <a href={listing.original_url} target="_blank" rel="noopener noreferrer">
                    Открыть оригинал <ExternalLink className="w-4 h-4" />
                  </a>
                </Button>
              )}
            </div>
          </div>

          {/* Freshness / Meta Info */}
          <div className="bg-muted/50 rounded-2xl border p-5 text-sm space-y-4 shadow-inner">
            <div className="flex items-start gap-3">
              <div className={`mt-0.5 w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                listing.status === 'active' ? 'bg-emerald-500' : 
                listing.status === 'possibly_inactive' ? 'bg-amber-500' : 'bg-destructive'
              }`} />
              <div>
                <p className="font-medium text-foreground">
                  Статус: {STATUS_LABELS[fresh.status] || fresh.status}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Обновлено {fmtDate(fresh.last_checked_at)}
                </p>
              </div>
            </div>
            
            <Separator className="bg-border/60" />
            
            <div className="grid grid-cols-2 gap-y-3 gap-x-2 text-xs">
              <div>
                <p className="text-muted-foreground mb-0.5">В базе с</p>
                <p className="font-medium text-foreground">{new Date(fresh.first_seen_at).toLocaleDateString("ru-RU")}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Дней в базе</p>
                <p className="font-medium text-foreground">{pi.days_in_db ?? 0}</p>
              </div>
              {fresh.last_changed_at && (
                <div className="col-span-2 mt-1">
                  <p className="text-muted-foreground mb-0.5">Последнее изменение данных</p>
                  <p className="font-medium text-foreground">{fmtDate(fresh.last_changed_at)}</p>
                </div>
              )}
              {listing.publication_date && (
                <div className="col-span-2 mt-1">
                  <p className="text-muted-foreground mb-0.5">Дата публикации на источнике</p>
                  <p className="font-medium text-foreground">{new Date(listing.publication_date).toLocaleDateString("ru-RU")}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
