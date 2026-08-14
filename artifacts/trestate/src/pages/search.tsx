import { useState, useEffect, useCallback } from "react";
import { useLocation } from "wouter";
import { useGetListings, getGetListingsQueryKey, useGetLocations, useGetMeta } from '@workspace/api-client-react';
import { keepPreviousData } from '@tanstack/react-query';
import { ListingCard } from "@/components/listing-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { SlidersHorizontal, ChevronLeft, ChevronRight, X, Search } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

const ROOMS = ["1+0", "1+1", "2+1", "3+1", "4+1", "5+1"];

export default function SearchPage() {
  const [, setLocationUrl] = useLocation();
  
  // Using query params directly from URL would be better in a real app, 
  // but keeping state local for simplicity in this implementation
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
  const perPage = 20;

  // Build params object, ignoring empty values
  const buildParams = useCallback(() => {
    const params: any = { page, per_page: perPage };
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value === "" || value === false) return;
      if (key === "rooms" && value) {
        params[key] = [value];
      } else if (["min_price", "max_price", "min_m2", "max_m2"].includes(key) && value) {
        params[key] = Number(value);
      } else {
        params[key] = value;
      }
    });
    
    return params;
  }, [filters, page]);

  // API Hooks
  const { data: locations = [] } = useGetLocations();
  const { data: meta } = useGetMeta();
  const currentParams = buildParams();
  const { data: listingData, isLoading, isError, error } = useGetListings(currentParams, { 
    query: { placeholderData: keepPreviousData, queryKey: getGetListingsQueryKey(currentParams) } 
  });

  const country = locations[0];
  const districts = (country?.children || []).flatMap((p) => p.children || []);
  const hoods = districts.flatMap((d) => (d.children || []).map((n) => ({ ...n, district: d.slug })));

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1); // Reset page on filter change
  };

  const handleResetFilters = () => {
    setFilters({
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
    setPage(1);
  };

  const FiltersForm = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="transaction_type">Сделка</Label>
          <Select 
            value={filters.transaction_type} 
            onValueChange={(v) => handleFilterChange("transaction_type", v)}
          >
            <SelectTrigger id="transaction_type">
              <SelectValue placeholder="Любая" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="sale">Покупка</SelectItem>
              <SelectItem value="rent_long">Аренда</SelectItem>
              <SelectItem value="rent_short">Краткосрочная</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="property_type">Тип недвиж.</Label>
          <Select 
            value={filters.property_type || "any"} 
            onValueChange={(v) => handleFilterChange("property_type", v === "any" ? "" : v)}
          >
            <SelectTrigger id="property_type">
              <SelectValue placeholder="Любой" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Любой</SelectItem>
              <SelectItem value="apartment">Квартира</SelectItem>
              <SelectItem value="house">Дом</SelectItem>
              <SelectItem value="villa">Вилла</SelectItem>
              <SelectItem value="commercial">Коммерческая</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="district">Район</Label>
          <Select 
            value={filters.district || "any"} 
            onValueChange={(v) => {
              handleFilterChange("district", v === "any" ? "" : v);
              handleFilterChange("neighbourhood", ""); // Reset hood when district changes
            }}
          >
            <SelectTrigger id="district">
              <SelectValue placeholder="Все районы" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Все районы</SelectItem>
              {districts.map((d) => (
                <SelectItem key={d.slug} value={d.slug}>{d.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="neighbourhood">Микрорайон</Label>
          <Select 
            value={filters.neighbourhood || "any"} 
            onValueChange={(v) => handleFilterChange("neighbourhood", v === "any" ? "" : v)}
            disabled={!filters.district}
          >
            <SelectTrigger id="neighbourhood">
              <SelectValue placeholder="Все микрорайоны" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Все микрорайоны</SelectItem>
              {hoods
                .filter((n) => !filters.district || n.district === filters.district)
                .map((n) => <SelectItem key={n.slug} value={n.slug}>{n.name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="rooms">Комнаты</Label>
          <Select 
            value={filters.rooms || "any"} 
            onValueChange={(v) => handleFilterChange("rooms", v === "any" ? "" : v)}
          >
            <SelectTrigger id="rooms">
              <SelectValue placeholder="Любые" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Любые</SelectItem>
              {ROOMS.map((r) => (
                <SelectItem key={r} value={r}>{r}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-4 pt-2 border-t">
        <h4 className="text-sm font-medium text-foreground">Цена</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="min_price" className="text-xs text-muted-foreground">От</Label>
            <Input 
              id="min_price" 
              type="number" 
              placeholder="0"
              value={filters.min_price}
              onChange={(e) => handleFilterChange("min_price", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="max_price" className="text-xs text-muted-foreground">До</Label>
            <Input 
              id="max_price" 
              type="number" 
              placeholder="∞"
              value={filters.max_price}
              onChange={(e) => handleFilterChange("max_price", e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="space-y-4 pt-2 border-t">
        <h4 className="text-sm font-medium text-foreground">Площадь (m²)</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="min_m2" className="text-xs text-muted-foreground">От</Label>
            <Input 
              id="min_m2" 
              type="number" 
              placeholder="0"
              value={filters.min_m2}
              onChange={(e) => handleFilterChange("min_m2", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="max_m2" className="text-xs text-muted-foreground">До</Label>
            <Input 
              id="max_m2" 
              type="number" 
              placeholder="∞"
              value={filters.max_m2}
              onChange={(e) => handleFilterChange("max_m2", e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center space-x-2">
            <Checkbox 
              id="furnished" 
              checked={filters.furnished}
              onCheckedChange={(c) => handleFilterChange("furnished", c)}
            />
            <Label htmlFor="furnished" className="text-sm font-normal">Мебель</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox 
              id="pool" 
              checked={filters.pool}
              onCheckedChange={(c) => handleFilterChange("pool", c)}
            />
            <Label htmlFor="pool" className="text-sm font-normal">Бассейн</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox 
              id="parking" 
              checked={filters.parking}
              onCheckedChange={(c) => handleFilterChange("parking", c)}
            />
            <Label htmlFor="parking" className="text-sm font-normal">Парковка</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox 
              id="balcony" 
              checked={filters.balcony}
              onCheckedChange={(c) => handleFilterChange("balcony", c)}
            />
            <Label htmlFor="balcony" className="text-sm font-normal">Балкон</Label>
          </div>
        </div>
        
        <div className="pt-2">
          <div className="flex items-center space-x-2 bg-emerald-50 dark:bg-emerald-950/30 p-3 rounded-lg border border-emerald-100 dark:border-emerald-900/50">
            <Checkbox 
              id="only_price_drops" 
              checked={filters.only_price_drops}
              onCheckedChange={(c) => handleFilterChange("only_price_drops", c)}
            />
            <Label htmlFor="only_price_drops" className="text-sm font-medium text-emerald-800 dark:text-emerald-400">Только снижения цены</Label>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col md:flex-row gap-6">
      {/* Desktop Sidebar Filters */}
      <aside className="hidden md:block w-72 flex-shrink-0">
        <div className="sticky top-24 bg-card rounded-xl border shadow-sm p-5">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <SlidersHorizontal className="w-5 h-5 text-primary" />
              Фильтры
            </h2>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleResetFilters}
              className="text-xs h-8 text-muted-foreground hover:text-foreground"
            >
              Сбросить
            </Button>
          </div>
          <FiltersForm />
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Недвижимость в Турции</h1>
            <div className="text-sm text-muted-foreground mt-1">
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <Skeleton className="w-8 h-4 inline-block" /> объектов найдено
                </span>
              ) : (
                `Найдено ${listingData?.total || 0} объектов`
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {/* Mobile Filters Trigger */}
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" className="md:hidden flex-1 sm:flex-none flex items-center gap-2">
                  <SlidersHorizontal className="w-4 h-4" />
                  Фильтры
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-full sm:w-[400px] overflow-y-auto">
                <SheetHeader className="mb-6 text-left">
                  <SheetTitle className="text-xl">Фильтры</SheetTitle>
                  <SheetDescription>
                    Настройте параметры поиска для точных результатов.
                  </SheetDescription>
                </SheetHeader>
                <FiltersForm />
                <div className="mt-8 pt-4 border-t sticky bottom-0 bg-background/95 backdrop-blur z-10 pb-4">
                  <Button className="w-full" onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))}>
                    Показать результаты
                  </Button>
                </div>
              </SheetContent>
            </Sheet>

            {/* Sort Select */}
            <Select 
              value={filters.sort} 
              onValueChange={(v) => handleFilterChange("sort", v)}
            >
              <SelectTrigger className="w-full sm:w-[180px] bg-card">
                <SelectValue placeholder="Сортировка" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">Сначала новые</SelectItem>
                <SelectItem value="price_asc">Дешевле</SelectItem>
                <SelectItem value="price_desc">Дороже</SelectItem>
                <SelectItem value="ppm2_asc">По цене за m²</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {isError ? (
          <div className="bg-destructive/10 border-destructive/20 text-destructive border rounded-lg p-6 text-center">
            <h3 className="font-semibold mb-2">Ошибка при загрузке данных</h3>
            <p className="text-sm opacity-90">{error?.message || "Пожалуйста, попробуйте изменить параметры поиска."}</p>
          </div>
        ) : isLoading && !listingData ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-2">
                <Skeleton className="w-full aspect-[4/3] rounded-xl" />
                <Skeleton className="w-3/4 h-5 mt-2" />
                <Skeleton className="w-1/2 h-6" />
                <Skeleton className="w-full h-4 mt-auto" />
              </div>
            ))}
          </div>
        ) : listingData?.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 px-4 text-center bg-card border rounded-xl shadow-sm">
            <div className="bg-muted p-4 rounded-full mb-4">
              <Search className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">Ничего не найдено</h3>
            <p className="text-muted-foreground mb-6 max-w-md">
              По вашему запросу нет подходящих объектов. Попробуйте смягчить условия поиска или сбросить фильтры.
            </p>
            <Button onClick={handleResetFilters}>Сбросить все фильтры</Button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {listingData?.items.map((listing) => (
                <ListingCard 
                  key={listing.id} 
                  listing={listing} 
                  priceDrop={filters.only_price_drops ? -1 : undefined} // Hint for ui if filtered
                />
              ))}
            </div>

            {/* Pagination */}
            {listingData && listingData.total > listingData.per_page && (
              <div className="flex items-center justify-center gap-4 mt-10 pt-6 border-t">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1 || isLoading}
                  className="w-28 flex items-center justify-center gap-2"
                >
                  <ChevronLeft className="w-4 h-4" /> Назад
                </Button>
                
                <span className="text-sm font-medium text-muted-foreground">
                  Стр. {page} из {Math.ceil(listingData.total / listingData.per_page)}
                </span>
                
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * listingData.per_page >= listingData.total || isLoading}
                  className="w-28 flex items-center justify-center gap-2"
                >
                  Вперед <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
