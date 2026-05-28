import type { SalonDetailDto, SalonListDto, SalonUpdateDto } from '../types';
import apiClient from './apiClient';

const salonService = {
  async getSalons(district?: string): Promise<SalonListDto[]> {
    const params = district ? { district } : undefined;
    const response = await apiClient.get<SalonListDto[]>('/salons', { params });
    return response.data;
  },

  async getSalonById(id: number): Promise<SalonDetailDto> {
    const response = await apiClient.get<SalonDetailDto>(`/salons/${id}`);
    return response.data;
  },

  async updateSalon(id: number, data: SalonUpdateDto): Promise<void> {
    await apiClient.put(`/salons/${id}`, data);
  },
};

export default salonService;