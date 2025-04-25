import React, { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Table, Spin, Alert, Typography, Button, Input } from "antd";
import type { TableProps } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import apiClient from "../services/api";

import {
  CategoryResultsResponse,
  OverallResult,
  Category,
  SnatchResultData,
  TGUResultData,
  KBSquatResultData,
  OneKettlebellPressResultData,
  TwoKettlebellPressResultData,
} from "../types";
import styles from "./CategoryPage.module.css";

const { Title, Paragraph } = Typography;
const { Search } = Input;

// --- TIME GATE ---
const OVERALL_RESULTS_VISIBLE_AFTER = new Date();
OVERALL_RESULTS_VISIBLE_AFTER.setHours(0, 1, 0, 0); // Ustaw właściwy czas (np. 16, 15 dla 16:15)

// --- Funkcje formatujące ---
const formatNumber = (
  value: number | null | undefined,
  digits: number = 1
): string => {
  if (value == null || isNaN(value)) return "-";
  return new Intl.NumberFormat(navigator.language || "pl-PL", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
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
    const [catInfoResponse, resultsResponse] = await Promise.all([
      apiClient.get<Category>(`/categories/${categoryId}/`),
      apiClient.get<CategoryResultsResponse>(
        `/categories/${categoryId}/results/`
      ),
    ]);

    const sortedResults = resultsResponse.data.sort(
      (a: OverallResult, b: OverallResult) =>
        (a.final_position ?? 999) - (b.final_position ?? 999)
    );
    return { categoryInfo: catInfoResponse.data, results: sortedResults };
  } catch (error) {
    console.error(`Error fetching category data for ID ${categoryId}:`, error);
    throw error;
  }
};

const overallColumns: TableProps<OverallResult>["columns"] = [
  {
    title: "M-ce",
    dataIndex: "final_position",
    key: "final_position",
    render: (pos: number | null | undefined) => pos ?? "-",
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.final_position ?? 999) - (b.final_position ?? 999),
    width: 80,
    align: "center",
    fixed: "left",
  },
  {
    title: "Zawodnik",
    key: "player",
    render: (_: any, record: OverallResult) =>
      `${record.player?.name ?? ""} ${record.player?.surname ?? ""}`.trim(),
    sorter: (a: OverallResult, b: OverallResult) =>
      `${a.player?.name ?? ""} ${a.player?.surname ?? ""}`
        .trim()
        .localeCompare(
          `${b.player?.name ?? ""} ${b.player?.surname ?? ""}`.trim()
        ),
    responsive: ["xs", "sm", "md", "lg", "xl", "xxl"],
    ellipsis: true,
  },
  {
    title: "Klub",
    dataIndex: ["player", "club_name"],
    key: "club",
    render: (club: string | null | undefined) => club || "-",
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.player?.club_name || "").localeCompare(b.player?.club_name || ""),
    responsive: ["md"],
    ellipsis: true,
  },
  {
    title: "Waga",
    dataIndex: ["player", "weight"],
    key: "weight",
    render: (w: number | null | undefined) => formatNumber(w, 1),
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.player?.weight ?? 0) - (b.player?.weight ?? 0),
    align: "right",
    responsive: ["lg"],
    width: 80,
  },
  {
    title: "Pkt Suma",
    dataIndex: "total_points",
    key: "total_points",
    render: (pts: number | null | undefined) => formatNumber(pts, 1),
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.total_points ?? -Infinity) - (b.total_points ?? -Infinity),
    align: "right",
    width: 100,
  },
  {
    title: "Pkt Snatch",
    dataIndex: "snatch_points",
    key: "snatch_points",
    render: (pts: number | null | undefined) => formatNumber(pts, 1),
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.snatch_points ?? -Infinity) - (b.snatch_points ?? -Infinity),
    align: "right",
    responsive: ["lg"],
    width: 100,
  },
  {
    title: "Pkt TGU",
    dataIndex: "tgu_points",
    key: "tgu_points",
    render: (pts: number | null | undefined) => formatNumber(pts, 1),
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.tgu_points ?? -Infinity) - (b.tgu_points ?? -Infinity),
    align: "right",
    responsive: ["lg"],
    width: 100,
  },
  {
    title: "Pkt KBS",
    dataIndex: "kb_squat_points",
    key: "kbs_points",
    render: (pts: number | null | undefined) => formatNumber(pts, 1),
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.kb_squat_points ?? -Infinity) - (b.kb_squat_points ?? -Infinity),
    align: "right",
    responsive: ["xl"],
    width: 100,
  },
  {
    title: "Pkt OKBP",
    dataIndex: "one_kb_press_points",
    key: "okbp_points",
    render: (pts: number | null | undefined) => formatNumber(pts, 1),
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.one_kb_press_points ?? -Infinity) -
      (b.one_kb_press_points ?? -Infinity),
    align: "right",
    responsive: ["xl"],
    width: 100,
  },
  {
    title: "Pkt TKBP",
    dataIndex: "two_kb_press_points",
    key: "tkbp_points",
    render: (pts: number | null | undefined) => formatNumber(pts, 1),
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.two_kb_press_points ?? -Infinity) -
      (b.two_kb_press_points ?? -Infinity),
    align: "right",
    responsive: ["xl"],
    width: 100,
  },
  {
    title: "Tiebreak",
    dataIndex: "tiebreak_points",
    key: "tiebreak_points",
    render: (pts: number | null | undefined) => formatNumber(pts, 1),
    sorter: (a: OverallResult, b: OverallResult) =>
      (a.tiebreak_points ?? -Infinity) - (b.tiebreak_points ?? -Infinity),
    align: "right",
    responsive: ["xl"],
    width: 100,
  },
];

