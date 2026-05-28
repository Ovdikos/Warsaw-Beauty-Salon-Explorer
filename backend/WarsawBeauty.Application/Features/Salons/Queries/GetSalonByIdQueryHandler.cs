using AutoMapper;
using MediatR;
using WarsawBeauty.Application.DTOs;
using WarsawBeauty.Application.Interfaces;

namespace WarsawBeauty.Application.Features.Salons.Queries;

public class GetSalonByIdQueryHandler : IRequestHandler<GetSalonByIdQuery, SalonDetailDto?>
{
    private readonly ISalonRepository _repository;
    private readonly IMapper _mapper;

    public GetSalonByIdQueryHandler(ISalonRepository repository, IMapper mapper)
    {
        _repository = repository;
        _mapper = mapper;
    }

    public async Task<SalonDetailDto?> Handle(GetSalonByIdQuery request, CancellationToken cancellationToken)
    {
        var salon = await _repository.GetSalonByIdAsync(request.Id);
        return salon is null ? null : _mapper.Map<SalonDetailDto>(salon);
    }
}
