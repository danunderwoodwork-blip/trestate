import { useEffect, useRef, useState } from "react";
import { useGetMapPoints, getGetMapPointsQueryKey } from '@workspace/api-client-react';
import { keepPreviousData } from '@tanstack/react-query';
import { fmtPrice } from "@/lib/utils-tre";
import { Link } from "wouter";
import { MapPin, Filter, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";

// Leaflet requires dynamic import on SSR, but since this is an SPA we can import directly
// However, we need to handle it carefully in React effects
import * as L from "leaflet";
import "leaflet/dist/leaflet.css";

export default function MapPage() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.LayerGroup | null>(null);
  
  const [bounds, setBounds] = useState<{
    min_lat?: number; max_lat?: number; min_lon?: number; max_lon?: number;
  }>({});

  // Use aggressive caching and no refetching while panning, unless specifically requested
  const mapParams = { ...bounds, limit: 1000 };
  const { data: points = [], isLoading } = useGetMapPoints(
    mapParams, 
    { 
      query: { 
        placeholderData: keepPreviousData,
        enabled: !!bounds.min_lat,
        staleTime: 60000,
        queryKey: getGetMapPointsQueryKey(mapParams),
      } 
    }
  );

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Alanya center [36.52, 32.05]
    mapRef.current = L.map(mapContainerRef.current, {
      center: [36.52, 32.05],
      zoom: 11,
      zoomControl: false // We'll add it in a custom position if needed
    });

    L.control.zoom({ position: 'bottomright' }).addTo(mapRef.current);

    // CartoDB Voyager tiles (light theme, good for data)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(mapRef.current);

    markersRef.current = L.layerGroup().addTo(mapRef.current);

    // Initial bounds fetch
    const updateBounds = () => {
      if (!mapRef.current) return;
      const b = mapRef.current.getBounds();
      setBounds({
        min_lat: b.getSouth(),
        max_lat: b.getNorth(),
        min_lon: b.getWest(),
        max_lon: b.getEast(),
      });
    };

    mapRef.current.on('moveend', updateBounds);
    
    // Slight delay to ensure map is fully sized before getting initial bounds
    setTimeout(() => {
      if (mapRef.current) {
        mapRef.current.invalidateSize();
        updateBounds();
      }
    }, 100);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Custom marker icon creation — built with DOM nodes to prevent XSS from feed-derived values
  const createMarkerIcon = (price: number | null | undefined, currency: string) => {
    const formattedPrice = fmtPrice(price, currency).replace(/\s/g, '');

    const wrapper = document.createElement('div');
    wrapper.className =
      'bg-primary text-primary-foreground font-bold px-2 py-1 rounded-md shadow-md text-[11px] whitespace-nowrap border border-primary-foreground/20 hover:scale-110 transition-transform origin-bottom-center relative';
    wrapper.textContent = formattedPrice; // textContent — never interpolated as HTML

    const arrow = document.createElement('div');
    arrow.className =
      'absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-primary transform rotate-45 border-b border-r border-primary-foreground/20';
    wrapper.appendChild(arrow);

    return L.divIcon({
      className: 'custom-map-marker',
      html: wrapper,      // Leaflet accepts HTMLElement directly
      iconSize: [0, 0],
      iconAnchor: [35, 30],
      popupAnchor: [0, -30],
    });
  };

  // Update markers when data changes
  useEffect(() => {
    if (!mapRef.current || !markersRef.current) return;
    
    markersRef.current.clearLayers();

    points.forEach(point => {
      if (point.latitude && point.longitude) {
        const marker = L.marker([point.latitude, point.longitude], {
          icon: createMarkerIcon(point.price, point.currency)
        });
        
        // Build popup with DOM nodes to avoid HTML injection from feed data
        const container = document.createElement('div');
        container.className = 'p-1 min-w-[140px]';

        const priceEl = document.createElement('div');
        priceEl.className = 'font-bold text-sm mb-1';
        priceEl.textContent = fmtPrice(point.price, point.currency);
        container.appendChild(priceEl);

        if (point.rooms != null) {
          const roomsEl = document.createElement('div');
          roomsEl.className = 'text-xs text-muted-foreground mb-2';
          roomsEl.textContent = `${point.rooms} комн.`;
          container.appendChild(roomsEl);
        }

        const link = document.createElement('a');
        link.href = `/listing/${Number(point.id)}`;
        link.className = 'block w-full text-center bg-primary text-primary-foreground text-xs py-1.5 rounded font-medium hover:bg-primary/90 transition-colors';
        link.setAttribute('data-wouter-link', '');
        link.textContent = 'Подробнее';
        container.appendChild(link);

        marker.bindPopup(container, {
          className: 'custom-leaflet-popup'
        });
        
        markersRef.current?.addLayer(marker);
      }
    });

    // We need to attach event listeners to links in popups since they are outside React's control
    mapRef.current.on('popupopen', (e) => {
      const links = e.popup.getElement()?.querySelectorAll('a[data-wouter-link]');
      links?.forEach(link => {
        link.addEventListener('click', (ev) => {
          ev.preventDefault();
          const href = link.getAttribute('href');
          if (href) {
            // Standard wouter navigation from outside React tree
            window.history.pushState(null, '', href);
            window.dispatchEvent(new Event('popstate'));
          }
        });
      });
    });

  }, [points]);

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] -mx-4 md:-mx-6 lg:-mx-8 -mt-4 md:-mt-6 lg:-mt-8 mb-[-1rem]">
      {/* Map Header / Controls Overlay */}
      <div className="absolute z-[1000] top-20 left-4 md:left-8 right-4 md:right-8 flex flex-wrap justify-between items-start gap-2 pointer-events-none">
        
        <div className="bg-background/90 backdrop-blur-md rounded-lg shadow-md border px-4 py-2 pointer-events-auto flex items-center gap-3">
          <MapPin className="w-5 h-5 text-primary" />
          <div>
            <h1 className="font-bold text-sm leading-tight">Объекты на карте</h1>
            <p className="text-[10px] text-muted-foreground">
              {isLoading ? 'Загрузка...' : `Показано: ${points.length} объектов в области видимости`}
            </p>
          </div>
        </div>

        {/* Action buttons could go here */}
        <div className="flex gap-2 pointer-events-auto">
          <Button variant="secondary" size="sm" className="shadow-md bg-background/90 backdrop-blur" asChild>
             <Link href="/">К списку</Link>
          </Button>
        </div>
      </div>

      {/* Map Container */}
      <div 
        ref={mapContainerRef} 
        className="w-full flex-1 z-0 relative"
      />
      
      <style dangerouslySetInnerHTML={{__html: `
        .leaflet-container { font-family: inherit; }
        .custom-leaflet-popup .leaflet-popup-content-wrapper { border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 2px; }
        .custom-leaflet-popup .leaflet-popup-content { margin: 8px; line-height: 1.4; }
        .custom-leaflet-popup .leaflet-popup-tip-container { display: none; /* Hide default tip */ }
      `}} />
    </div>
  );
}
