namespace WarsawBeauty.Application.DTOs;

public class SalonListDto
{
    public int Id { get; set; }
    public string Name { get; set; } = null!;
    public string District { get; set; } = null!;
    public double? Rating { get; set; }
    public string? PriceRange { get; set; }
}
