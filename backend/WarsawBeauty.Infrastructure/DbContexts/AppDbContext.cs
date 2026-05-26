using Microsoft.EntityFrameworkCore;
using WarsawBeauty.Core.Entities;

namespace WarsawBeauty.Infrastructure.DbContexts;

/// <summary>
/// EF Core database context for the Warsaw Beauty SQLite database.
/// The connection string is injected via DbContextOptions from the API layer —
/// never hardcoded here to keep Infrastructure environment-agnostic.
/// </summary>
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<Salon> Salons { get; set; } = null!;
    public DbSet<Service> Services { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Salon>()
            .HasMany(s => s.Services)
            .WithOne(svc => svc.Salon)
            .HasForeignKey(svc => svc.SalonId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
