import React, { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Table, Spin, Alert, Typography, Button, Input } from "antd";
import type { TableProps, ColumnsType} from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import apiClient from "../services/api";
import { CategoryResultsResponse, OverallResult, Category } from "../types";
import styles from "./CategoryPage.module.css";

const { Title, Paragraph } = Typography;
const { Search } = Input;

// --- TIME GATE FOR OVERALL RESULTS ---
// Set the date and time after which the overall results should be visible.
// It uses the browser's local time zone (Warsaw/CEST in your case).
const OVERALL_RESULTS_VISIBLE_AFTER = new Date();
// Set hours, minutes, seconds, milliseconds (HH, MM, SS, MS) for today. Change 21, 10 for desired time.
OVERALL_RESULTS_VISIBLE_AFTER.setHours(0, 1, 0, 0);

const formatNumber = (
  value: number | null | undefined,
  digits: number = 1
): string => {
  if (value == null || isNaN(value)) return "-";
  return value.toFixed(digits);
};
const formatPercentage = (value: number | null | undefined): string => {
  if (value == null || isNaN(value)) return "-";
  return `${value.toFixed(2)}%`;
};

const fetchCategoryData = async (
  categoryId: string | undefined
): Promise<{ categoryInfo: Category; results: CategoryResultsResponse }> => {
  if (!categoryId) throw new Error("Category ID jest wymagane");

  try {
    console.log(`Attempting to fetch category data for ID: ${categoryId}`);

    const [catInfoResponse, resultsResponse] = await Promise.all([
      apiClient.get<Category>(`/categories/${categoryId}/`),
      apiClient.get<CategoryResultsResponse>(
        `/categories/${categoryId}/results/`
      ),
    ]);

    console.log("Category data successfully retrieved");
    const sortedResults = resultsResponse.data.sort(
      (a, b) => (a.final_position ?? 999) - (b.final_position ?? 999)
    );
    return { categoryInfo: catInfoResponse.data, results: sortedResults };
  } catch (error) {
    console.error(`Error fetching category data for ID ${categoryId}:`, error);
    // Could add mock data option here if needed during development
    throw error;
  }
};

