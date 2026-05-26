using WarsawBeauty.API.Models;

namespace WarsawBeauty.API.Repositories;

public interface ISalonRepository
{
    Task<IEnumerable<Salon>> GetSalonsAsync(string? district);
    Task<Salon?> GetSalonByIdAsync(int id);
    Task UpdateSalonAsync(Salon salon);
}
