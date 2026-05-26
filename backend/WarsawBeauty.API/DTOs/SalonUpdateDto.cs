using System.ComponentModel.DataAnnotations;

namespace WarsawBeauty.API.DTOs;

public class SalonUpdateDto
{
    [Required]
    public string Address { get; set; } = null!;
    
    public string? Website { get; set; }
}
