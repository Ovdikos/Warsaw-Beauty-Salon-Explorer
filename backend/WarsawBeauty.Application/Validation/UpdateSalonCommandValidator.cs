using FluentValidation;
using WarsawBeauty.Application.Features.Salons.Commands;

namespace WarsawBeauty.Application.Validation;

public class UpdateSalonCommandValidator : AbstractValidator<UpdateSalonCommand>
{
    public UpdateSalonCommandValidator()
    {
        RuleFor(x => x.Dto.Address)
            .NotEmpty().WithMessage("Address is required.");

        RuleFor(x => x.Dto.Website)
            .Must(BeAValidUrl).WithMessage("Website must be a valid URL.")
            .When(x => !string.IsNullOrWhiteSpace(x.Dto.Website));
    }

    private static bool BeAValidUrl(string? url)
    {
        return Uri.TryCreate(url, UriKind.Absolute, out var result)
            && (result.Scheme == Uri.UriSchemeHttp || result.Scheme == Uri.UriSchemeHttps);
    }
}
