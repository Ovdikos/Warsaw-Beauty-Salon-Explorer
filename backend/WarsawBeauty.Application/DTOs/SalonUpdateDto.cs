using System.ComponentModel.DataAnnotations;

namespace WarsawBeauty.Application.DTOs;

public class SalonUpdateDto
{
    [Required]
    public string Address { get; set; } = null!;

    public string? Website { get; set; }
}
