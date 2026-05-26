using WarsawBeauty.Core.Entities;

namespace WarsawBeauty.Core.Interfaces;

public interface ISalonRepository
{
    /// <summary>Returns all salons, optionally filtered by district (case-insensitive).</summary>
    Task<IEnumerable<Salon>> GetSalonsAsync(string? district);

    /// <summary>Returns a single salon by primary key, including its services. Returns null if not found.</summary>
    Task<Salon?> GetSalonByIdAsync(int id);

    /// <summary>Persists changes to an existing salon record.</summary>
    Task UpdateSalonAsync(Salon salon);
}
