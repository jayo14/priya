import React from "react";

export const Navbar: React.FC = () => {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-amber-500 to-rose-500 flex items-center justify-center font-bold text-white shadow-md shadow-rose-500/20">
            P
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-white">
              Priya
            </span>
            <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Scout v0.1
            </span>
          </div>
        </div>

        <nav className="flex items-center gap-6 text-sm">
          <span className="text-zinc-400 hover:text-white transition cursor-pointer">
            Overview
          </span>
          <span className="text-zinc-500 hover:text-zinc-300 transition cursor-pointer">
            Providers
          </span>
          <span className="text-zinc-500 hover:text-zinc-300 transition cursor-pointer">
            Sources
          </span>
          <span className="text-zinc-500 hover:text-zinc-300 transition cursor-pointer">
            System
          </span>
        </nav>
      </div>
    </header>
  );
};
