import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { List, Card, Spin, Alert, Typography } from "antd";
import apiClient from "../services/api";
import { Category } from "../types";
import styles from "./HomePage.module.css";

const { Title, Paragraph, Text } = Typography;

const fetchCategories = async (): Promise<Category[]> => {
  const response = await apiClient.get<Category[]>("/categories/");
  return response.data;
};

interface GroupedCategories {
  Amateur: Category[];
  Pro: Category[];
  Najlepszy: Category[];
  Master: Category[];
  U18Plus: Category[];
  U16: Category[];
  Other?: Category[];
}

const HomePage: React.FC = () => {
  const {
    data: categories = [],
    isLoading,
    isError,
    error,
    isFetching,
  } = useQuery<Category[], Error>({
    queryKey: ["categories"],
    queryFn: fetchCategories,
    staleTime: 60 * 1000 * 10,
  });

  const groupedCategories = useMemo((): GroupedCategories => {
    const groups: GroupedCategories = {
      Amateur: [],
      Pro: [],
      Najlepszy: [],
      Master: [],
      U18Plus: [],
      U16: [],
      Other: [],
    };
    const najlepszyNames = ["Ząbkowiczanka", "Ząbkowiczanin"];

    categories.forEach((cat) => {
      const name = cat.name;
      const nameLower = name.toLowerCase();

      if (najlepszyNames.includes(name)) {
        groups.Najlepszy.push(cat);
      } else if (nameLower.includes("master")) {
        groups.Master.push(cat);
      } else if (nameLower.includes("+18") || nameLower.includes("plus 18")) {
        groups.U18Plus.push(cat);
      } else if (nameLower.includes("u16") || nameLower.includes("under 16")) {
        groups.U16.push(cat);
      } else if (nameLower.includes("pro")) {
        groups.Pro.push(cat);
      } else if (
        nameLower.includes("amator") ||
        nameLower.includes("amateur")
      ) {
        groups.Amateur.push(cat);
      } else if (groups.Other) {
        groups.Other.push(cat);
      }
    });

    Object.values(groups).forEach((group) =>
      group?.sort((a, b) => a.name.localeCompare(b.name))
    );

    if (groups.Other?.length === 0) {
      delete groups.Other;
    }
    return groups;
  }, [categories]);

  const formatCategoryName = (
    name: string,
    groupKey: keyof GroupedCategories
  ): string => {
    if (groupKey === "Najlepszy") {
      if (name === "Ząbkowiczanka") return "Ząbkowiczanka";
      if (name === "Ząbkowiczanin") return "Ząbkowiczanin";
      return name;
    }
    const cleanedName = name.replace(
      /^(Amator |Amateur |PRO |Masters |\+18 |U16 )\s*/i,
      ""
    );
    return cleanedName;
  };

  const renderCategoryGroup = (
    title: string,
    groupKey: keyof GroupedCategories
  ) => {
    const groupCategories = groupedCategories[groupKey];
    if (!groupCategories || groupCategories.length === 0) return null;
    return (
      <section key={title}>
        <Title level={3} className={styles.categoryGroupTitle}>
          {title}
        </Title>
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 5 }}
          dataSource={groupCategories}
          renderItem={(category) => (
            <List.Item>
              <Link to={`/category/${category.id}`}>
                <Card
                  hoverable
                  className={styles.categoryCard}
                  title={formatCategoryName(category.name, groupKey)}
                ></Card>
              </Link>
            </List.Item>
          )}
        />
      </section>
    );
  };

  return (
    <div className={styles.homeContainer}>
      <Title level={1}>European Kettlebell Championship - Live Results</Title>
      <Paragraph className={styles.introText}>
        Witaj na stronie wyników! Wybierz kategorię poniżej, aby zobaczyć
        aktualne rezultaty zawodników.
      </Paragraph>

      {isLoading && (
        <div className={styles.centered}>
          <Spin size="large" tip="Ładowanie kategorii..." />
        </div>
      )}
      {isError && (
        <Alert
          message="Błąd ładowania kategorii"
          description={
            error?.message ||
            "Nie udało się pobrać listy kategorii. Spróbuj odświeżyć stronę."
          }
          type="error"
          showIcon
          className={styles.errorAlert}
        />
      )}

      {!isLoading && !isError && categories.length > 0 && (
        <>
          {renderCategoryGroup("Amator", "Amateur")}
          {renderCategoryGroup("PRO", "Pro")}
          {renderCategoryGroup("Najlepszy", "Najlepszy")}
          {renderCategoryGroup("Masters", "Master")}
          {renderCategoryGroup("+18", "U18Plus")}
          {renderCategoryGroup("U16", "U16")}
          {groupedCategories.Other && renderCategoryGroup("Pozostałe", "Other")}
        </>
      )}
      {!isLoading && !isError && categories.length === 0 && (
        <Paragraph style={{ textAlign: "center" }}>
          Brak dostępnych kategorii do wyświetlenia.
        </Paragraph>
      )}

      {isFetching && !isLoading && (
        <Spin
          size="small"
          style={{
            position: "fixed",
            top: "10px",
            right: "10px",
            zIndex: 1000,
          }}
        />
      )}
    </div>
  );
};

export default HomePage;
