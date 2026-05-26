using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using WarsawBeauty.Core.Interfaces;
using WarsawBeauty.Infrastructure.DbContexts;
using WarsawBeauty.Infrastructure.Repositories;

namespace WarsawBeauty.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, string connectionString)
    {
        services.AddDbContext<AppDbContext>(options =>
            options.UseSqlite(connectionString));

        services.AddScoped<ISalonRepository, SalonRepository>();

        return services;
    }
}
