using Microsoft.EntityFrameworkCore;
using WarsawBeauty.API.Models;

namespace WarsawBeauty.API.Data;

/// <summary>
/// Entity Framework Core context for accessing the Warsaw Beauty SQLite database.
/// </summary>
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<Salon> Salons { get; set; } = null!;
    public DbSet<Service> Services { get; set; } = null!;

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        if (!optionsBuilder.IsConfigured)
        {
            // Pointing to the SQLite DB relative to the backend folder
            // The API runs from backend/WarsawBeauty.API/ bin directory, but we can set it to connect relative to the project root.
            optionsBuilder.UseSqlite("Data Source=../../data/salons.db");
        }
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configure the one-to-many relationship explicitly
        modelBuilder.Entity<Salon>()
            .HasMany(s => s.Services)
            .WithOne(svc => svc.Salon)
            .HasForeignKey(svc => svc.SalonId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
