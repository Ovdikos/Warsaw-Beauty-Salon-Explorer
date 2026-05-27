import { MapPin, Star, Tag } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { SalonListDto } from '../types';

interface SalonCardProps {
  salon: SalonListDto;
}

export default function SalonCard({ salon }: SalonCardProps) {
  return (
    <Link
      to={`/salons/${salon.id}`}
      className="group block rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-violet-500/50 hover:bg-white/10 hover:shadow-xl hover:shadow-violet-900/30"
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <h3 className="text-base font-semibold leading-snug text-white group-hover:text-violet-300 transition-colors duration-200">
          {salon.name}
        </h3>
        {salon.priceRange && (
          <span className="shrink-0 rounded-full bg-violet-500/20 px-2.5 py-0.5 text-xs font-medium text-violet-300 flex items-center gap-1">
            <Tag size={11} />
            {salon.priceRange}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1.5 text-sm text-zinc-400 mb-4">
        <MapPin size={13} className="shrink-0 text-violet-400" />
        <span>{salon.district}</span>
      </div>

      <div className="flex items-center justify-between">
        {salon.rating !== null ? (
          <div className="flex items-center gap-1.5">
            <Star size={14} className="fill-amber-400 text-amber-400" />
            <span className="text-sm font-medium text-amber-300">
              {salon.rating.toFixed(1)}
            </span>
          </div>
        ) : (
          <span className="text-xs text-zinc-600">No rating</span>
        )}
        <span className="text-xs text-zinc-500 group-hover:text-violet-400 transition-colors duration-200">
          View details →
        </span>
      </div>
    </Link>
  );
}
