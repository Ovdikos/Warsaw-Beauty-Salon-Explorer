using MediatR;
using WarsawBeauty.Application.DTOs;

namespace WarsawBeauty.Application.Features.Salons.Queries;

public record GetSalonByIdQuery(int Id) : IRequest<SalonDetailDto?>;
