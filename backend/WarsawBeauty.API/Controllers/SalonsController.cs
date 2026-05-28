using MediatR;
using Microsoft.AspNetCore.Mvc;
using WarsawBeauty.Application.DTOs;
using WarsawBeauty.Application.Features.Salons.Commands;
using WarsawBeauty.Application.Features.Salons.Queries;

namespace WarsawBeauty.API.Controllers;

[ApiController]
[Route("api/salons")]
public class SalonsController : ControllerBase
{
    private readonly IMediator _mediator;

    public SalonsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<SalonListDto>>> GetSalons([FromQuery] string? district)
    {
        var result = await _mediator.Send(new GetSalonsQuery(district));
        return Ok(result);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<SalonDetailDto>> GetSalonById(int id)
    {
        var result = await _mediator.Send(new GetSalonByIdQuery(id));
        return result is null ? NotFound() : Ok(result);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateSalon(int id, [FromBody] SalonUpdateDto dto)
    {
        await _mediator.Send(new UpdateSalonCommand(id, dto));
        return NoContent();
    }
}
