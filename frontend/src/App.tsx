import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import CategoryPage from "./pages/CategoryPage";
import Layout from "./components/Layout";
import "./index.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="category/:categoryId" element={<CategoryPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
