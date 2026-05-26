using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace WarsawBeauty.API.Models;

/// <summary>
/// Represents a service offered by a beauty salon, mapped to the SQLite database.
/// </summary>
[Table("Services")]
public class Service
{
    [Key]
    public int Id { get; set; }

    [Required]
    public int SalonId { get; set; }

    [Required]
    public string Name { get; set; } = null!;

    [Required]
    public decimal Price { get; set; }

    /// <summary>
    /// Navigation property back to the salon.
    /// </summary>
    [ForeignKey(nameof(SalonId))]
    public Salon Salon { get; set; } = null!;
}