function getNestedValue(
  obj: any,
  path: string,
  defaultValue: any = undefined
): any {
  if (obj === null || typeof obj === "undefined") {
    return defaultValue;
  }
  const value = path
    .split(".")
    .reduce(
      (acc, key) =>
        acc && typeof acc === "object" && key in acc
          ? acc[key as keyof typeof acc]
          : defaultValue,
      obj
    );
  return value === null ? defaultValue : value;
}

const calculateSnatchScore = (result?: SnatchResultData | null): number => {
  if (!result) return -Infinity;
  const weight = result.kettlebell_weight ?? 0;
  const reps = result.repetitions ?? 0;
  return weight > 0 && reps > 0 ? weight * reps : -Infinity;
};

const calculateTguScore = (
  result?: TGUResultData | null,
  playerWeight?: number | null
): number => {
  if (!result || !playerWeight || playerWeight <= 0) return -Infinity;
  const percentage = result.bw_percentage_display;
  if (percentage != null && !isNaN(percentage)) return percentage;

  const maxRes =
    result.max_result_display ??
    Math.max(result.result_1 ?? 0, result.result_2 ?? 0, result.result_3 ?? 0);
  return maxRes > 0 ? (maxRes / playerWeight) * 100 : -Infinity;
};

const calculateKbSquatScore = (
  result?: KBSquatResultData | null,
  playerWeight?: number | null
): number => {
  if (!result || !playerWeight || playerWeight <= 0) return -Infinity;
  const percentage = result.bw_percentage_display;
  if (percentage != null && !isNaN(percentage)) return percentage;

  const maxRes =
    result.max_result_display ??
    Math.max(result.result_1 ?? 0, result.result_2 ?? 0, result.result_3 ?? 0);
  return maxRes > 0 ? (maxRes / playerWeight) * 100 : -Infinity;
};

const calculateOneKbPressScore = (
  result?: OneKettlebellPressResultData | null,
  playerWeight?: number | null
): number => {
  if (!result || !playerWeight || playerWeight <= 0) return -Infinity;
  const percentage = result.bw_percentage_display;
  if (percentage != null && !isNaN(percentage)) return percentage;

  const maxRes =
    result.max_result_display ??
    Math.max(result.result_1 ?? 0, result.result_2 ?? 0, result.result_3 ?? 0);
  return maxRes > 0 ? (maxRes / playerWeight) * 100 : -Infinity;
};

const calculateTwoKbPressScore = (
  result?: TwoKettlebellPressResultData | null,
  playerWeight?: number | null
): number => {
  if (!result || !playerWeight || playerWeight <= 0) return -Infinity;
  const percentage = result.bw_percentage_display;
  if (percentage != null && !isNaN(percentage)) return percentage;

  const maxRes =
    result.max_result_display ??
    Math.max(result.result_1 ?? 0, result.result_2 ?? 0, result.result_3 ?? 0);
  return maxRes > 0 ? (maxRes / playerWeight) * 100 : -Infinity;
};

