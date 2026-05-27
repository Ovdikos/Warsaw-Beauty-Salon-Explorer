import { Route, Routes } from 'react-router-dom';
import SalonsPage from './pages/SalonsPage';
import SalonDetailsPage from './pages/SalonDetailsPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SalonsPage />} />
      <Route path="/salons/:id" element={<SalonDetailsPage />} />
    </Routes>
  );
}
