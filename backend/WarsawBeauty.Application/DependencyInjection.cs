using FluentValidation;
using MediatR;
using Microsoft.Extensions.DependencyInjection;
using WarsawBeauty.Application.Behaviors;
using WarsawBeauty.Application.Mappings;

namespace WarsawBeauty.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        // AutoMapper 16 natively supports assembly scanning via AddAutoMapper
        services.AddAutoMapper(cfg => cfg.AddMaps(typeof(MappingProfile).Assembly));

        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly);
            cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
        });

        services.AddValidatorsFromAssemblyContaining<MappingProfile>();

        return services;
    }
}
