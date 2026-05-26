using MediatR;
using WarsawBeauty.Application.DTOs;

namespace WarsawBeauty.Application.Features.Salons.Commands;

public record UpdateSalonCommand(int Id, SalonUpdateDto Dto) : IRequest;
