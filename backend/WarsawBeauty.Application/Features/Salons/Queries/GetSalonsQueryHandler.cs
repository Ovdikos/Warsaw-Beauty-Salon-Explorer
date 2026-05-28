using AutoMapper;
using MediatR;
using WarsawBeauty.Application.DTOs;
using WarsawBeauty.Core.Interfaces;

namespace WarsawBeauty.Application.Features.Salons.Queries;

public class GetSalonsQueryHandler : IRequestHandler<GetSalonsQuery, IEnumerable<SalonDetailDto>>
{
    private readonly ISalonRepository _repository;
    private readonly IMapper _mapper;

    public GetSalonsQueryHandler(ISalonRepository repository, IMapper mapper)
    {
        _repository = repository;
        _mapper = mapper;
    }

    public async Task<IEnumerable<SalonDetailDto>> Handle(GetSalonsQuery request, CancellationToken cancellationToken)
    {
        var salons = await _repository.GetSalonsAsync(request.District);
        return _mapper.Map<IEnumerable<SalonDetailDto>>(salons);
    }
}