const overallColumns: TableProps<OverallResult>["columns"] = [
  {
    title: "M-ce",
    dataIndex: "final_position",
    key: "final_position",
    render: (pos) => pos ?? "-",
    sorter: (a, b) => (a.final_position ?? 999) - (b.final_position ?? 999),
    width: 80,
    align: "center",
  },
  {
    title: "Zawodnik",
    key: "player",
    render: (_, record) => `${record.player.name} ${record.player.surname}`,
    sorter: (a, b) =>
      `${a.player.name} ${a.player.surname}`.localeCompare(
        `${b.player.name} ${b.player.surname}`
      ),
    responsive: ["xs", "sm", "md", "lg", "xl", "xxl"],
  },
  {
    title: "Klub",
    dataIndex: ["player", "club_name"],
    key: "club",
    render: (club) => club || "-",
    sorter: (a, b) =>
      (a.player.club_name || "").localeCompare(b.player.club_name || ""),
    responsive: ["md"],
  },
  {
    title: "Waga",
    dataIndex: ["player", "weight"],
    key: "weight",
    render: (w) => formatNumber(w, 1),
    sorter: (a, b) => (a.player.weight ?? 0) - (b.player.weight ?? 0),
    align: "right",
    responsive: ["lg"],
  },
  {
    title: "Pkt Suma",
    dataIndex: "total_points",
    key: "total_points",
    render: (pts) => formatNumber(pts, 1),
    sorter: (a, b) => (a.total_points ?? 0) - (b.total_points ?? 0),
    align: "right",
    className: "boldColumn",
    width: 100,
  },
  {
    title: "Snatch",
    dataIndex: "snatch_points",
    key: "snatch_points",
    render: (pts) => formatNumber(pts, 1),
    sorter: (a, b) => (a.snatch_points ?? 0) - (b.snatch_points ?? 0),
    align: "right",
    responsive: ["lg"],
  },
  {
    title: "TGU",
    dataIndex: "tgu_points",
    key: "tgu_points",
    render: (pts) => formatNumber(pts, 1),
    sorter: (a, b) => (a.tgu_points ?? 0) - (b.tgu_points ?? 0),
    align: "right",
    responsive: ["lg"],
  },
  // {
  //   title: "SSP",
  //   dataIndex: "see_saw_press_points",
  //   key: "ssp_points",
  //   render: (pts) => formatNumber(pts, 1),
  //   sorter: (a, b) =>
  //     (a.see_saw_press_points ?? 0) - (b.see_saw_press_points ?? 0),
  //   align: "right",
  //   responsive: ["xl"],
  // },
  {
    title: "KBS",
    dataIndex: "kb_squat_points",
    key: "kbs_points",
    render: (pts) => formatNumber(pts, 1),
    sorter: (a, b) => (a.kb_squat_points ?? 0) - (b.kb_squat_points ?? 0),
    align: "right",
    responsive: ["xl"],
  },
  // {
  //   title: "Pistol",
  //   dataIndex: "pistol_squat_points",
  //   key: "pistol_points",
  //   render: (pts) => formatNumber(pts, 1),
  //   sorter: (a, b) =>
  //     (a.pistol_squat_points ?? 0) - (b.pistol_squat_points ?? 0),
  //   align: "right",
  //   responsive: ["xl"],
  // },
  {
    title: "OKBP",
    dataIndex: "one_kb_press_points",
    key: "okbp_points",
    render: (pts) => formatNumber(pts, 1),
    sorter: (a, b) =>
      (a.one_kb_press_points ?? 0) - (b.one_kb_press_points ?? 0),
    align: "right",
    responsive: ["xl"],
  },
  {
    title: "TKBP",
    dataIndex: "two_kb_press_points",
    key: "tkbp_points",
    render: (pts) => formatNumber(pts, 1),
    sorter: (a, b) =>
      (a.two_kb_press_points ?? 0) - (b.two_kb_press_points ?? 0),
    align: "right",
    responsive: ["xl"],
  },
  {
    title: "Tiebreak",
    dataIndex: "tiebreak_points",
    key: "tiebreak_points",
    render: (pts) => formatNumber(pts, 1),
    sorter: (a, b) => (a.tiebreak_points ?? 0) - (b.tiebreak_points ?? 0),
    align: "right",
    responsive: ["xl"],
  },
];
// Helper function for safe nested property access
function getNestedValue(
  obj: any,
  path: string,
  defaultValue: any = undefined
): any {
  if (obj === null || typeof obj === "undefined") {
    return defaultValue;
  }
  return path
    .split(".")
    .reduce(
      (acc, key) =>
        acc && typeof acc === "object" && key in acc
          ? acc[key as keyof typeof acc]
          : defaultValue,
      obj
    );
}
const calculateSnatchScore = (result: OverallResult['snatch_result']): number => {
  if (!result) return 0;
  const weight = result.kettlebell_weight ?? 0;
  const reps = result.repetitions ?? 0;
  return weight > 0 && reps > 0 ? weight * reps : 0;
};

const calculateTguScore = (result: OverallResult['tgu_result'], playerWeight?: number | null): number => {
  if (!result || !playerWeight || playerWeight <= 0) return 0;
  const maxRes = Math.max(result.result_1 ?? 0, result.result_2 ?? 0, result.result_3 ?? 0);
  return maxRes > 0 ? (maxRes / playerWeight) * 100 : 0; // Zwraca % masy ciała
};

const calculateKbSquatScore = (result: OverallResult['kb_squat_result'], playerWeight?: number | null): number => {
  if (!result || !playerWeight || playerWeight <= 0) return 0;
  const maxRes = Math.max(result.result_1 ?? 0, result.result_2 ?? 0, result.result_3 ?? 0);
  return maxRes > 0 ? (maxRes / playerWeight) * 100 : 0; // Zwraca % masy ciała
};

