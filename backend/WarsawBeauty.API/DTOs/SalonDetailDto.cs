namespace WarsawBeauty.API.DTOs;

public class SalonDetailDto
{
    public int Id { get; set; }
    public string Name { get; set; } = null!;
    public string Address { get; set; } = null!;
    public string District { get; set; } = null!;
    public string? Website { get; set; }
    public string? PriceRange { get; set; }
    public double? Rating { get; set; }
    public int? ReviewCount { get; set; }
    
    public ICollection<ServiceDto> Services { get; set; } = new List<ServiceDto>();
}