const createDisciplineColumns = (
  specificColumns: TableProps<OverallResult>["columns"] = []
): TableProps<OverallResult>["columns"] => {
  const safeSpecificColumns = Array.isArray(specificColumns)
    ? specificColumns
    : [];
  const mappedSpecificColumns: TableProps<OverallResult>["columns"] =
    safeSpecificColumns.map((col: any) => ({
      ...col,
      align: col.align || "right",
      width: col.width || 100,
      ellipsis: col.ellipsis ?? true,
    }));

  const columns: TableProps<OverallResult>["columns"] = [
    {
      title: "M-ce",
      key: "rank",
      width: 60,
      align: "center",
      fixed: "left",
      render: (
        _text: any,
        record: OverallResult & { calculatedRank?: number }
      ): number | string => record.calculatedRank ?? "-",
    },
    {
      title: "Zawodnik",
      key: "player",
      render: (_text: any, record: OverallResult): React.ReactNode => {
        const name = record.player?.name ?? "";
        const surname = record.player?.surname ?? "";
        return name || surname ? `${name} ${surname}`.trim() : "?";
      },
      sorter: (a: OverallResult, b: OverallResult): number => {
        const nameA = `${a.player?.name ?? ""} ${
          a.player?.surname ?? ""
        }`.trim();
        const nameB = `${b.player?.name ?? ""} ${
          b.player?.surname ?? ""
        }`.trim();
        return nameA.localeCompare(nameB);
      },
      width: 180,
      ellipsis: true,
    },
    {
      title: "Waga",
      dataIndex: ["player", "weight"],
      key: "weight",
      render: (w: number | null | undefined) => formatNumber(w, 1),
      sorter: (a: OverallResult, b: OverallResult): number =>
        (a.player?.weight ?? 0) - (b.player?.weight ?? 0),
      align: "right",
      width: 80,
    },
    ...mappedSpecificColumns,
  ];
  return columns ?? [];
};

const snatchCols = createDisciplineColumns([
  {
    title: "Waga Kettla",
    dataIndex: ["snatch_result", "kettlebell_weight"],
    key: "snatch_kettlebell",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Powt.",
    dataIndex: ["snatch_result", "repetitions"],
    key: "snatch_reps",
    render: (v: number | null | undefined) => v ?? 0,
  },
  {
    title: "Wynik",
    key: "snatch_score",
    render: (_: any, record: OverallResult) =>
      formatNumber(calculateSnatchScore(record.snatch_result), 1),
  },
]);

const tguCols = createDisciplineColumns([
  {
    title: "Próba 1",
    dataIndex: ["tgu_result", "result_1"],
    key: "tgu_r1",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Próba 2",
    dataIndex: ["tgu_result", "result_2"],
    key: "tgu_r2",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Próba 3",
    dataIndex: ["tgu_result", "result_3"],
    key: "tgu_r3",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Max (kg)",
    dataIndex: ["tgu_result", "max_result_display"],
    key: "tgu_max",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "% MC",
    dataIndex: ["tgu_result", "bw_percentage_display"],
    key: "tgu_perc",
    render: (v: number | null | undefined) => formatPercentage(v),
  },
]);

const kbsCols = createDisciplineColumns([
  {
    title: "Próba 1",
    dataIndex: ["kb_squat_result", "result_1"],
    key: "kbs_r1",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Próba 2",
    dataIndex: ["kb_squat_result", "result_2"],
    key: "kbs_r2",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Próba 3",
    dataIndex: ["kb_squat_result", "result_3"],
    key: "kbs_r3",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Max (kg)",
    dataIndex: ["kb_squat_result", "max_result_display"],
    key: "kbs_max",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "% MC",
    dataIndex: ["kb_squat_result", "bw_percentage_display"],
    key: "kbs_perc",
    render: (v: number | null | undefined) => formatPercentage(v),
  },
]);