const calculateOneKbPressScore = (result: OverallResult['one_kettlebell_press_result'], playerWeight?: number | null): number => {
   if (!result || !playerWeight || playerWeight <= 0) return 0;
   const maxRes = Math.max(result.result_1 ?? 0, result.result_2 ?? 0, result.result_3 ?? 0);
   return maxRes > 0 ? (maxRes / playerWeight) * 100 : 0; // Zwraca % masy ciała
};

const calculateTwoKbPressScore = (result: OverallResult['two_kettlebell_press_result'], playerWeight?: number | null): number => {
   if (!result || !playerWeight || playerWeight <= 0) return 0;
   const maxRes = Math.max(result.result_1 ?? 0, result.result_2 ?? 0, result.result_3 ?? 0);
   return maxRes > 0 ? (maxRes / playerWeight) * 100 : 0; // Zwraca % masy ciała
};
const createDisciplineColumns = (
  specificColumns: ColumnsType<OverallResult> = [] // Użyj ColumnsType zamiast TableProps[...]
): ColumnsType<OverallResult> => {
  const mappedSpecificColumns: ColumnsType<OverallResult> =
    specificColumns.map((col: any) => ({
      ...col,
      align: col.align || "right",
      width: col.width || 80,
    }));

  const columns: ColumnsType<OverallResult> = [
    {
      title: "Pozycja", // Przesunięta na początek dla lepszej widoczności
      key: "rank",
      width: 60,
      align: "center",
      fixed: "left",
      // Renderuje pozycję na podstawie indeksu w posortowanej tablicy
      // (index jest przekazywany przez Ant Design Table jako drugi argument render)
      render: (_, __, index) => index + 1,
    },
    {
      title: "Zawodnik",
      key: "player",
      render: (_, record: OverallResult): React.ReactNode =>
        record?.player ? `${record.player.name} ${record.player.surname}` : "?",
      sorter: (a: OverallResult, b: OverallResult): number => // Sortowanie po nazwisku nadal może być przydatne w samej kolumnie
        `${a.player?.name} ${a.player?.surname}`.localeCompare(
          `${b.player?.name} ${b.player?.surname}`
        ),
      // fixed: 'left', // Już nie fixed, bo pozycja jest fixed
      width: 180,
    },
    {
      title: "Waga",
      dataIndex: ["player", "weight"],
      key: "weight",
      render: (w) => formatNumber(w, 1),
      // Sortowanie po wadze nadal OK
      sorter: (a: OverallResult, b: OverallResult) => (a.player?.weight ?? 0) - (b.player?.weight ?? 0),
      align: "right",
      width: 80,
    },
    ...mappedSpecificColumns, // Kolumny specyficzne dla dyscypliny
    // Usunięto starą kolumnę "Pozycja", która sortowała po kluczu z API
  ];

  return columns;
};

// Definicje kolumn bez zmian dla dyscyplin, które już były poprawne
const snatchCols = createDisciplineColumns(
  [
    {
      title: "Waga kettla",
      dataIndex: ["snatch_result", "kettlebell_weight"],
      key: "snatch_weight",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Powt.",
      dataIndex: ["snatch_result", "repetitions"],
      key: "snatch_reps",
      render: (v) => v ?? 0,
    },
    {
      title: "Wynik",
      dataIndex: ["snatch_result", "result_score"],
      key: "snatch_score",
      render: (v) => formatNumber(v, 1),
    },
  ],
  "snatch_result.position"
);

