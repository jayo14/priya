import { HealthStatus } from "@/components/HealthStatus";

const MONITORED_CATALOGUE = [
  { name: "Claude Pro & Max", provider: "Anthropic", status: "Ready" },
  { name: "ChatGPT Plus & Pro", provider: "OpenAI", status: "Ready" },
  { name: "Grok Subscriptions", provider: "xAI", status: "Ready" },
  { name: "Google AI Pro", provider: "Google", status: "Ready" },
  { name: "Perplexity Pro", provider: "Perplexity", status: "Ready" },
  { name: "Cursor Pro", provider: "Cursor", status: "Ready" },
  { name: "GitHub Copilot Pro", provider: "GitHub", status: "Ready" },
];

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Hero Section */}
      <div className="space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-300 border border-rose-500/20">
          <span>Your Personal AI Deal Scout</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white">
          Meet <span className="bg-gradient-to-r from-amber-400 to-rose-400 bg-clip-text text-transparent">Priya</span>.
        </h1>
        <p className="text-lg text-zinc-400 max-w-3xl leading-relaxed">
          Think of Priya as a tireless friend who monitors Telegram channels, Reddit posts, and partner offers for free or discounted premium AI subscriptions—so you never have to waste hours searching.
        </p>
        <p className="text-sm italic text-zinc-500">
          You discover the opportunity. Priya brings it to you. You decide whether to claim it.
        </p>
      </div>

      {/* System Health Component */}
      <HealthStatus />

      {/* Monitored AI Providers Catalogue Overview */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-white">Monitored Subscription Plans</h2>
          <p className="text-sm text-zinc-400">
            Initial catalog configured in the Priya domain registry for discovery monitoring.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {MONITORED_CATALOGUE.map((item) => (
            <div
              key={item.name}
              className="p-5 rounded-2xl border border-zinc-800/80 bg-zinc-900/40 hover:border-zinc-700 transition"
            >
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">
                {item.provider}
              </span>
              <h3 className="text-base font-semibold text-white mt-1">{item.name}</h3>
              <div className="mt-4 flex items-center justify-between text-xs">
                <span className="text-zinc-500">Pipeline status</span>
                <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  {item.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
