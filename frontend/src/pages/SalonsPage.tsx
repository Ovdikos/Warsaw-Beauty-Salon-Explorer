import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import SalonCard from '../components/SalonCard';
import salonService from '../services/salonService';
import type { SalonListDto } from '../types';

const ITEMS_PER_PAGE = 6;

export default function SalonsPage() {
  const [allSalons, setAllSalons] = useState<SalonListDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDistricts, setSelectedDistricts] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await salonService.getSalons();
        setAllSalons(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load salons.');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);


  const districts = useMemo(
    () => [...new Set(allSalons.map((s) => s.district))].sort(),
    [allSalons],
  );


  const filtered = useMemo(
    () =>
      selectedDistricts.size === 0
        ? allSalons
        : allSalons.filter((s) => selectedDistricts.has(s.district)),
    [allSalons, selectedDistricts],
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE));
  const paginated = filtered.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE);

  const toggleDistrict = (district: string) => {
    setSelectedDistricts((prev) => {
      const next = new Set(prev);
      next.has(district) ? next.delete(district) : next.add(district);
      return next;
    });
    setPage(1); // reset to first page on filter change
  };

  const clearFilters = () => {
    setSelectedDistricts(new Set());
    setPage(1);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#0f0f13] text-white">

      <div className="pointer-events-none fixed inset-x-0 top-0 h-64 bg-gradient-to-b from-rose-950/20 to-transparent" />

      <div className="relative mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 pb-16 pt-16 sm:px-6 lg:px-8">


        <header className="mb-14 text-center">
          <h1 className="text-5xl font-light tracking-tight text-white sm:text-6xl">
            Warsaw{' '}
            <em className="not-italic bg-gradient-to-r from-rose-400 to-fuchsia-400 bg-clip-text text-transparent font-semibold">
              Beauty
            </em>{' '}
            Explorer
          </h1>
        </header>


        <div className="flex flex-1 flex-col">

          {!loading && !error && districts.length > 0 && (
            <div className="mb-10">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-[11px] uppercase tracking-widest text-zinc-600">
                  Filter by district
                </span>
                {selectedDistricts.size > 0 && (
                  <button
                    onClick={clearFilters}
                    className="text-[11px] text-rose-400 hover:text-rose-300 transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {districts.map((district) => {
                  const active = selectedDistricts.has(district);
                  return (
                    <button
                      key={district}
                      onClick={() => toggleDistrict(district)}
                      className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition-all duration-200 ${
                        active
                          ? 'border-rose-500 bg-rose-500/15 text-rose-300'
                          : 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-600 hover:text-zinc-200'
                      }`}
                    >
                      {district}
                    </button>
                  );
                })}
              </div>
            </div>
          )}


          {!loading && !error && (
            <p className="mb-6 text-xs text-zinc-600">
              {filtered.length} salon{filtered.length !== 1 ? 's' : ''}
              {selectedDistricts.size > 0 && ` in ${[...selectedDistricts].join(', ')}`}
            </p>
          )}


          {loading && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-40 animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900/60"
                />
              ))}
            </div>
          )}


          {!loading && error && (
            <div className="mx-auto max-w-sm rounded-2xl border border-red-500/20 bg-red-500/10 px-6 py-5 text-center text-sm text-red-400">
              {error}
            </div>
          )}


          {!loading && !error && filtered.length === 0 && (
            <div className="py-20 text-center">
              <p className="text-zinc-600">No salons match the selected districts.</p>
              <button onClick={clearFilters} className="mt-3 text-sm text-rose-400 hover:text-rose-300 transition-colors">
                Clear filters
              </button>
            </div>
          )}


          {!loading && !error && paginated.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {paginated.map((salon) => (
                <SalonCard key={salon.id} salon={salon} />
              ))}
            </div>
          )}


          {!loading && !error && totalPages > 1 && (
            <div className="mt-auto pt-16 flex items-center justify-center gap-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-zinc-800 bg-zinc-900 text-zinc-400 transition-all hover:border-zinc-600 hover:text-white disabled:pointer-events-none disabled:opacity-30"
              >
                <ChevronLeft size={16} />
              </button>

              <span className="text-[11px] font-medium tracking-widest text-zinc-500 uppercase">
                Page <span className="text-zinc-200">{page}</span> of {totalPages}
              </span>

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-zinc-800 bg-zinc-900 text-zinc-400 transition-all hover:border-zinc-600 hover:text-white disabled:pointer-events-none disabled:opacity-30"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