const tguCols = createDisciplineColumns(
  [
    {
      title: "Próba 1",
      dataIndex: ["tgu_result", "result_1"],
      key: "tgu_r1",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 2",
      dataIndex: ["tgu_result", "result_2"],
      key: "tgu_r2",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 3",
      dataIndex: ["tgu_result", "result_3"],
      key: "tgu_r3",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Max (kg)",
      dataIndex: ["tgu_result", "max_result_val"],
      key: "tgu_max",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "% MC",
      dataIndex: ["tgu_result", "bw_percentage_val"],
      key: "tgu_perc",
      render: (v) => formatPercentage(v),
    },
  ],
  "tgu_result.position"
);

const sspCols = createDisciplineColumns(
  [
    // See Saw Press - zakładam, że ma podział L/P i zostaje bez zmian? Jeśli nie, zmień poniżej.
    {
      title: "L1",
      dataIndex: ["see_saw_press_result", "result_left_1"],
      key: "ssp_l1",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "P1",
      dataIndex: ["see_saw_press_result", "result_right_1"],
      key: "ssp_r1",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "L2",
      dataIndex: ["see_saw_press_result", "result_left_2"],
      key: "ssp_l2",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "P2",
      dataIndex: ["see_saw_press_result", "result_right_2"],
      key: "ssp_r2",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "L3",
      dataIndex: ["see_saw_press_result", "result_left_3"],
      key: "ssp_l3",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "P3",
      dataIndex: ["see_saw_press_result", "result_right_3"],
      key: "ssp_r3",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Max (kg)",
      dataIndex: ["see_saw_press_result", "max_score_val"],
      key: "ssp_max",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "% MC",
      dataIndex: ["see_saw_press_result", "bw_percentage_val"],
      key: "ssp_perc",
      render: (v) => formatPercentage(v),
    },
  ],
  "see_saw_press_result.position"
);

// --- ZMIENIONA DEFINICJA KOLUMN DLA KETTLEBELL SQUAT (KBS) ---
const kbsCols = createDisciplineColumns(
  [
    {
      title: "Próba 1",
      dataIndex: ["kb_squat_result", "result_1"],
      key: "kbs_r1",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 2",
      dataIndex: ["kb_squat_result", "result_2"],
      key: "kbs_r2",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 3",
      dataIndex: ["kb_squat_result", "result_3"],
      key: "kbs_r3",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Max (kg)",
      dataIndex: ["kb_squat_result", "max_score_val"],
      key: "kbs_max",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "% MC",
      dataIndex: ["kb_squat_result", "bw_percentage_val"],
      key: "kbs_perc",
      render: (v) => formatPercentage(v),
    },
  ],
  "kb_squat_result.position" // Klucz sortowania pozostaje bez zmian
);

const pistolCols = createDisciplineColumns(
  [
    {
      title: "Próba 1",
      dataIndex: ["pistol_squat_result", "result_1"],
      key: "pistol_r1",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 2",
      dataIndex: ["pistol_squat_result", "result_2"],
      key: "pistol_r2",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 3",
      dataIndex: ["pistol_squat_result", "result_3"],
      key: "pistol_r3",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Max (kg)",
      dataIndex: ["pistol_squat_result", "max_result_val"],
      key: "pistol_max",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "% MC",
      dataIndex: ["pistol_squat_result", "bw_percentage_val"],
      key: "pistol_perc",
      render: (v) => formatPercentage(v),
    },
  ],
  "pistol_squat_result.position"
);

const okbpCols = createDisciplineColumns(
  [
    {
      title: "Próba 1",
      dataIndex: ["one_kettlebell_press_result", "result_1"],
      key: "okbp_r1",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 2",
      dataIndex: ["one_kettlebell_press_result", "result_2"],
      key: "okbp_r2",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 3",
      dataIndex: ["one_kettlebell_press_result", "result_3"],
      key: "okbp_r3",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Max (kg)",
      dataIndex: ["one_kettlebell_press_result", "max_result_val"],
      key: "okbp_max",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "% MC",
      dataIndex: ["one_kettlebell_press_result", "bw_percentage_val"],
      key: "okbp_perc",
      render: (v) => formatPercentage(v),
    },
  ],
  "one_kettlebell_press_result.position"
);

