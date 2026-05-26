using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace WarsawBeauty.API.Models;

[Table("Services")]
public class Service
{
    [Key]
    [Column("Id")]
    public int Id { get; set; }

    [Required]
    [Column("SalonId")]
    public int SalonId { get; set; }

    [Required]
    [Column("Name")]
    public string Name { get; set; } = null!;

    [Required]
    [Column("Price")]
    public decimal Price { get; set; }

    [ForeignKey(nameof(SalonId))]
    public Salon Salon { get; set; } = null!;
}
