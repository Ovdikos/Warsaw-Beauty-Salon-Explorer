using Microsoft.EntityFrameworkCore;
using WarsawBeauty.Core.Entities;
using WarsawBeauty.Core.Interfaces;
using WarsawBeauty.Infrastructure.DbContexts;

namespace WarsawBeauty.Infrastructure.Repositories;


public class SalonRepository : ISalonRepository
{
    private readonly AppDbContext _context;

    public SalonRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<IEnumerable<Salon>> GetSalonsAsync(string? district)
    {
        var query = _context.Salons.AsQueryable();

        if (!string.IsNullOrWhiteSpace(district))
        {
            query = query.Where(s => s.District.ToLower() == district.ToLower());
        }

        return await query.ToListAsync();
    }

    public async Task<Salon?> GetSalonByIdAsync(int id)
    {
        return await _context.Salons
            .Include(s => s.Services)
            .FirstOrDefaultAsync(s => s.Id == id);
    }

    public async Task UpdateSalonAsync(Salon salon)
    {
        _context.Salons.Update(salon);
        await _context.SaveChangesAsync();
    }
}