// --- ZMIENIONA DEFINICJA KOLUMN DLA TWO KETTLEBELL PRESS (TKBP) ---
const tkbpCols = createDisciplineColumns(
  [
    {
      title: "Próba 1",
      dataIndex: ["two_kettlebell_press_result", "result_1"],
      key: "tkbp_r1",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 2",
      dataIndex: ["two_kettlebell_press_result", "result_2"],
      key: "tkbp_r2",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Próba 3",
      dataIndex: ["two_kettlebell_press_result", "result_3"],
      key: "tkbp_r3",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "Max (kg)",
      dataIndex: ["two_kettlebell_press_result", "max_score_val"],
      key: "tkbp_max",
      render: (v) => formatNumber(v, 1),
    },
    {
      title: "% MC",
      dataIndex: ["two_kettlebell_press_result", "bw_percentage_val"],
      key: "tkbp_perc",
      render: (v) => formatPercentage(v),
    },
  ],
  "two_kettlebell_press_result.position" // Klucz sortowania pozostaje bez zmian
);

interface DisciplineMapEntry {
  name: string;
  key: keyof OverallResult;
  columns: TableProps<any>["columns"];
  sortKey: string;
}

// Mapa dyscyplin - używa teraz zaktualizowanych kbsCols i tkbpCols
interface DisciplineMapEntry {
  name: string;
  key: keyof OverallResult; // Klucz do obiektu wyniku w OverallResult (np. 'snatch_result')
  columns: ColumnsType<any>; // Poprawiony typ
  calculateScore: (result: OverallResult) => number; // Funkcja do obliczania wyniku
}

const disciplineMap: Record<string, DisciplineMapEntry> = {
  snatch: {
    name: "Snatch",
    key: "snatch_result",
    columns: snatchCols,
    calculateScore: (r) => calculateSnatchScore(r.snatch_result),
  },
  tgu: {
    name: "Turkish Get-Up (TGU)",
    key: "tgu_result",
    columns: tguCols,
    calculateScore: (r) => calculateTguScore(r.tgu_result, r.player?.weight),
  },
  // see_saw_press: { ... }, // Jeśli używane
  kb_squat: {
    name: "Kettlebell Squat (KBS)",
    key: "kb_squat_result", // Upewnij się, że klucz pasuje do danych z API
    columns: kbsCols,
    calculateScore: (r) => calculateKbSquatScore(r.kb_squat_result, r.player?.weight), // Użyj poprawnego klucza
  },
  // pistol_squat: { ... }, // Jeśli używane
  one_kettlebell_press: {
    name: "One Kettlebell Press (OKBP)", // Zmieniona nazwa dla jasności?
    key: "one_kettlebell_press_result",
    columns: okbpCols,
    calculateScore: (r) => calculateOneKbPressScore(r.one_kettlebell_press_result, r.player?.weight),
  },
  two_kettlebell_press: {
    name: "Two Kettlebell Press (TKBP)", // Zmieniona nazwa dla jasności?
    key: "two_kettlebell_press_result", // Upewnij się, że klucz pasuje do danych z API
    columns: tkbpCols,
    calculateScore: (r) => calculateTwoKbPressScore(r.two_kettlebell_press_result, r.player?.weight), // Użyj poprawnego klucza
  },
};

