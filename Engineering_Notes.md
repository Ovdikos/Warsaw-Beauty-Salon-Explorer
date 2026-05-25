# Engineering Notes: Warsaw Beauty Salon Explorer

This document outlines the technical decisions, architectural trade-offs, and data collection strategies made during the development of the Warsaw Beauty Salon Explorer.

## 1. Architectural Overview & Tech Stack

The application is built as a modular monolith, separated into three distinct components to clearly divide responsibilities: data collection, data serving, and data presentation.

* **Data Collection:** Python 3 + Playwright (`asyncio`)
  * *Why:* Booksy is a heavily dynamic Single Page Application (SPA). Instead of trying to reverse-engineer undocumented and heavily protected private APIs, I chose Playwright to render the page and extract the embedded `application/ld+json` schema. Python's robust scraping ecosystem made this rapid to develop.
* **Database:** SQLite
  * *Why:* While PostgreSQL is my go-to for production applications, the assignment highly values the ability for reviewers to run the project from scratch. SQLite eliminates the need to configure Docker containers or local database servers. It "just works" out of the box using a shared `.db` file between the Python scraper and the .NET backend.
* **Backend API:** .NET 8 (C#) & Entity Framework Core
  * *Why:* C# and ASP.NET Core provide a robust, strictly typed environment for building REST APIs. It ensures data integrity and allows for clean, readable code structure (Controllers, DTOs, Models) without unnecessary boilerplate.
* **Frontend UI:** React (TypeScript + Vite + TailwindCSS)
  * *Why:* React allows for building a simple, responsive, and component-driven UI quickly. TypeScript ensures that the data structures consumed from the .NET backend match the frontend expectations perfectly.

---

## 2. Data Collection Strategy (The "Booksy" Pivot)

Collecting high-quality data on local services was the most challenging and interesting part of this project.

### Targeting
Initially, I considered iterating over multiple service categories (hair, nails, massage). However, I realized the single category `salon-kosmetyczny` (beauty salon) in Warsaw alone contains over 3,600 businesses. To optimize the process, I pivoted to a pagination-based approach on a single category, appending `?businessesPage={page}` to gather URLs.

### Data Extraction
* **JSON-LD Schema:** The primary source of truth is the hidden SEO schema (`application/ld+json`). It provides clean, structured data for the salon's name, address, services, and ratings, making the scraper highly resilient to UI/CSS changes.
* **DOM Inspection:** Phone numbers were often omitted from the JSON-LD schema. To fulfill the "nice to have" requirement, I implemented targeted DOM extraction using Playwright's specific test IDs (e.g., `data-testid="business-contact-info-phone"`) from the visual sidebar.

### Performance & Fault Tolerance
A naive scraper would take hours and crash easily. I implemented three critical optimizations:

1. **Network Interception:** Playwright is configured to aggressively drop all requests for images, fonts, and stylesheets, downloading only the raw HTML.
2. **Concurrency:** Using `asyncio`, detail pages are fetched in concurrent batches rather than sequentially.
3. **Idempotency (Resume Capability):** The script checks the SQLite database before processing a URL. If the execution is interrupted, it can be restarted and will safely skip already-saved salons.
