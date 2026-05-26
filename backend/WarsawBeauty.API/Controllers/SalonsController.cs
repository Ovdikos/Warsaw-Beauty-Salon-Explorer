using Microsoft.AspNetCore.Mvc;
using WarsawBeauty.API.DTOs;
using WarsawBeauty.API.Repositories;

namespace WarsawBeauty.API.Controllers;

[ApiController]
[Route("api/salons")]
public class SalonsController : ControllerBase
{
    private readonly ISalonRepository _repository;

    public SalonsController(ISalonRepository repository)
    {
        _repository = repository;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<SalonListDto>>> GetSalons([FromQuery] string? district)
    {
        var salons = await _repository.GetSalonsAsync(district);

        // Map the entities to a collection of SalonListDto
        var dtos = salons.Select(s => new SalonListDto
        {
            Id = s.Id,
            Name = s.Name,
            District = s.District,
            Rating = s.Rating,
            PriceRange = s.PriceRange
        });

        return Ok(dtos);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<SalonDetailDto>> GetSalonById(int id)
    {
        // The repository uses Eager Loading (.Include(s => s.Services))
        var salon = await _repository.GetSalonByIdAsync(id);

        if (salon == null)
        {
            return NotFound();
        }

        var dto = new SalonDetailDto
        {
            Id = salon.Id,
            Name = salon.Name,
            Address = salon.Address,
            District = salon.District,
            Website = salon.Website,
            PriceRange = salon.PriceRange,
            Rating = salon.Rating,
            ReviewCount = salon.ReviewCount,
            Services = salon.Services.Select(svc => new ServiceDto
            {
                Id = svc.Id,
                Name = svc.Name,
                Price = svc.Price
            }).ToList()
        };

        return Ok(dto);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateSalon(int id, [FromBody] SalonUpdateDto updateDto)
    {
        var salon = await _repository.GetSalonByIdAsync(id);

        if (salon == null)
        {
            return NotFound();
        }

        // Update only the allowed editable fields
        salon.Address = updateDto.Address;
        salon.Website = updateDto.Website;

        await _repository.UpdateSalonAsync(salon);

        return NoContent();
    }
}
