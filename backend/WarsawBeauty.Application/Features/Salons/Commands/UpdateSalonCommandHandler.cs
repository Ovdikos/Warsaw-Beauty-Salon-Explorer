using MediatR;
using WarsawBeauty.Application.Interfaces;

namespace WarsawBeauty.Application.Features.Salons.Commands;

public class UpdateSalonCommandHandler : IRequestHandler<UpdateSalonCommand>
{
    private readonly ISalonRepository _repository;

    public UpdateSalonCommandHandler(ISalonRepository repository)
    {
        _repository = repository;
    }

    public async Task Handle(UpdateSalonCommand request, CancellationToken cancellationToken)
    {
        var salon = await _repository.GetSalonByIdAsync(request.Id)
            ?? throw new KeyNotFoundException($"Salon with id {request.Id} was not found.");

        salon.Address = request.Dto.Address;
        salon.Website = request.Dto.Website;

        await _repository.UpdateSalonAsync(salon);
    }
}
