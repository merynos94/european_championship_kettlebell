export interface Category {
  id: number;
  name: string;
  disciplines: string[];
}

export interface PlayerBasicInfo {
  id: number;
  name: string;
  surname: string;
  club_name: string | null;
  weight: number | null;
}

export interface SnatchResultData {
  kettlebell_weight: number | null;
  repetitions: number | null;
  result_score: number;
  position: number | null;
}

export interface TGUResultData {
  result_1: number | null;
  result_2: number | null;
  result_3: number | null;
  max_result_val: number;
  bw_percentage_val: number;
  position: number | null;
}

export interface OneKettlebellPressResultData {
  result_1: number | null;
  result_2: number | null;
  result_3: number | null;
  max_result_val: number;
  bw_percentage_val: number;
  position: number | null;
}

export interface PistolSquatResultData {
  result_1: number | null;
  result_2: number | null;
  result_3: number | null;
  max_result_val: number;
  bw_percentage_val: number;
  position: number | null;
}

export interface SeeSawPressResultData {
  result_left_1: number | null;
  result_right_1: number | null;
  result_left_2: number | null;
  result_right_2: number | null;
  result_left_3: number | null;
  result_right_3: number | null;
  max_score_val: number;
  bw_percentage_val: number;
  position: number | null;
}

export interface KBSquatResultData {
  result_1: number | null; // Dodane
  result_2: number | null; // Dodane
  result_3: number | null; // Dodane
  max_result_val: number; // Dodane/Zmienione z max_score_val? Sprawdź API!
  bw_percentage_val: number;
  position: number | null; // Jeśli API nadal to zwraca
  // Usuń stare pola jeśli ich nie ma: result_left_1, result_right_1 etc.
}

export interface TwoKettlebellPressResultData {
  result_1: number | null; // Dodane
  result_2: number | null; // Dodane
  result_3: number | null; // Dodane
  max_result_val: number; // Dodane/Zmienione z max_score_val? Sprawdź API!
  bw_percentage_val: number;
  position: number | null; // Jeśli API nadal to zwraca
  // Usuń stare pola jeśli ich nie ma: result_left_1, result_right_1 etc.
}

export interface OverallResult {
  final_position: number | null;
  player: PlayerBasicInfo;
  total_points: number;
  snatch_points: number;
  tgu_points: number;
  see_saw_press_points: number;
  kb_squat_points: number;
  pistol_squat_points: number;
  one_kb_press_points: number;
  two_kb_press_points: number;
  tiebreak_points: number;

  snatch_result: SnatchResultData | null;
  tgu_result: TGUResultData | null;
  see_saw_press_result: SeeSawPressResultData | null;
  kb_squat_result: KBSquatResultData | null;
  pistol_squat_result: PistolSquatResultData | null;
  one_kettlebell_press_result: OneKettlebellPressResultData | null;
  two_kettlebell_press_result: TwoKettlebellPressResultData | null;
}

export type CategoryResultsResponse = OverallResult[];
