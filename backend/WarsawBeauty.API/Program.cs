using WarsawBeauty.API.Data;
using WarsawBeauty.API.Repositories;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();

// Register the SQLite AppDbContext. 
// Note: connection string is configured in AppDbContext.OnConfiguring
builder.Services.AddDbContext<AppDbContext>();

// Register the repository with the appropriate scoped lifetime
builder.Services.AddScoped<ISalonRepository, SalonRepository>();

// Configure CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// Configure the HTTP request pipeline strictly in the architectural order:

// 1. Exception Handler
if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
}
else
{
    app.UseExceptionHandler("/error");
}

// 2. HTTPS Redirection
app.UseHttpsRedirection();

// 3. Static Files
app.UseStaticFiles();

// 4. Routing
app.UseRouting();

// 5. CORS (Allow arbitrary origins for our upcoming React frontend integration)
app.UseCors("AllowAll");

// 6. Authorization
app.UseAuthorization();

// 7. Map Controllers (Endpoints execution)
app.MapControllers();

app.Run();
