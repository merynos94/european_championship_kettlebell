// src/pages/CategoryPage.tsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../services/api';
import { CategoryResultsResponse, OverallResult, Category } from '../types';
import styles from './CategoryPage.module.css'; // Importujemy CSS Module

const CategoryPage: React.FC = () => {
  const { categoryId } = useParams<{ categoryId: string }>();
  const [results, setResults] = useState<CategoryResultsResponse>([]);
  const [categoryInfo, setCategoryInfo] = useState<Category | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!categoryId) return;

    const fetchCategoryData = async () => {
      try {
        setLoading(true);
        setError(null);
        setResults([]);
        setCategoryInfo(null);

        const [catInfoResponse, resultsResponse] = await Promise.all([
          apiClient.get<Category>(`/categories/${categoryId}/`),
          apiClient.get<CategoryResultsResponse>(`/categories/${categoryId}/results/`)
        ]);

        setCategoryInfo(catInfoResponse.data);
        const sortedResults = resultsResponse.data.sort((a, b) => (a.final_position ?? 999) - (b.final_position ?? 999));
        setResults(sortedResults);

      } catch (err) {
        console.error(`Error fetching data for category ${categoryId}:`, err);
        setError(`Nie udało się załadować danych dla kategorii ${categoryId}. Spróbuj odświeżyć stronę.`);
      } finally {
        setLoading(false);
      }
    };

    fetchCategoryData();
  }, [categoryId]);

  // Funkcje pomocnicze bez zmian
  const formatNumber = (value: number | null | undefined, digits: number = 1): string => {
    if (value == null) return '-';
    return value.toFixed(digits);
  };
   const formatPercentage = (value: number | null | undefined): string => {
     if (value == null) return '-';
     return `${value.toFixed(2)}%`;
   };

  // Funkcja do renderowania tabeli dla konkretnej dyscypliny
  // Zapobiega powtarzaniu kodu
  const renderDisciplineTable = (
      disciplineName: string,
      resultKey: keyof OverallResult, // Klucz do obiektu z wynikiem dyscypliny
      columns: { header: string; dataKey: string; format?: (value: any) => string }[], // Definicja kolumn
      sortPositionKey: string // Klucz do pozycji w danej dyscyplinie (np. 'snatch_result.position')
  ) => {
      const filteredResults = results
          .filter(r => r[resultKey]) // Bierzemy tylko tych co mają wynik
          .sort((a: OverallResult, b: OverallResult) => {
              // Bezpieczne pobieranie zagnieżdżonej pozycji
              const posA = sortPositionKey.split('.').reduce((o, k) => o?.[k], a) ?? 999;
              const posB = sortPositionKey.split('.').reduce((o, k) => o?.[k], b) ?? 999;
              return (posA as number) - (posB as number);
          });

      if (filteredResults.length === 0) {
          return null; // Nie renderuj tabeli, jeśli nie ma wyników
      }

      return (
          <>
              <h2>Wyniki - {disciplineName}</h2>
              <div className={styles.tableContainer}> {/* Wrapper dla responsywności */}
                  <table className={styles.resultsTable}> {/* Używamy klasy CSS Module */}
                      <thead>
                          <tr>
                              <th>Zawodnik</th>
                              {columns.map(col => <th key={col.header}>{col.header}</th>)}
                              <th>Pozycja ({disciplineName})</th>
                          </tr>
                      </thead>
                      <tbody>
                          {filteredResults.map(result => {
                              const disciplineResult = result[resultKey] as any; // Wynik konkretnej dyscypliny
                              const position = sortPositionKey.split('.').reduce((o, k) => o?.[k], result) ?? '-';

                              return (
                                  <tr key={result.player.id + '-' + resultKey}>
                                      <td>{result.player.name} {result.player.surname}</td>
                                      {columns.map(col => {
                                           // Bezpieczne pobieranie zagnieżdżonych danych
                                           const value = col.dataKey.split('.').reduce((o, k) => o?.[k], disciplineResult);
                                           return <td key={col.dataKey}>{col.format ? col.format(value) : (value ?? '-')}</td>;
                                      })}
                                      <td>{position}</td>
                                  </tr>
                              );
                          })}
                      </tbody>
                  </table>
              </div>
          </>
      );
  };


  return (
    <div className={styles.categoryContainer}>
      <Link to="/" className={styles.backLink}>{'<'} Powrót do listy kategorii</Link>
      <h1 className={styles.categoryTitle}>
        Wyniki: {categoryInfo?.name || (loading ? 'Ładowanie...' : `Kategoria ${categoryId}`)}
      </h1>
      {categoryInfo && <p className={styles.categoryDisciplines}>Dyscypliny: {categoryInfo.disciplines.join(', ')}</p>}

      {loading && <div className="loading-message">Ładowanie wyników...</div>}
      {error && <div className="error-message">{error}</div>}

      {!loading && !error && (
        <>
          <h2>Klasyfikacja Generalna</h2>
          {results.length > 0 ? (
            <div className={styles.tableContainer}> {/* Wrapper dla responsywności */}
              <table className={styles.resultsTable}> {/* Używamy klasy CSS Module */}
                <thead>
                  <tr>
                    <th>Miejsce</th>
                    <th>Zawodnik</th>
                    <th>Klub</th>
                    <th className={styles.textRight}>Waga (kg)</th>
                    <th className={styles.textRight}>Punkty Ogółem</th>
                    <th className={styles.textRight}>Pkt Snatch</th>
                    <th className={styles.textRight}>Pkt TGU</th>
                    <th className={styles.textRight}>Pkt SSP</th>
                    <th className={styles.textRight}>Pkt KBS</th>
                    <th className={styles.textRight}>Pkt Pistol</th>
                    <th className={styles.textRight}>Pkt OKBP</th>
                    <th className={styles.textRight}>Pkt TKBP</th>
                    <th className={styles.textRight}>Pkt Tiebreak</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => (
                    <tr key={result.player.id + '-overall'}>
                      <td>{result.final_position ?? '-'}</td>
                      <td>{result.player.name} {result.player.surname}</td>
                      <td>{result.player.club_name || '-'}</td>
                      <td className={styles.textRight}>{formatNumber(result.player.weight, 1)}</td>
                      <td className={`${styles.textRight} ${styles.bold}`}>{formatNumber(result.total_points, 1)}</td> {/* Pogrubienie sumy */}
                      <td className={styles.textRight}>{formatNumber(result.snatch_points, 1)}</td>
                      <td className={styles.textRight}>{formatNumber(result.tgu_points, 1)}</td>
                      <td className={styles.textRight}>{formatNumber(result.see_saw_press_points, 1)}</td>
                      <td className={styles.textRight}>{formatNumber(result.kb_squat_points, 1)}</td>
                      <td className={styles.textRight}>{formatNumber(result.pistol_squat_points, 1)}</td>
                      <td className={styles.textRight}>{formatNumber(result.one_kb_press_points, 1)}</td>
                      <td className={styles.textRight}>{formatNumber(result.two_kb_press_points, 1)}</td>
                      <td className={styles.textRight}>{formatNumber(result.tiebreak_points, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>Brak wyników do wyświetlenia dla tej kategorii.</p>
          )}

          {/* Renderowanie tabel dyscyplin za pomocą funkcji pomocniczej */}
          {renderDisciplineTable('Snatch', 'snatch_result', [
              { header: 'Waga odważnika (kg)', dataKey: 'kettlebell_weight', format: (v) => formatNumber(v) },
              { header: 'Powtórzenia', dataKey: 'repetitions', format: (v) => v ?? 0 },
              { header: 'Wynik (obl.)', dataKey: 'result_score', format: (v) => formatNumber(v) }
          ], 'snatch_result.position')}

          {renderDisciplineTable('Turkish Get-Up (TGU)', 'tgu_result', [
              { header: 'Max Wynik (kg)', dataKey: 'max_result_val', format: (v) => formatNumber(v) },
              { header: '% Masy Ciała', dataKey: 'bw_percentage_val', format: (v) => formatPercentage(v) }
          ], 'tgu_result.position')}

          {renderDisciplineTable('See Saw Press (SSP)', 'see_saw_press_result', [
              { header: 'Max Wynik (kg)', dataKey: 'max_score_val', format: (v) => formatNumber(v) },
              { header: '% Masy Ciała', dataKey: 'bw_percentage_val', format: (v) => formatPercentage(v) }
          ], 'see_saw_press_result.position')}

           {renderDisciplineTable('Kettlebell Squat (KBS)', 'kb_squat_result', [
               { header: 'Max Wynik (kg)', dataKey: 'max_score_val', format: (v) => formatNumber(v) },
               { header: '% Masy Ciała', dataKey: 'bw_percentage_val', format: (v) => formatPercentage(v) }
           ], 'kb_squat_result.position')}

           {renderDisciplineTable('Pistol Squat', 'pistol_squat_result', [
               { header: 'Max Wynik (kg)', dataKey: 'max_result_val', format: (v) => formatNumber(v) },
               { header: '% Masy Ciała', dataKey: 'bw_percentage_val', format: (v) => formatPercentage(v) }
           ], 'pistol_squat_result.position')}

           {renderDisciplineTable('One Kettlebell Press (OKBP)', 'one_kettlebell_press_result', [
               { header: 'Max Wynik (kg)', dataKey: 'max_result_val', format: (v) => formatNumber(v) },
               { header: '% Masy Ciała', dataKey: 'bw_percentage_val', format: (v) => formatPercentage(v) }
           ], 'one_kettlebell_press_result.position')}

           {renderDisciplineTable('Two Kettlebell Press (TKBP)', 'two_kettlebell_press_result', [
               { header: 'Max Wynik (kg)', dataKey: 'max_score_val', format: (v) => formatNumber(v) },
               { header: '% Masy Ciała', dataKey: 'bw_percentage_val', format: (v) => formatPercentage(v) }
           ], 'two_kettlebell_press_result.position')}

          {/* Stopka jest teraz w komponencie Layout */}
        </>
      )}
    </div>
  );
};

export default CategoryPage;