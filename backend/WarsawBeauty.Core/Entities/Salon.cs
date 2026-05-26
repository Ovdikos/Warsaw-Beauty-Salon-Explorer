using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace WarsawBeauty.Core.Entities;

[Table("Salons")]
public class Salon
{
    [Key]
    [Column("Id")]
    public int Id { get; set; }

    [Required]
    [Column("Name")]
    public string Name { get; set; } = null!;

    [Required]
    [Column("Address")]
    public string Address { get; set; } = null!;

    [Required]
    [Column("District")]
    public string District { get; set; } = null!;

    [Column("Website")]
    public string? Website { get; set; }

    [Column("PriceRange")]
    public string? PriceRange { get; set; }

    [Column("Rating")]
    public double? Rating { get; set; }

    [Column("ReviewCount")]
    public int? ReviewCount { get; set; }

    public ICollection<Service> Services { get; set; } = new List<Service>();
}
