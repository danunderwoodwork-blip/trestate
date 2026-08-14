import { type ReactNode } from "react";
import { Link, useLocation } from "wouter";
import { Search, Map as MapIcon, Heart, Home } from "lucide-react";

export function Layout({ children }: { children: ReactNode }) {
  const [location] = useLocation();

  const isActive = (path: string) => location === path || (path !== "/" && location.startsWith(path));

  return (
    <div className="min-h-[100dvh] flex flex-col w-full bg-background">
      <header className="sticky top-0 z-40 w-full border-b bg-primary text-primary-foreground shadow-sm">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight">
            <Home className="h-6 w-6" />
            <span>TREstate</span>
          </Link>
          <nav className="flex items-center space-x-1 md:space-x-4">
            <Link 
              href="/" 
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${location === '/' ? 'bg-primary-foreground/10' : 'hover:bg-primary-foreground/10'}`}
              data-testid="nav-search"
            >
              <Search className="h-4 w-4" />
              <span className="hidden md:inline">Поиск</span>
            </Link>
            <Link 
              href="/map" 
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/map') ? 'bg-primary-foreground/10' : 'hover:bg-primary-foreground/10'}`}
              data-testid="nav-map"
            >
              <MapIcon className="h-4 w-4" />
              <span className="hidden md:inline">Карта</span>
            </Link>
            <Link 
              href="/favorites" 
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/favorites') ? 'bg-primary-foreground/10' : 'hover:bg-primary-foreground/10'}`}
              data-testid="nav-favorites"
            >
              <Heart className="h-4 w-4" />
              <span className="hidden md:inline">Избранное</span>
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1 w-full max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
}
