using AutoMapper;
using WarsawBeauty.Application.DTOs;
using WarsawBeauty.Core.Entities;

namespace WarsawBeauty.Application.Mappings;

public class MappingProfile : Profile
{
    public MappingProfile()
    {
        CreateMap<Salon, SalonListDto>();
        CreateMap<Salon, SalonDetailDto>();
        CreateMap<Service, ServiceDto>();
    }
}
