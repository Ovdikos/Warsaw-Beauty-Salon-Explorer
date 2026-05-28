# Warsaw Beauty Salon Explorer

This application is built as part of the home task for the **SumUp Warsaw Accelerator Program (Software Engineer Intern)**. It represents a full-stack local services platform that crawls, cleanses, indexes, and beautifully presents data from over 100 beauty salons across Warsaw.

---

## 1. How to Run the Application

You can experience the application in two ways: via the live production demo or by spinning up the full-stack architecture locally.

### Option A: Live Production Demo (Instant Access)
If you want to immediately explore the user interface and interact with the application without cloning any code or setting up local environments, you can access the pre-deployed version hosted on the university server:

👉 **Live URL:** [https://users.pja.edu.pl/~s30920](https://users.pja.edu.pl/~s30920)

*Note: Since the university user hosting platform is optimized for static file delivery, backend write operations (such as saving changes in the salon edit mode) are seamlessly simulated client-side with realistic network delays and notifications in this live preview.*

### Option B: Local Full-Stack Deployment (From Source)
To run the full live system with the active .NET 8 backend API and persistent SQLite database, follow these steps:

#### Prerequisites
* **.NET 8.0 SDK** installed on your machine.
* **Node.js** (v18.0 or higher) and **npm**.
* **Git** for repository cloning.

#### Step 1: Create a folder
```bash
mkdir warsaw-beauty-salon-explorer
cd warsaw-beauty-salon-explorer
```

#### Step 2: Clone the Repository

```bash
git clone https://github.com/Ovdikos/Warsaw-Beauty-Salon-Explorer .
```

#### Step 3: Spin Up the Backend API
Navigate to the API project directory and run the .NET application. The backend will automatically bind to the SQLite database file located in the data/ folder and establish local endpoints.

```bash
cd backend/WarsawBeauty.API
dotnet run
```

#### Step 4: Spin Up the Frontend Development Server
Open a new terminal window, navigate to the frontend directory, install dependencies, and start the Vite development server

```bash
cd frontend
npm install
npm run dev
```

Once started, open your browser and go to the local address displayed in your terminal (http://localhost:5173) to experience the fully functional system with write capabilities.

---

## 2. Technical Solution & Frameworks Used
The application is built as a modular monolith with three completely decoupled layers:

#### 1. Data Collection (Scraper): Python 3 + Playwright for asynchronous headless scraping and DOM state extraction, storing cleansed data in SQLite.

#### 2. Backend API: C# / .NET 8 structured with Clean Architecture. It utilizes CQRS via MediatR, FluentValidation for fail-fast requests, global exception handling (RFC 7807), and Entity Framework Core.

#### 3. Frontend UI: React 19 + TypeScript + Vite, styled with Tailwind CSS v4. Features a responsive, symmetrical "Bento Box" design system and centralized domain services (Axios).

> 📖 **Deep-Dive Documentation:** This section is kept intentionally brief. For a detailed breakdown of architectural decisions, schema design, network optimizations, and the product trade-offs made during development, please refer to the **[Engineering_Notes.md](./Engineering_Notes.md)**.

---

## 3. What I'd Improve with More Time
If given more time to evolve this prototype into a production-grade SaaS product, I would focus on the following product and engineering enhancements:

* **Geospatial Search & Interactive Mapping (UX & Product):** Transition from a purely list-based explorer to a map-centric UI integrating Mapbox or Google Maps API. On the backend, I would migrate from SQLite to PostgreSQL with PostGIS to support advanced spatial queries ("find salons within a 3km radius").

* **Business Authorization & Profile "Claiming" (Security):** Currently, API endpoints are open to facilitate easy local testing. For production, I would implement JWT-based authentication with RBAC. Specifically, I would introduce a "Claim your business" flow (similar to Google My Business), ensuring that only verified salon owners can modify their services and pricing.

* **Scaling Data Collection (Data Engineering):** While the current Playwright scraper works flawlessly for a local Warsaw dataset, scaling it to index 10,000+ salons across Poland requires a stronger setup. I would add proxies to prevent the scraper from being blocked by websites. I would also schedule automatic weekly updates so that salon prices and data are always kept fresh and accurate.

* **Comprehensive QA & Containerization (DevOps):** Introduce robust automated testing by covering the .NET API with unit/integration tests using xUnit and Moq, and the React frontend with End-to-End UI tests. Additionally, I would fully containerize the application using Docker Compose (DB + API + UI) and configure a CI/CD pipeline via GitHub Actions for seamless deployment.
