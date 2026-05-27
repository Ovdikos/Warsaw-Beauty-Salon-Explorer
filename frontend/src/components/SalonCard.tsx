import { MapPin, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { SalonListDto } from '../types';

interface SalonCardProps {
  salon: SalonListDto;
}

export default function SalonCard({ salon }: SalonCardProps) {
  return (
    <Link
      to={`/salons/${salon.id}`}
      className="group relative flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 backdrop-blur-sm transition-all duration-300 hover:border-rose-500/50 hover:shadow-[0_0_24px_rgba(225,29,72,0.12)]"
    >

      {salon.priceRange && (
        <span className="absolute right-4 top-4 rounded-full bg-zinc-800 px-2.5 py-0.5 text-[11px] font-medium tracking-wide text-zinc-400">
          {salon.priceRange}
        </span>
      )}


      <h3 className="mb-3 pr-12 text-[15px] font-semibold leading-snug text-white transition-colors duration-200 group-hover:text-rose-300">
        {salon.name}
      </h3>


      <div className="mb-auto flex items-center gap-1.5 text-xs text-zinc-500">
        <MapPin size={11} className="shrink-0 text-rose-500/70" />
        {salon.district}
      </div>


      <div className="mt-4 flex items-center justify-between border-t border-zinc-800 pt-3">
        {salon.rating !== null ? (
          <div className="flex items-center gap-1.5">
            <Star size={13} className="fill-rose-400 text-rose-400" />
            <span className="text-sm font-medium text-zinc-200">
              {salon.rating.toFixed(1)}
            </span>
          </div>
        ) : (
          <span className="text-xs text-zinc-700">—</span>
        )}
        <span className="text-[11px] tracking-wide text-zinc-600 transition-colors duration-200 group-hover:text-rose-400">
          View →
        </span>
      </div>
    </Link>
  );
}
