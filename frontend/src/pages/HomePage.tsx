import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import apiClient from "../services/api";
import { Category } from "../types";
import styles from "./HomePage.module.css";

const HomePage: React.FC = () => {
  console.log("--- HomePage KOMPONENT STARTUJE ---");
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log("--- useEffect w HomePage wystartował ---");

    const fetchCategories = async () => {
      console.log("--- fetchCategories: Rozpoczynam próbę pobrania danych ---");
      try {
        console.log("--- fetchCategories: Ustawiam loading na true ---");
        setLoading(true);
        setError(null);

        console.log(
          '--- fetchCategories: Wywołuję apiClient.get("/categories/") ---'
        );
        const response = await apiClient.get<Category[]>("/categories/");
        console.log(
          "--- fetchCategories: Otrzymano odpowiedź API ---",
          response.data
        );

        console.log("--- fetchCategories: Ustawiam stan categories ---");
        setCategories(response.data);
      } catch (err) {
        console.error(
          "--- fetchCategories: BŁĄD podczas pobierania kategorii! ---",
          err
        );
        setError("Nie udało się załadować kategorii.");
      } finally {
        console.log(
          "--- fetchCategories: Blok finally - ustawiam loading na false ---"
        );
        setLoading(false);
      }
    };

    fetchCategories();

    console.log(
      "--- useEffect w HomePage zakończył definicję i wywołanie fetchCategories ---"
    );
  }, []);

  return (
    <div className={styles.homeContainer}>
      <h1>Mistrzostwa Europy Kettlebell - Wyniki na Żywo</h1>
      <p className={styles.introText}>
        Witaj na stronie wyników! Wybierz kategorię poniżej, aby zobaczyć
        aktualne rezultaty zawodników.
      </p>

      <h2>Dostępne Kategorie:</h2>

      {loading && <div className="loading-message">Ładowanie kategorii...</div>}
      {error && <div className="error-message">{error}</div>}

      {!loading && !error && (
        <div className={styles.categoryList}>
          {categories.length > 0 ? (
            categories.map((category) => (
              <Link
                key={category.id}
                to={`/category/${category.id}`}
                className={styles.categoryLink}
              >
                {category.name}
                {category.disciplines && (
                  <span className={styles.categoryDisciplines}>
                    ({category.disciplines.join(", ")})
                  </span>
                )}
              </Link>
            ))
          ) : (
            <p>Brak dostępnych kategorii do wyświetlenia.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default HomePage;