const okbpCols = createDisciplineColumns([
  {
    title: "Próba 1",
    dataIndex: ["one_kettlebell_press_result", "result_1"],
    key: "okbp_r1",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Próba 2",
    dataIndex: ["one_kettlebell_press_result", "result_2"],
    key: "okbp_r2",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Próba 3",
    dataIndex: ["one_kettlebell_press_result", "result_3"],
    key: "okbp_r3",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Max (kg)",
    dataIndex: ["one_kettlebell_press_result", "max_result_display"],
    key: "okbp_max",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "% MC",
    dataIndex: ["one_kettlebell_press_result", "bw_percentage_display"],
    key: "okbp_perc",
    render: (v: number | null | undefined) => formatPercentage(v),
  },
]);

const tkbpCols = createDisciplineColumns([
  {
    title: "Próba 1",
    dataIndex: ["two_kettlebell_press_result", "result_1"],
    key: "tkbp_r1",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Próba 2",
    dataIndex: ["two_kettlebell_press_result", "result_2"],
    key: "tkbp_r2",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Próba 3",
    dataIndex: ["two_kettlebell_press_result", "result_3"],
    key: "tkbp_r3",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "Max (kg)",
    dataIndex: ["two_kettlebell_press_result", "max_result_display"],
    key: "tkbp_max",
    render: (v: number | null | undefined) => formatNumber(v, 1),
  },
  {
    title: "% MC",
    dataIndex: ["two_kettlebell_press_result", "bw_percentage_display"],
    key: "tkbp_perc",
    render: (v: number | null | undefined) => formatPercentage(v),
  },
]);

// --- Mapa dyscyplin ---
interface DisciplineMapEntry {
  name: string;
  dataKey: string;
  columns: TableProps<OverallResult>["columns"];
  calculateScore: (result: OverallResult) => number;
}

