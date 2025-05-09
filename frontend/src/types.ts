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
  result_score: number | null;
  position?: number | null;
}

export interface TGUResultData {
  result_1: number | null;
  result_2: number | null;
  result_3: number | null;
  max_result_display: number | null;
  bw_percentage_display: number | null;
  position?: number | null;
}

export interface OneKettlebellPressResultData {
  result_1: number | null;
  result_2: number | null;
  result_3: number | null;
  max_result_display: number | null;
  bw_percentage_display: number | null;
  position?: number | null;
}
export interface KBSquatResultData {
  result_1: number | null;
  result_2: number | null;
  result_3: number | null;
  max_result_display: number | null;
  bw_percentage_display: number | null;
  position?: number | null;
}

export interface TwoKettlebellPressResultData {
  result_1: number | null;
  result_2: number | null;
  result_3: number | null;
  max_result_display: number | null;
  bw_percentage_display: number | null;
  position?: number | null;
}

export interface OverallResult {
  final_position: number | null;
  player: PlayerBasicInfo;
  total_points: number | null;
  snatch_points?: number | null;
  tgu_points?: number | null;
  kb_squat_points?: number | null;
  one_kb_press_points?: number | null;
  two_kb_press_points?: number | null;
  tiebreak_points?: number | null;

  snatch_result: SnatchResultData | null;
  tgu_result: TGUResultData | null;
  kb_squat_result: KBSquatResultData | null;
  one_kettlebell_press_result: OneKettlebellPressResultData | null;
  two_kettlebell_press_result: TwoKettlebellPressResultData | null;
}

export type CategoryResultsResponse = OverallResult[];
