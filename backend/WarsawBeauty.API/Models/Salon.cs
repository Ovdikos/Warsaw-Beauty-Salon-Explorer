using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace WarsawBeauty.API.Models;

/// <summary>
/// Represents a beauty salon mapped to the SQLite database.
/// </summary>
[Table("Salons")]
public class Salon
{
    [Key]
    public int Id { get; set; }

    [Required]
    public string Name { get; set; } = null!;

    [Required]
    public string Address { get; set; } = null!;

    [Required]
    public string District { get; set; } = null!;

    public string? Website { get; set; }

    public string? PriceRange { get; set; }

    public double? Rating { get; set; }

    public int? ReviewCount { get; set; }

    /// <summary>
    /// Navigation property for the salon's services.
    /// </summary>
    public ICollection<Service> Services { get; set; } = new List<Service>();
}
