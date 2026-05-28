import type { SalonDetailDto, SalonListDto, SalonUpdateDto } from '../types';
import apiClient from './apiClient';

const salonService = {
  async getSalons(district?: string): Promise<SalonListDto[]> {
    if (import.meta.env.DEV) {
      // for localhost
      const params = district ? { district } : undefined;
      const response = await apiClient.get<SalonListDto[]>('/salons', { params });
      return response.data;
    } else {
      // for production
      const response = await fetch(`${import.meta.env.BASE_URL}data/salons.json`);
      if (!response.ok) throw new Error('Failed to load static salons data');
      let data: SalonListDto[] = await response.json();
      if (district) {
        data = data.filter((s) => s.district === district);
      }
      return data;
    }
  },

  async getSalonById(id: number): Promise<SalonDetailDto> {
    if (import.meta.env.DEV) {
      // for localhost
      const response = await apiClient.get<SalonDetailDto>(`/salons/${id}`);
      return response.data;
    } else {
      // for production
      const response = await fetch(`${import.meta.env.BASE_URL}data/salons.json`);
      if (!response.ok) throw new Error('Failed to load static salon data');
      const data: SalonDetailDto[] = await response.json();
      const salon = data.find((s) => s.id === id);
      if (!salon) throw new Error('Salon not found');
      return salon;
    }
  },

  async updateSalon(id: number, data: SalonUpdateDto): Promise<void> {
    if (import.meta.env.DEV) {
      // for localhost
      await apiClient.put(`/salons/${id}`, data);
    } else {
      // for production
      await new Promise(r => setTimeout(r, 500));
      console.log('Updated salon:', id, 'with data:', data);
      return Promise.resolve();
    }
  },
};

export default salonService;
