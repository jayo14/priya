import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Priya — AI Subscription Deal Finder",
  description:
    "Your personal AI deal scout searching Telegram channels, Reddit, and communities for free or discounted AI subscriptions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-zinc-950 text-zinc-100 flex flex-col`}
      >
        <Navbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-zinc-900 py-6 text-center text-xs text-zinc-500">
          Priya &bull; Deterministic AI Subscription Promotion Discovery Engine &bull; Phase 1 Foundation
        </footer>
      </body>
    </html>
  );
}
