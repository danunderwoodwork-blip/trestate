import { Link } from "wouter";
import type { ListingCard as ListingCardType } from '@workspace/api-client-react';
import { fmtPrice, STATUS_LABELS } from "@/lib/utils-tre";
import { Building2, MapPin, Maximize, TrendingDown } from "lucide-react";
import { format } from "date-fns";

interface ListingCardProps {
  listing: ListingCardType;
  priceDrop?: number;
}

export function ListingCard({ listing, priceDrop }: ListingCardProps) {
  const location = [listing.district?.name, listing.neighbourhood?.name].filter(Boolean).join(" · ");
  
  const isPossiblyInactive = listing.status === 'possibly_inactive';
  const isInactive = listing.status === 'inactive';

  return (
    <Link 
      href={`/listing/${listing.id}`} 
      className={`group flex flex-col bg-card border rounded-xl overflow-hidden hover:shadow-md transition-all duration-200 ${isInactive ? 'opacity-70' : ''}`}
      data-testid={`card-listing-${listing.id}`}
    >
      <div className="relative aspect-[4/3] bg-muted overflow-hidden">
        {listing.images?.[0] ? (
          <img 
            src={listing.images[0].url} 
            alt={listing.title || 'Property thumbnail'} 
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-muted-foreground bg-muted">
            <Building2 className="w-12 h-12 opacity-20" />
          </div>
        )}
        
        {/* Status badges overlay */}
        <div className="absolute top-3 left-3 flex flex-col gap-2">
          {isInactive ? (
            <span className="bg-destructive/90 text-destructive-foreground text-xs font-semibold px-2.5 py-1 rounded-md backdrop-blur-sm shadow-sm">
              {STATUS_LABELS[listing.status]}
            </span>
          ) : isPossiblyInactive ? (
            <span className="bg-amber-500/90 text-white text-xs font-semibold px-2.5 py-1 rounded-md backdrop-blur-sm shadow-sm">
              {STATUS_LABELS[listing.status]}
            </span>
          ) : null}
          
          {priceDrop && priceDrop < 0 && (
            <span className="bg-emerald-600/90 text-white text-xs font-semibold px-2.5 py-1 rounded-md backdrop-blur-sm shadow-sm flex items-center gap-1">
              <TrendingDown className="w-3 h-3" />
              Снижение цены
            </span>
          )}
        </div>
      </div>

      <div className="p-4 flex flex-col flex-1">
        <div className="flex items-center text-xs text-muted-foreground mb-1.5 font-medium">
          <MapPin className="w-3.5 h-3.5 mr-1" />
          <span className="truncate">{location || "Турция"}</span>
        </div>
        
        <h3 className="font-semibold text-foreground text-sm line-clamp-2 leading-tight mb-2 min-h-[40px]">
          {listing.rooms ? <span className="text-primary font-bold">{listing.rooms}</span> : null}
          {listing.rooms ? ' · ' : ''}
          {listing.title || listing.property_type}
        </h3>
        
        <div className="mt-auto pt-2 border-t flex flex-col">
          <div className="text-xl font-bold text-foreground tracking-tight">
            {fmtPrice(listing.price, listing.currency)}
          </div>
          
          <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
            {listing.net_area_m2 && (
              <div className="flex items-center gap-1 bg-muted/50 px-2 py-0.5 rounded">
                <Maximize className="w-3.5 h-3.5 opacity-70" />
                <span>{listing.net_area_m2} м²</span>
              </div>
            )}
            {listing.price_per_net_m2 && (
              <span className="truncate opacity-80">{fmtPrice(listing.price_per_net_m2, listing.currency)} / м²</span>
            )}
          </div>
          
          <div className="flex flex-wrap gap-1.5 mt-3">
            {listing.floor != null && <span className="bg-secondary/10 text-secondary-foreground text-[10px] px-2 py-0.5 rounded border border-secondary/20">Этаж {listing.floor}{listing.total_floors ? `/${listing.total_floors}` : ''}</span>}
            {listing.building_age != null && <span className="bg-secondary/10 text-secondary-foreground text-[10px] px-2 py-0.5 rounded border border-secondary/20">{listing.building_age} лет</span>}
            {listing.furnished && <span className="bg-accent text-accent-foreground text-[10px] px-2 py-0.5 rounded border">Мебель</span>}
            {listing.pool && <span className="bg-accent text-accent-foreground text-[10px] px-2 py-0.5 rounded border">Бассейн</span>}
          </div>
          
          <div className="mt-3 text-[10px] text-muted-foreground flex justify-between opacity-80">
            <span>Обн: {format(new Date(listing.last_checked_at), 'dd.MM.yyyy')}</span>
            <span className="capitalize">{listing.transaction_type === 'sale' ? 'Продажа' : 'Аренда'}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
