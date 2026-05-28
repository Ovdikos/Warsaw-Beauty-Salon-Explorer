using MediatR;
using WarsawBeauty.Application.DTOs;

namespace WarsawBeauty.Application.Features.Salons.Queries;

public record GetSalonsQuery(string? District) : IRequest<IEnumerable<SalonDetailDto>>;
