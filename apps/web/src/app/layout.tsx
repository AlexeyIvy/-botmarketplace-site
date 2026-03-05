import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "./navbar";
import { ChatWidgetWrapper } from "@/components/chat/ChatWidgetWrapper";
import { OnboardingModal } from "@/components/OnboardingModal";

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
      <head>
        {/* Anti-FOUC: apply theme class before first paint */}
        {/* eslint-disable-next-line @next/next/no-before-interactive-script-outside-document */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var t=localStorage.getItem('theme');if(t==='light'){document.documentElement.classList.add('theme-light');}else if(t==='system'&&!window.matchMedia('(prefers-color-scheme: dark)').matches){document.documentElement.classList.add('theme-light');}})();`,
          }}
        />
      </head>
      <body>
        <Navbar />
        <OnboardingModal />
        <main style={{ paddingTop: "var(--nav-height)" }}>{children}</main>
        <ChatWidgetWrapper />
      </body>
    </html>
  );
}
