import { useCallback, useEffect, useRef, useState } from 'react';
import { Search, Sparkles } from 'lucide-react';
import SalonCard from '../components/SalonCard';
import salonService from '../services/salonService';
import type { SalonListDto } from '../types';

export default function SalonsPage() {
  const [salons, setSalons] = useState<SalonListDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchDistrict, setSearchDistrict] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchSalons = useCallback(async (district: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await salonService.getSalons(district || undefined);
      setSalons(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load salons.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Debounce the API call by 400ms to avoid hammering the backend on every keystroke
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchSalons(searchDistrict);
    }, 400);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchDistrict, fetchSalons]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f0f13] via-[#12101e] to-[#0f0f13]">
      {/* Ambient glow blobs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-violet-700/20 blur-3xl" />
        <div className="absolute top-1/3 -right-32 h-80 w-80 rounded-full bg-fuchsia-700/15 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        {/* Hero */}
        <header className="mb-12 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-sm text-violet-300">
            <Sparkles size={14} />
            Warsaw's Best Beauty Salons
          </div>
          <h1 className="text-5xl font-bold tracking-tight text-white sm:text-6xl">
            Warsaw{' '}
            <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
              Beauty
            </span>{' '}
            Explorer
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-zinc-400">
            Discover top-rated beauty salons across every district of Warsaw.
          </p>
        </header>

        {/* Search bar */}
        <div className="mx-auto mb-10 max-w-md">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500"
            />
            <input
              type="text"
              value={searchDistrict}
              onChange={(e) => setSearchDistrict(e.target.value)}
              placeholder="Filter by district (e.g. Mokotów)…"
              className="w-full rounded-2xl border border-white/10 bg-white/5 py-3.5 pl-11 pr-4 text-sm text-white placeholder-zinc-500 outline-none ring-0 backdrop-blur-sm transition-all duration-200 focus:border-violet-500/60 focus:bg-white/8 focus:ring-1 focus:ring-violet-500/30"
            />
          </div>
        </div>

        {/* Content */}
        {loading && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-36 animate-pulse rounded-2xl border border-white/5 bg-white/5"
              />
            ))}
          </div>
        )}

        {!loading && error && (
          <div className="mx-auto max-w-md rounded-2xl border border-red-500/30 bg-red-500/10 px-6 py-5 text-center text-sm text-red-300">
            {error}
          </div>
        )}

        {!loading && !error && salons.length === 0 && (
          <p className="text-center text-zinc-500">
            No salons found{searchDistrict ? ` in "${searchDistrict}"` : ''}.
          </p>
        )}

        {!loading && !error && salons.length > 0 && (
          <>
            <p className="mb-5 text-sm text-zinc-500">
              {salons.length} salon{salons.length !== 1 ? 's' : ''} found
              {searchDistrict ? ` in "${searchDistrict}"` : ''}
            </p>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {salons.map((salon) => (
                <SalonCard key={salon.id} salon={salon} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
