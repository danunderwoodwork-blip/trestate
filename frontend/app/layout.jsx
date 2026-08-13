import "./globals.css";
import "leaflet/dist/leaflet.css";
import Link from "next/link";

export const metadata = {
  title: "TREstate — недвижимость в Турции",
  description: "Независимый агрегатор недвижимости в Турции",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>
        <header className="site">
          <div className="container">
            <Link href="/" className="logo">TREstate</Link>
            <nav>
              <Link href="/">Поиск</Link>
              <Link href="/map">Карта</Link>
              <Link href="/favorites">Избранное</Link>
            </nav>
          </div>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
