import { useState, useEffect, useRef } from "react";
import { useGetFavorites } from '@workspace/api-client-react';
import { ListingCard } from "@/components/listing-card";
import { Heart, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import { Skeleton } from "@/components/ui/skeleton";

export default function FavoritesPage() {
  const { data: favorites, isLoading, isError } = useGetFavorites();

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Heart className="w-8 h-8 text-destructive fill-destructive" />
          Избранное
        </h1>
        <p className="text-muted-foreground mt-2">
          Сохраненные вами объекты недвижимости для быстрого доступа.
        </p>
      </div>

      {isError ? (
        <div className="bg-destructive/10 border-destructive/20 text-destructive border rounded-lg p-6 text-center max-w-lg mx-auto mt-12">
          <h3 className="font-semibold mb-2">Ошибка при загрузке</h3>
          <p className="text-sm opacity-90">Не удалось загрузить избранные объекты. Пожалуйста, обновите страницу.</p>
        </div>
      ) : isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-2">
              <Skeleton className="w-full aspect-[4/3] rounded-xl" />
              <Skeleton className="w-3/4 h-5 mt-2" />
              <Skeleton className="w-1/2 h-6" />
              <Skeleton className="w-full h-4 mt-auto" />
            </div>
          ))}
        </div>
      ) : !favorites || favorites.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 px-4 text-center bg-card border rounded-2xl shadow-sm max-w-2xl mx-auto mt-8">
          <div className="bg-muted p-5 rounded-full mb-6">
            <Heart className="w-10 h-10 text-muted-foreground" />
          </div>
          <h3 className="text-2xl font-bold text-foreground mb-3">В избранном пока пусто</h3>
          <p className="text-muted-foreground mb-8 max-w-md text-lg">
            Отмечайте понравившиеся объекты символом сердечка, чтобы не потерять их и следить за изменением цены.
          </p>
          <Button size="lg" asChild className="px-8 font-medium">
            <Link href="/" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              Перейти к поиску
            </Link>
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {favorites.map((listing) => (
            <ListingCard 
              key={listing.id} 
              listing={listing} 
            />
          ))}
        </div>
      )}
    </div>
  );
}
