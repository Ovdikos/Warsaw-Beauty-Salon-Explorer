using WarsawBeauty.Core.Entities;

namespace WarsawBeauty.Application.Interfaces;

public interface ISalonRepository
{
    Task<IEnumerable<Salon>> GetSalonsAsync(string? district);

    Task<Salon?> GetSalonByIdAsync(int id);

    Task UpdateSalonAsync(Salon salon);
}
