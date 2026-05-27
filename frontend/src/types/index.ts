export interface ServiceDto {
  id: number;
  name: string;
  price: number;
}

export interface SalonListDto {
  id: number;
  name: string;
  district: string;
  rating: number | null;
  priceRange: string | null;
}

export interface SalonDetailDto {
  id: number;
  name: string;
  address: string;
  district: string;
  website: string | null;
  priceRange: string | null;
  rating: number | null;
  reviewCount: number | null;
  services: ServiceDto[];
}

export interface SalonUpdateDto {
  address: string;
  website: string | null;
}
