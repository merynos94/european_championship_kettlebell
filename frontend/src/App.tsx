import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import HomePage from "./pages/HomePage";
import CategoryPage from "./pages/CategoryPage";
import LivePage from "./pages/LivePage";
import ContactPage from "./pages/ContactPage";
import Layout from "./components/Layout";
import "./index.css";

function App() {
  useEffect(() => {
    document.title = "European Kettlebell Championship";
  }, []);
  
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="category/:categoryId" element={<CategoryPage />} />
          <Route path="live" element={<LivePage />} />
          <Route path="contact" element={<ContactPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;