const CategoryPage: React.FC = () => {
  const { categoryId } = useParams<{ categoryId: string }>();
  const [filterTerm, setFilterTerm] = useState<string>("");

  const { data, isLoading, isError, error, isFetching } = useQuery<
    { categoryInfo: Category; results: CategoryResultsResponse },
    Error
  >({
    queryKey: ["categoryData", categoryId],
    queryFn: () => fetchCategoryData(categoryId),
    enabled: !!categoryId,
    refetchInterval: 120000,
    staleTime: 60000,
  });

  const categoryInfo = data?.categoryInfo;
  const results = data?.results ?? [];

  const filteredResults = useMemo(() => {
    if (!results) return [];
    if (!filterTerm) return results;
    const lowerCaseFilter = filterTerm.toLowerCase();
    return results.filter(
      (result) =>
        result.player &&
        (`${result.player.name} ${result.player.surname}`
          .toLowerCase()
          .includes(lowerCaseFilter) ||
          (result.player.club_name || "")
            .toLowerCase()
            .includes(lowerCaseFilter))
    );
  }, [results, filterTerm]);

  const renderAntdTable = (
    title: string,
    dataSource: OverallResult[], // Przyjmuje już posortowane dane
    columns: ColumnsType<any> = [], // Poprawiony typ
    rowKeySuffix: string
  ) => {
    if (!dataSource || dataSource.length === 0) {
      if (filterTerm && results.length > 0) { // Sprawdź oryginalne wyniki przed filtrowaniem
        return (
          <Paragraph key={rowKeySuffix} style={{ marginTop: "1rem" }}>
            Brak zawodników pasujących do filtra dla: {title}
          </Paragraph>
        );
      }
      return null;
    }

    return (
      <section key={rowKeySuffix}>
        <Title level={2} className={styles.disciplineTableTitle}>
          {title}
        </Title>
        <Table
          dataSource={dataSource} // Przekaż posortowane dane
          columns={columns}
          rowKey={(record) =>
            record?.player?.id
              ? `${record.player.id}-${rowKeySuffix}` // Bardziej unikalny klucz
              : `${Math.random()}-${rowKeySuffix}`
          }
          pagination={false} // Zwykle nie paginujemy tabel dyscyplin
          size="middle"
          bordered
          scroll={{ x: "max-content" }}
          // Loading nie jest już potrzebny tutaj w ten sposób
        />
      </section>
    );
  };

  if (isLoading) {
    return (
      <div className={styles.centered}>
        <Spin
          size="large"
          tip={`Ładowanie danych kategorii ${categoryId}...`}
        />
      </div>
    );
  }

  if (isError && !results.length) {
    return (
      <div className={styles.categoryContainer}>
        <Button
          type="link"
          icon={<ArrowLeftOutlined />}
          href="/"
          className={styles.backButton}
        >
          Powrót do listy kategorii
        </Button>
        <Alert
          message={`Błąd ładowania danych dla kategorii ${categoryId}`}
          description={
            error?.message ||
            "Nie udało się pobrać danych. Spróbuj odświeżyć stronę."
          }
          type="error"
          showIcon
        />
      </div>
    );
  }

  // --- Calculate if overall results should be shown based on time ---
  const now = new Date();
  const showOverallResults = now >= OVERALL_RESULTS_VISIBLE_AFTER;

  return (
    <div className={styles.categoryContainer}>
      <Button
        type="link"
        icon={<ArrowLeftOutlined />}
        href="/"
        className={styles.backButton}
      >
        Powrót do listy kategorii
      </Button>

      <Title level={2} className={styles.categoryTitle}>
        Wyniki: {categoryInfo?.name || `Kategoria ${categoryId}`}
        {isFetching && !isLoading && (
          <Spin size="small" style={{ marginLeft: "8px" }} />
        )}
      </Title>
      {categoryInfo && (
        <Paragraph type="secondary" className={styles.categoryDisciplines}>
          Dyscypliny: {categoryInfo.disciplines.join(", ")}
        </Paragraph>
      )}

      <Search
        placeholder="Filtruj po nazwisku, imieniu lub klubie..."
        allowClear
        enterButton="Filtruj"
        size="large"
        onSearch={(value) => setFilterTerm(value)}
        onChange={(e) => {
          if (!e.target.value) setFilterTerm("");
        }}
        className={styles.filterInput}
        disabled={results.length === 0}
      />

      {isError && results.length > 0 && (
        <Alert
          message="Nie udało się odświeżyć danych"
          description={
            error?.message || "Wyświetlane są ostatnie znane wyniki."
          }
          type="warning"
          showIcon
          style={{ marginBottom: "1rem" }}
          closable
        />
      )}

      {showOverallResults ? (
        renderAntdTable(
          "Klasyfikacja Generalna",
          filteredResults,
          overallColumns,
          "overall"
        )
      ) : (
        <div
          style={{
            padding: "20px",
            textAlign: "center",
            border: "1px dashed #ccc",
            margin: "20px 0",
            borderRadius: "4px",
          }}
        >
          <Paragraph style={{ fontStyle: "italic", color: "#FFFFFF" }}>
          Pełna klasyfikacja będzie dostępna po 16:15./ Overall Classification will be available after 16:15.
          </Paragraph>
          <Paragraph type="secondary" style={{ fontSize: "0.9em", color: "#FFFFFF" }}>
            (Po tym czasie należy odświeżyć stronę /Please refresh the page after this time)
          </Paragraph>
        </div>
      )}

      {/* --- ZMODYFIKOWANA PĘTLA MAPUJĄCA DYSCYPLINY --- */}
      {categoryInfo?.disciplines &&
        categoryInfo.disciplines.map((disciplineApiKey) => {
          const mappingInfo = disciplineMap[disciplineApiKey];
          if (!mappingInfo) {
            console.warn(
              `Nie znaleziono mapowania dla klucza dyscypliny z API: ${disciplineApiKey}`
            );
            return null;
          }

          // 1. Filtrowanie: Weź tylko wyniki pasujące do filtra tekstowego ORAZ
          //    mające jakikolwiek obiekt wyniku dla DANEJ dyscypliny
          const filteredSource = filteredResults.filter(
            (r) => r && getNestedValue(r, mappingInfo.key) // Sprawdza czy istnieje obiekt np. r.snatch_result
          );

          // 2. Sortowanie na Frontendzie: Użyj funkcji calculateScore z mapy
          const sortedDisciplineDataSource = [...filteredSource].sort((a, b) => {
            const scoreA = mappingInfo.calculateScore(a);
            const scoreB = mappingInfo.calculateScore(b);

            // Sortuj malejąco po wyniku (score)
            if (scoreA > scoreB) return -1;
            if (scoreA < scoreB) return 1;

            // Tie-breaking: Po punktach tiebreak (jeśli istnieją i są istotne dla tej dyscypliny)
            // Zakładamy, że wyższy tiebreak jest lepszy
            const tieA = a.tiebreak_points ?? -Infinity;
            const tieB = b.tiebreak_points ?? -Infinity;
            if (tieA > tieB) return -1;
            if (tieA < tieB) return 1;

            // Ostateczny tie-breaking: Po nazwisku i imieniu
            const nameA = `${a.player?.name} ${a.player?.surname}`;
            const nameB = `${b.player?.name} ${b.player?.surname}`;
            return nameA.localeCompare(nameB);
          });

          // 3. Renderowanie tabeli z już posortowanymi danymi
          return renderAntdTable(
            mappingInfo.name,
            sortedDisciplineDataSource, // Przekaż posortowane dane
            mappingInfo.columns,
            mappingInfo.key.toString() // Użyj klucza dyscypliny jako suffix dla rowKey
          );
        })}

      {filterTerm && filteredResults.length === 0 && results.length > 0 && (
        <Paragraph style={{ textAlign: "center", marginTop: "2rem" }}>
          Brak zawodników pasujących do filtra "{filterTerm}".
        </Paragraph>
      )}
      {!isLoading && !isError && results.length === 0 && !filterTerm && (
        <Paragraph style={{ textAlign: "center", marginTop: "2rem" }}>
          Brak wyników w tej kategorii.
        </Paragraph>
      )}
    </div>
  );
};

export default CategoryPage;
