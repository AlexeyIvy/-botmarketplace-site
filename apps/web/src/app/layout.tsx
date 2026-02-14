import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "./navbar";

export const metadata: Metadata = {
  title: "BotMarketplace",
  description: "Trading terminal, strategy lab & bot factory",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>
        <Navbar />
        <main style={{ paddingTop: "var(--nav-height)" }}>{children}</main>
      </body>
    </html>
  );
}
