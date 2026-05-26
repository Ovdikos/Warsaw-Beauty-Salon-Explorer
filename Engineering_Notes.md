# Engineering Notes: Warsaw Beauty Salon Explorer

This document outlines the technical decisions, architectural trade-offs, and data collection strategies made during the development of the Warsaw Beauty Salon Explorer.

## 1. Architectural Overview & Tech Stack

The application is built as a modular monolith, separated into distinct components to clearly divide responsibilities: data collection, data serving, and data presentation.

* **Data Collection:** Python 3 + Playwright (`asyncio`)
  * *Why:* Booksy is a heavily dynamic Single Page Application (SPA). Instead of trying to reverse-engineer undocumented and heavily protected private APIs, I chose Playwright to render the page and extract the embedded `application/ld+json` schema. Python's robust scraping ecosystem made this rapid to develop.
* **Database:** SQLite
  * *Why:* While MS SQL Server is my go-to for larger enterprise applications, the assignment highly values the ability for reviewers to run the project from scratch. SQLite eliminates the need to configure Docker containers or local database servers. It "just works" out of the box using a shared `.db` file between the Python scraper and the .NET backend.
* **Backend API:** .NET 8 (C#) & Entity Framework Core
  * *Why:* C# and ASP.NET Core provide a robust, strictly typed environment. To demonstrate enterprise-readiness, the backend is structured using **Clean Architecture** principles, ensuring high testability and clear separation of concerns.
* **Frontend UI:** React (TypeScript + Vite + TailwindCSS)
  * *Why:* React allows for building a simple, responsive, and component-driven UI quickly. TypeScript ensures that the data structures consumed from the .NET backend match the frontend expectations perfectly.

---

## 2. Data Collection Strategy (The "Booksy" Pivot)

Collecting high-quality data on local services was the most challenging and interesting part of this project.

### Targeting
Initially, I considered iterating over multiple service categories (hair, nails, massage). However, I realized the single category `salon-kosmetyczny` (beauty salon) in Warsaw alone contains over 3,600 businesses. To optimize the process, I pivoted to a pagination-based approach on a single category, appending `?businessesPage={page}` to gather URLs.

### Data Extraction & Fallbacks
* **JSON-LD Schema:** The primary source of truth is the hidden SEO schema (`application/ld+json`). It provides clean, structured data for the salon's name, address, services, and ratings, making the scraper highly resilient to UI/CSS changes.
* **The `__NUXT__` State Fallback:** When the JSON-LD schema occasionally omitted the list of services, relying on visual DOM parsing proved brittle. Instead, I utilized Playwright's native JS evaluation to extract the `window.__NUXT__` state, extracting the raw data exactly as the frontend framework sees it.

### Product Decision: The Phone Number Trade-off
During development, I discovered that Booksy actively hides salon phone numbers behind an authentication wall to retain users within their ecosystem. While it is technically possible to bypass this by utilizing Playwright's `storageState` with a dummy account, I made a conscious product decision to **drop this field**. 
* **Reasoning:** Implementing forced authentication would completely break the project's "run from scratch" requirement for users of this app. Maybe I will find a better way to do this in the future, but for now I have no time :)

### Performance & Fault Tolerance
A naive scraper would take hours and crash easily. I implemented three critical optimizations:
1. **Surgical Network Interception:** Playwright is configured to aggressively drop heavy requests (images, fonts, media) while allowing scripts and XHR through, making the page load incredibly fast without breaking the SPA.
2. **Controlled Concurrency:** Using `asyncio.Semaphore`, detail pages are fetched in controlled concurrent batches (5 at a time) to speed up extraction without overwhelming the target server.
3. **Idempotency (Resume Capability):** The script checks the SQLite database before processing a URL. If the execution is interrupted, it can be restarted and will safely skip already-saved salons, preventing duplicates.

---

## 3. Backend API Architecture (Clean Architecture)

To demonstrate scalable, enterprise-grade .NET development, I refactored the backend into a **Clean Architecture** structure. This separates the domain logic from the framework-specific implementations.

### Phase 1: The Core Layer (`WarsawBeauty.Core`)
This is the heart of the application. It contains zero dependencies on external frameworks (not even EF Core) and holds the Enterprise Entities and Repository Interfaces (`ISalonRepository`).

* **Explicit Schema Mapping:** The SQLite database is generated dynamically by an external Python scraper. To ensure bulletproof compatibility and prevent EF Core from relying on implicit "magic" conventions, I utilized strict Data Annotations (`[Table("salons")]`, `[Column("PriceRange")]`). This explicit mapping creates a rigid contract between the C# domain models and the physical database schema, eliminating runtime binding errors and making the data structure crystal clear to other developers.
* **Strict Entity Modeling:** Because the `PhoneNumber` was dropped during data collection, it was explicitly removed from the Domain Entities to prevent EF Core from throwing binding exceptions during database queries.

### Phase 2: The Infrastructure Layer (`WarsawBeauty.Infrastructure`)
This layer handles all Data Access implementations and depends on the Core layer.

* **Repository Pattern:** Instead of injecting `AppDbContext` directly into controllers, I implemented the Repository Pattern. This encapsulates the LINQ queries, decouples the database logic from the business logic, and makes the system highly unit-testable via Dependency Injection.
* **Query Optimization (Eager Loading):** To prevent the dreaded **N+1 query problem**, the `GetSalonByIdAsync` repository method uses explicit Eager Loading (`.Include(s => s.Services)`). This ensures the salon and its nested services are fetched in a single, optimized database roundtrip.
* **Environment-Agnostic Context:** Rather than hardcoding the SQLite connection string inside the `AppDbContext`, it is configured to accept `DbContextOptions` via Dependency Injection. The actual path is securely managed in `appsettings.json` and injected at runtime by the API layer.