const disciplineMap: Record<string, DisciplineMapEntry> = {
  snatch: {
    name: "Snatch",
    dataKey: "snatch_result",
    columns: snatchCols,
    calculateScore: (r) => calculateSnatchScore(r.snatch_result),
  },
  tgu: {
    name: "Turkish Get-Up (TGU)",
    dataKey: "tgu_result",
    columns: tguCols,
    calculateScore: (r) => calculateTguScore(r.tgu_result, r.player?.weight),
  },
  kb_squat: {
    name: "Kettlebell Squat (KBS)",
    dataKey: "kb_squat_result",
    columns: kbsCols,
    calculateScore: (r) =>
      calculateKbSquatScore(
        getNestedValue(r, "kb_squat_result"),
        r.player?.weight
      ),
  },
  one_kettlebell_press: {
    name: "One Kettlebell Press (OKBP)",
    dataKey: "one_kettlebell_press_result",
    columns: okbpCols,
    calculateScore: (r) =>
      calculateOneKbPressScore(r.one_kettlebell_press_result, r.player?.weight),
  },
  two_kettlebell_press: {
    name: "Two Kettlebell Press (TKBP)",
    dataKey: "two_kettlebell_press_result",
    columns: tkbpCols,
    calculateScore: (r) =>
      calculateTwoKbPressScore(
        getNestedValue(r, "two_kettlebell_press_result"),
        r.player?.weight
      ),
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
    const lowerCaseFilter = filterTerm.toLowerCase().trim();
    if (!lowerCaseFilter) return results;
    return results.filter((result: OverallResult) => {
      const playerName = result.player?.name?.toLowerCase() ?? "";
      const playerSurname = result.player?.surname?.toLowerCase() ?? "";
      const playerClub = result.player?.club_name?.toLowerCase() ?? "";
      const fullName = `${playerName} ${playerSurname}`.trim();
      return (
        fullName.includes(lowerCaseFilter) ||
        playerClub.includes(lowerCaseFilter)
      );
    });
  }, [results, filterTerm]);

  const renderAntdTable = (
    title: string,
    dataSource: (OverallResult & { calculatedRank?: number })[],
    columns: TableProps<OverallResult>["columns"],
    rowKeySuffix: string,
    isOverallTable: boolean = false
  ) => {
    if (!dataSource || dataSource.length === 0) {
      if (filterTerm && results.length > 0) {
        return (
          <Paragraph
            key={rowKeySuffix}
            style={{ marginTop: "1rem", textAlign: "center" }}
          >
            {" "}
            Brak zawodników pasujących do filtra "{filterTerm}" dla: {title}{" "}
          </Paragraph>
        );
      }
      if (!isOverallTable && !filterTerm) return null;
      return (
        <Paragraph
          key={rowKeySuffix}
          style={{ marginTop: "1rem", textAlign: "center" }}
        >
          {" "}
          Brak wyników{" "}
          {filterTerm ? ` pasujących do filtra "${filterTerm}"` : ""} w tej
          kategorii.{" "}
        </Paragraph>
      );
    }

    return (
      <section key={rowKeySuffix} style={{ marginBottom: "2rem" }}>
        <Title
          level={isOverallTable ? 2 : 3}
          className={styles.disciplineTableTitle}
        >
          {" "}
          {title}{" "}
        </Title>
        <Table
          dataSource={dataSource}
          columns={columns}
          rowKey={(record: OverallResult) =>
            record?.player?.id
              ? `${record.player.id}-${rowKeySuffix}`
              : `${Math.random()}-${rowKeySuffix}`
          }
          pagination={
            isOverallTable
              ? {
                  pageSize: 20,
                  showSizeChanger: true,
                  pageSizeOptions: ["10", "20", "50", "100"],
                  hideOnSinglePage: true,
                  showTotal: (total: number, range: [number, number]) =>
                    `${range[0]}-${range[1]} z ${total} zawodników`,
                }
              : false
          }
          size="middle"
          bordered
          scroll={{ x: "max-content" }}
          loading={isOverallTable && isLoading && !isFetching}
        />
      </section>
    );
  };

  const now = new Date();
  const showOverallResults = now >= OVERALL_RESULTS_VISIBLE_AFTER;

  if (isLoading && !data) {
    return (
      <div className={styles.centered}>
        {" "}
        <Spin
          size="large"
          tip={`Ładowanie danych kategorii ${categoryId}...`}
        />{" "}
      </div>
    );
  }

  if (isError && results.length === 0) {
    return (
      <div className={styles.categoryContainer}>
        <Button
          type="link"
          icon={<ArrowLeftOutlined />}
          href="/"
          className={styles.backButton}
        >
          {" "}
          Powrót do listy kategorii{" "}
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

  const hasCategoryData = !!categoryInfo;
  const hasResultsData = results.length > 0;

  return (
    <div className={styles.categoryContainer}>
      <Button
        type="link"
        icon={<ArrowLeftOutlined />}
        href="/"
        className={styles.backButton}
      >
        {" "}
        Powrót do listy kategorii{" "}
      </Button>

      <Title level={2} className={styles.categoryTitle}>
        Wyniki:{" "}
        {categoryInfo?.name ||
          (categoryId ? `Kategoria ${categoryId}` : "Ładowanie...")}
        {isFetching && <Spin size="small" style={{ marginLeft: "10px" }} />}
      </Title>
      {hasCategoryData && categoryInfo?.disciplines?.length > 0 && (
        <Paragraph
          type="secondary"
          className={styles.categoryDisciplines}
        ></Paragraph>
      )}

      <Search
        placeholder="Filtruj po nazwisku, imieniu lub klubie..."
        allowClear
        enterButton="Filtruj"
        size="large"
        onSearch={(value) => setFilterTerm(value)}
        onChange={(e) => !e.target.value && setFilterTerm("")}
        className={styles.filterInput}
        disabled={!hasResultsData}
      />
      {isError && hasResultsData && (
        <Alert
          message="Nie udało się odświeżyć danych"
          description="Wyświetlane są ostatnie znane wyniki. Odświeżenie nastąpi automatycznie."
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
          "overall",
          true
        )
      ) : (
        <div
          className={styles.timeGateMessage}
          style={{
            padding: "20px",
            textAlign: "center",
            border: "1px dashed #ccc",
            margin: "20px 0",
            borderRadius: "4px",
          }}
        >
          <Paragraph style={{ fontStyle: "italic", color: "#FFFFFF" }}>
            Pełna klasyfikacja będzie dostępna po{" "}
            {OVERALL_RESULTS_VISIBLE_AFTER.toLocaleTimeString("pl-PL", {
              hour: "2-digit",
              minute: "2-digit",
            })}
            .
          </Paragraph>
          <Paragraph
            type="secondary"
            style={{ fontSize: "0.9em", color: "#FFFFFF" }}
          >
            (Po tym czasie należy odświeżyć stronę / Please refresh the page
            after this time)
          </Paragraph>
        </div>
      )}

      {hasCategoryData &&
        categoryInfo?.disciplines &&
        categoryInfo.disciplines.length > 0 && (
          <div className={styles.disciplinesSection}>
            <Title
              level={2}
              style={{ marginTop: "2rem", marginBottom: "1rem" }}
            >
              Wyniki w Dyscyplinach
            </Title>
            {categoryInfo.disciplines.map((disciplineApiKey) => {
              const mappingInfo = disciplineMap[disciplineApiKey];
              if (!mappingInfo) {
                console.warn(
                  `Nie znaleziono mapowania dla klucza dyscypliny z API: ${disciplineApiKey}`
                );
                return (
                  <Alert
                    key={disciplineApiKey}
                    message={`Brak konfiguracji dla dyscypliny: ${disciplineApiKey}`}
                    type="warning"
                    style={{ marginBottom: "1rem" }}
                  />
                );
              }

              const sourceForDiscipline = filteredResults.filter(
                (r: OverallResult) =>
                  r &&
                  getNestedValue(r, mappingInfo.dataKey, undefined) !==
                    undefined
              );

              if (sourceForDiscipline.length === 0) {
                return null;
              }

              // 1. Sortowanie (wg score, tiebreak, nazwiska)
              const sortedDisciplineDataSource = [...sourceForDiscipline].sort(
                (a: OverallResult, b: OverallResult) => {
                  const scoreA = mappingInfo.calculateScore(a);
                  const scoreB = mappingInfo.calculateScore(b);
                  const finalScoreA = isNaN(scoreA) ? -Infinity : scoreA;
                  const finalScoreB = isNaN(scoreB) ? -Infinity : scoreB;

                  if (finalScoreA > finalScoreB) return -1; // DESC score
                  if (finalScoreA < finalScoreB) return 1;

                  const tieA = a.tiebreak_points ?? -Infinity;
                  const tieB = b.tiebreak_points ?? -Infinity;
                  if (tieA > tieB) return -1; // DESC tiebreak
                  if (tieA < tieB) return 1;

                  const nameA = `${a.player?.name ?? ""} ${
                    a.player?.surname ?? ""
                  }`.trim();
                  const nameB = `${b.player?.name ?? ""} ${
                    b.player?.surname ?? ""
                  }`.trim();
                  return nameA.localeCompare(nameB); // ASC name
                }
              );

              // 2. Obliczanie poprawnych miejsc (rankingu) z obsługą remisów
              let currentRank = 0;
              let previousScore = NaN;
              let previousTiebreak = NaN;

              const dataSourceWithRank = sortedDisciplineDataSource.map(
                (record, index) => {
                  const currentScore = mappingInfo.calculateScore(record);
                  const currentTiebreak = record.tiebreak_points ?? -Infinity;

                  // Porównaj z poprzednim - jeśli score LUB tiebreak są różne, to jest nowe miejsce
                  if (
                    currentScore !== previousScore ||
                    currentTiebreak !== previousTiebreak
                  ) {
                    currentRank = index + 1; // Nowy rank to index+1
                    previousScore = currentScore;
                    previousTiebreak = currentTiebreak;
                  }
                  // Jeśli score i tiebreak są takie same, currentRank pozostaje bez zmian

                  return {
                    ...record,
                    calculatedRank: currentRank, // Dodaj obliczone miejsce do rekordu
                  };
                }
              );

              // 3. Renderowanie tabeli
              return renderAntdTable(
                mappingInfo.name,
                dataSourceWithRank,
                mappingInfo.columns,
                mappingInfo.dataKey.toString()
              );
            })}
          </div>
        )}

      {/* Komunikaty końcowe */}
      {filterTerm && filteredResults.length === 0 && hasResultsData && (
        <Paragraph style={{ textAlign: "center", marginTop: "2rem" }}>
          {" "}
          Brak zawodników pasujących do filtra "{filterTerm}".{" "}
        </Paragraph>
      )}
      {!isLoading && !isError && !hasResultsData && !filterTerm && (
        <Paragraph style={{ textAlign: "center", marginTop: "2rem" }}>
          {" "}
          Brak wyników w tej kategorii.{" "}
        </Paragraph>
      )}
    </div>
  );
};

export default CategoryPage;
