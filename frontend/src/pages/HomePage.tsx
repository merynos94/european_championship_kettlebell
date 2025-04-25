import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Category } from "../types";
import apiClient from "../services/api";
import styles from "./HomePage.module.css";
import { Typography, Space, Card, Spin, Alert } from "antd";
const { Title, Paragraph } = Typography;


interface GroupedCategories {
  Amateur: Category[];
  Pro: Category[];
  Najlepszy: Category[];
  Master: Category[];
  U16: Category[];
}

const categoryGroupConfig: { key: keyof GroupedCategories; title: string; keywords: string[] }[] = [

  { key: 'U16', title: 'Junior 16 / U16', keywords: ['junior 16', 'u16', 'dziewcząt', 'chłopców', 'under 16'] },
  { key: 'Amateur', title: 'Amator / Amateur', keywords: ['amator', 'amateur'] },
  { key: 'Pro', title: 'Pro / Professional', keywords: ['pro', 'professional'] },
  { key: 'Master', title: 'Masters', keywords: ['master'] },
  { key: 'Najlepszy', title: 'Najlepszy / Best', keywords: ['najlepsz', 'local'] },
];

const HomePage: React.FC = () => {
  // --- Pobieranie Danych (bez zmian) ---
  const fetchCategories = async (): Promise<Category[]> => {
    try {
      const response = await apiClient.get<Category[]>("/categories/");
      // Proste sortowanie pobranych kategorii alfabetycznie od razu
      return response.data.sort((a, b) => a.name.localeCompare(b.name));
    } catch (error) {
      console.error("Error fetching categories:", error);
      throw error;
    }
  };

  const {
    data: categories = [],
    isLoading,
    isError,
    error,
    isFetching,
  } = useQuery<Category[], Error>({
    queryKey: ["categories"],
    queryFn: fetchCategories,
    staleTime: 60 * 1000 * 10, // 10 minut
  });

  // --- Grupowanie Kategorii (bez specjalnych przypadków ID) ---
  const groupedCategories = useMemo((): GroupedCategories => {
    // Inicjalizacja pustych grup
    const groups: GroupedCategories = {
      Amateur: [], Pro: [], Najlepszy: [], Master: [], U16: [],
    };

    categories.forEach((cat) => {
      if (!cat.name) return; // Pomijamy kategorie bez nazwy

      let assigned = false;
      const nameLower = cat.name.toLowerCase();

      // Iteracja po zdefiniowanej konfiguracji grup
      for (const config of categoryGroupConfig) {
          // Sprawdzenie, czy nazwa zawiera któreś ze słów kluczowych dla danej grupy
          if (config.keywords.some(keyword => nameLower.includes(keyword))) {
              groups[config.key].push(cat);
              assigned = true;
              break; // Przypisz tylko do pierwszej pasującej grupy
          }
      }

      // Jeśli kategoria nie została przypisana do żadnej grupy na podstawie słów kluczowych
      if (!assigned) {
         console.warn(`Category "${cat.name}" (ID: ${cat.id}) did not match any predefined group keywords.`);
         // Można by ewentualnie dodać logikę fallback, np. sprawdzanie części nazwy przed " / "
         // lub stworzyć grupę "Inne", ale na razie tylko ostrzegamy.
      }
    });

    // Sortowanie wewnątrz grup nie jest już potrzebne, bo sortujemy główne `categories` po pobraniu.
    // Jeśli jednak chcesz zachować sortowanie w grupach, odkomentuj poniższy blok:
    // /*
    Object.values(groups).forEach((group) =>
      group?.sort((a: Category, b: Category) => a.name.localeCompare(b.name))
    );
    // */

    return groups;
  }, [categories]); // Zależność od posortowanych kategorii

  // --- Funkcje Formatujące (bez zmian z ostatniej wersji) ---
  const formatCategoryName = (name: string): string => {
    if (!name) return "Unnamed Category";
    if (name.includes("Najlepsza Ząbkowiczanka") || name.includes("Najlepszy Ząbkowiczanin")) {
        return name.split(" / ")[0].trim();
    }
    return name.includes(" / ") ? name.split(" / ")[0].trim() : name;
  };

  const getEnglishName = (name: string): string | null => {
    if (!name) return null;
    if (name.includes(" / ")) {
      const parts = name.split(" / ");
      return parts.length > 1 ? parts[1].trim() : null;
    }
    return null;
  };

  // --- Renderowanie Komponentu (bez zmian z ostatniej wersji) ---
  return (
    <div className={styles.homeContainer}>
      {/* <Title level={1}>Hardstyle Kettlebell European Championship- Live Results</Title> */}

      {isLoading && (
        <div className={styles.centered}>
          <Spin size="large" tip="Ładowanie kategorii..." />
        </div>
      )}

      {isError && (
        <Alert
          message="Błąd ładowania kategorii"
          description={ error?.message || "Nie udało się pobrać listy kategorii. Spróbuj odświeżyć stronę." }
          type="error"
          showIcon
          className={styles.errorAlert}
        />
      )}

      {!isLoading && !isError && categories.length > 0 && (
        <>
          {categoryGroupConfig.map((groupConfig) => {
            const groupCategories = groupedCategories[groupConfig.key];
            if (!groupCategories || groupCategories.length === 0) {
              return null;
            }
            return (
              <section key={groupConfig.key} className="category-section">
              <Title level={2} className={`${styles.categoryGroupTitle} category-title`}>
                {groupConfig.title}
              </Title>
               <Space wrap size={[16, 16]}>
                 {groupCategories.map((category) => {
                   const displayName = formatCategoryName(category.name);
                   const englishName = getEnglishName(category.name);
                   return (
                     // Renderujemy Link i Card bezpośrednio w mapowaniu
                     <Link to={`/category/${category.id}`} key={category.id}>
                       <Card
                         hoverable
                         className={styles.categoryCard} // Ta sama klasa CSS
                         title={displayName}
                       >
                         {englishName && (
                           <div className={styles.englishName}>
                             {englishName}
                           </div>
                         )}
                       </Card>
                     </Link>
                   );
                 })}
               </Space>

              </section>
            );
          })}
        </>
      )}


      {!isLoading && !isError && categories.length === 0 && (
        <Paragraph style={{ textAlign: "center" }}>
          Brak dostępnych kategorii do wyświetlenia.
        </Paragraph>
      )}

      {isFetching && !isLoading && (
        <Spin size="small" style={{ position: "fixed", top: "10px", right: "10px", zIndex: 1000 }} />
      )}
    </div>
  );
};

export default HomePage;
