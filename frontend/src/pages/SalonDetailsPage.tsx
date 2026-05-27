import { useState, useEffect } from 'react';
import { ArrowLeft, ExternalLink, MapPin, Pencil, Save, Star, X, Tag, Edit2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { Link, useParams } from 'react-router-dom';
import salonService from '../services/salonService';
import type { SalonDetailDto } from '../types';

interface FormState {
  address: string;
  website: string;
}

export default function SalonDetailsPage() {
  const { id } = useParams<{ id: string }>();

  const [salon, setSalon] = useState<SalonDetailDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState<FormState>({ address: '', website: '' });
  const [formError, setFormError] = useState<string | null>(null);

  const fetchSalon = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await salonService.getSalonById(Number(id));
      setSalon(data);
      setForm({ address: data.address, website: data.website ?? '' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load salon.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSalon();
  }, [id]);

  const handleEditToggle = () => {
    if (salon) {
      setForm({ address: salon.address, website: salon.website ?? '' });
    }
    setFormError(null);
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setFormError(null);
  };

  const handleSave = async () => {
    if (!form.address.trim()) {
      setFormError('Address is required.');
      return;
    }
    setFormError(null);
    setIsSaving(true);
    try {
      await salonService.updateSalon(Number(id), {
        address: form.address.trim(),
        website: form.website.trim() || null,
      });
      toast.success('Salon details updated.');
      setIsEditing(false);
      await fetchSalon();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Update failed.');
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col bg-[#0f0f13] p-8 pt-20">
        <div className="mx-auto w-full max-w-6xl animate-pulse space-y-8">
          <div className="h-4 w-24 rounded bg-zinc-800/50" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="min-h-[600px] rounded-3xl bg-zinc-800/30" />
            <div className="min-h-[600px] rounded-3xl bg-zinc-800/30" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !salon) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0f0f13]">
        <div className="text-center">
          <p className="mb-4 text-sm text-red-400">{error ?? 'Salon not found.'}</p>
          <Link to="/" className="text-sm font-medium text-rose-400 transition-colors hover:text-rose-300">
            ← Return to collection
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f0f13] text-white flex flex-col items-center justify-center relative">
      {/* Ambient background gradients */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -right-40 -top-40 h-[600px] w-[600px] rounded-full bg-rose-950/10 blur-[140px]" />
        <div className="absolute top-1/3 -left-40 h-[500px] w-[500px] rounded-full bg-fuchsia-950/10 blur-[120px]" />
      </div>

      <div className="relative z-10 w-full max-w-6xl px-4 py-16 flex flex-col justify-center min-h-screen">
        {/* Navigation */}
        <div className="mb-8">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-[11px] font-medium uppercase tracking-widest text-zinc-500 transition-colors hover:text-rose-400"
          >
            <ArrowLeft size={14} />
            Back to collection
          </Link>
        </div>

        {/* 50/50 Symmetrical Bento Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch w-full">

          {/* Left Block: Premium Salon Info & Actions */}
          <div className="rounded-3xl border border-white/5 bg-zinc-900/30 p-8 sm:p-10 backdrop-blur-md flex flex-col justify-between min-h-[600px]">
            <div className="flex flex-col gap-6">
              {/* Header (No line clamp, flows naturally) */}
              <h1 className="text-3xl lg:text-4xl font-bold tracking-tight text-white leading-tight">
                {salon.name}
              </h1>

              {/* Badges / Metrics */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-1.5 rounded-full border border-zinc-800 bg-zinc-900/80 px-3 py-1.5">
                  <MapPin size={13} className="text-rose-500/70" />
                  <span className="text-[11px] font-medium tracking-wide text-zinc-300">
                    {salon.district}
                  </span>
                </div>

                {salon.rating !== null && (
                  <div className="flex items-center gap-1.5 rounded-full border border-zinc-800 bg-zinc-900/80 px-3 py-1.5">
                    <Star size={13} className="fill-rose-400 text-rose-400" />
                    <span className="text-[11px] font-medium text-zinc-200">
                      {salon.rating.toFixed(1)}
                    </span>
                    {salon.reviewCount !== null && (
                      <span className="text-[10px] text-zinc-500 ml-0.5">
                        ({salon.reviewCount})
                      </span>
                    )}
                  </div>
                )}

                {salon.priceRange && (
                  <div className="flex items-center gap-1.5 rounded-full border border-zinc-800 bg-zinc-900/80 px-3 py-1.5">
                    <Tag size={13} className="text-zinc-500" />
                    <span className="text-[11px] font-medium tracking-wide text-zinc-300">
                      {salon.priceRange}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Contact & Edit Section */}
            <div className="mt-auto border-t border-white/5 pt-8">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-zinc-500">
                  <Edit2 size={13} className="text-rose-500/70" />
                  Contact Details
                </h2>
                {!isEditing && (
                  <button
                    onClick={handleEditToggle}
                    className="group flex h-8 w-8 items-center justify-center rounded-full bg-zinc-800/50 text-zinc-400 transition-all hover:bg-rose-500/10 hover:text-rose-400"
                    title="Edit Details"
                  >
                    <Pencil size={13} className="transition-transform group-hover:scale-110" />
                  </button>
                )}
              </div>

              {isEditing ? (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                  <div>
                    <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
                      Address <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.address}
                      onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                      className="w-full rounded-xl border border-zinc-800 bg-[#0f0f13]/80 px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition-all focus:border-rose-500/40 focus:bg-[#0f0f13] focus:ring-1 focus:ring-rose-500/20"
                      placeholder="Enter full address…"
                    />
                    {formError && (
                      <p className="mt-1.5 text-[10px] font-medium text-rose-500">{formError}</p>
                    )}
                  </div>

                  <div>
                    <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
                      Website <span className="text-zinc-600">(Optional)</span>
                    </label>
                    <input
                      type="url"
                      value={form.website}
                      onChange={(e) => setForm((f) => ({ ...f, website: e.target.value }))}
                      className="w-full rounded-xl border border-zinc-800 bg-[#0f0f13]/80 px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition-all focus:border-rose-500/40 focus:bg-[#0f0f13] focus:ring-1 focus:ring-rose-500/20"
                      placeholder="https://…"
                    />
                  </div>

                  <div className="flex items-center gap-3 pt-2">
                    <button
                      onClick={handleSave}
                      disabled={isSaving}
                      className="flex-1 flex justify-center items-center gap-2 rounded-xl bg-rose-900/40 border border-rose-500/30 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-widest text-rose-300 transition-all hover:bg-rose-900/60 disabled:pointer-events-none disabled:opacity-50"
                    >
                      <Save size={14} />
                      {isSaving ? 'Saving' : 'Save'}
                    </button>
                    <button
                      onClick={handleCancel}
                      disabled={isSaving}
                      className="flex justify-center items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-widest text-zinc-400 transition-all hover:bg-zinc-800 hover:text-white disabled:pointer-events-none disabled:opacity-50"
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h3 className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
                      Address
                    </h3>
                    <p className="text-sm font-light leading-relaxed text-zinc-300">
                      {salon.address}
                    </p>
                  </div>
                  <div>
                    <h3 className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
                      Website
                    </h3>
                    <div>
                      {salon.website ? (
                        <a
                          href={salon.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group inline-flex items-center gap-2 text-sm font-light text-rose-400 transition-colors hover:text-rose-300"
                        >
                          Visit online
                          <ExternalLink size={13} className="transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                        </a>
                      ) : (
                        <span className="text-sm font-light italic text-zinc-600">Not provided</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Block: Premium Symmetrical Services Menu */}
          <div className="rounded-3xl border border-white/5 bg-zinc-900/30 p-8 sm:p-10 backdrop-blur-md flex flex-col min-h-[600px] max-h-[600px]">
            <h2 className="mb-6 text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
              Services Menu
            </h2>

            {salon.services.length === 0 ? (
              <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-zinc-800 p-8">
                <p className="text-sm italic text-zinc-600">No services listed.</p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto pr-4 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-zinc-800 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-700">
                <ul className="flex flex-col">
                  {salon.services.map((svc, idx) => (
                    <li
                      key={svc.id}
                      className={`group flex items-center justify-between py-4 transition-colors hover:bg-white/[0.02] ${idx !== 0 ? 'border-t border-zinc-800/40' : ''
                        }`}
                    >
                      <span className="pr-4 text-[14px] font-light text-zinc-300 group-hover:text-white transition-colors">
                        {svc.name}
                      </span>

                      <span className="pl-4 text-[14px] font-medium tracking-wide text-rose-400 whitespace-nowrap">
                        {svc.price.toFixed(2)} <span className="text-[10px] text-rose-500/50 ml-0.5 uppercase tracking-wider">PLN</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
