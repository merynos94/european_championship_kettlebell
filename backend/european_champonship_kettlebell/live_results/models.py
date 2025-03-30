from django.db import models
from django.db.models.functions import Greatest

# snatch - powtórzenia * ciężar test, tgu - one rep /%BW, one kettlebell press - 3 próby /%BW, kb_squat -3proby (2x)/%BW, press (2x)/%bw - 3 próby


# Discipline constants
SNATCH = "snatch"
TGU = "tgu"
ONE_KB_PRESS = "one_kettlebell_press"
KB_SQUAT_2X = "kb_squat_2x"
TWO_KB_PRESS = "two_kettlebell_press"

AVAILABLE_DISCIPLINES = [
    (SNATCH, "Snatch"),
    (TGU, "Turkish Get-Up"),
    (ONE_KB_PRESS, "One Kettlebell Press"),
    (KB_SQUAT_2X, "Kettlebell Squat x2"),
    (TWO_KB_PRESS, "Two Kettlebells Press"),
]


class SportClub(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    disciplines = models.JSONField(default=list)

    def __str__(self):
        return self.name

    def set_disciplines(self, disciplines):
        valid_disciplines = [d[0] for d in AVAILABLE_DISCIPLINES]
        self.disciplines = [d for d in disciplines if d in valid_disciplines]
        self.save()

    def get_disciplines(self):
        return self.disciplines


class Player(models.Model):
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    weight = models.FloatField(null=True, blank=True, default=0)
    club = models.ForeignKey(SportClub, on_delete=models.CASCADE)
    categories = models.ManyToManyField(Category)

    snatch_kettlebell_weight = models.FloatField(null=True, blank=True, default=0)
    snatch_repetitions = models.IntegerField(null=True, blank=True, default=0)

    tgu_weight_1 = models.FloatField(null=True, blank=True, default=0)
    tgu_weight_2 = models.FloatField(null=True, blank=True, default=0)
    tgu_weight_3 = models.FloatField(null=True, blank=True, default=0)

    see_saw_press_weight_left_1 = models.FloatField(null=True, blank=True, default=0)
    see_saw_press_weight_left_2 = models.FloatField(null=True, blank=True, default=0)
    see_saw_press_weight_left_3 = models.FloatField(null=True, blank=True, default=0)
    see_saw_press_weight_right_1 = models.FloatField(null=True, blank=True, default=0)
    see_saw_press_weight_right_2 = models.FloatField(null=True, blank=True, default=0)
    see_saw_press_weight_right_3 = models.FloatField(null=True, blank=True, default=0)

    kb_squat_weight_left_1 = models.FloatField(null=True, blank=True, default=0)
    kb_squat_weight_left_2 = models.FloatField(null=True, blank=True, default=0)
    kb_squat_weight_left_3 = models.FloatField(null=True, blank=True, default=0)
    kb_squat_weight_right_1 = models.FloatField(null=True, blank=True, default=0)
    kb_squat_weight_right_2 = models.FloatField(null=True, blank=True, default=0)
    kb_squat_weight_right_3 = models.FloatField(null=True, blank=True, default=0)

    pistol_squat_weight_1 = models.FloatField(null=True, blank=True, default=0)
    pistol_squat_weight_2 = models.FloatField(null=True, blank=True, default=0)
    pistol_squat_weight_3 = models.FloatField(null=True, blank=True, default=0)
    tiebreak = models.BooleanField(default=False)

    _updating_results = False

    def calculate_bw_percentage(self, weight):
        return (weight / self.weight) * 100 if self.weight else 0

    def update_results(self):
        if self._updating_results:
            return
        self._updating_results = True
        try:
            self._update_snatch_result()
            self._update_tgu_result()
            self._update_see_saw_press_result()
            self._update_kb_squat_result()
            self._update_best_kb_squat_result()
            self._update_best_see_saw_press_result()
            self._update_pistol_squat_result()
            self._update_overall_result()
        finally:
            self._updating_results = False

    def kb_squat_body_percent_weight(self, side, attempt):
        weight = getattr(self, f"kb_squat_weight_{side}_{attempt}")
        return weight

    def _update_snatch_result(self):
        snatch_result, _ = SnatchResult.objects.get_or_create(player=self)
        snatch_result.result = round(self.snatch_results() or 0, 1)
        snatch_result.save()

    def _update_tgu_result(self):
        tgu_result, _ = TGUResult.objects.get_or_create(player=self)
        tgu_result.result_1 = self.tgu_weight_1 or 0
        tgu_result.result_2 = self.tgu_weight_2 or 0
        tgu_result.result_3 = self.tgu_weight_3 or 0
        tgu_result.save()

    def _update_pistol_squat_result(self):
        pistol_squat_result, _ = PistolSquatResult.objects.get_or_create(player=self)
        pistol_squat_result.result_1 = self.pistol_squat_weight_1 or 0
        pistol_squat_result.result_2 = self.pistol_squat_weight_2 or 0
        pistol_squat_result.result_3 = self.pistol_squat_weight_3 or 0
        pistol_squat_result.save()

    def _update_see_saw_press_result(self):
        see_saw_result, _ = SeeSawPressResult.objects.get_or_create(player=self)
        for side in ["left", "right"]:
            for attempt in range(1, 4):
                setattr(
                    see_saw_result,
                    f"result_{side}_{attempt}",
                    round(
                        getattr(self, f"see_saw_press_body_percent_weight_{side}")(attempt) or 0,
                        1,
                    ),
                )
        see_saw_result.save()

    def _update_kb_squat_result(self):
        kb_squat_result, _ = KBSquatResult.objects.get_or_create(player=self)
        for side in ["left", "right"]:
            for attempt in range(1, 4):
                setattr(
                    kb_squat_result,
                    f"result_{side}_{attempt}",
                    self.kb_squat_body_percent_weight(side, attempt),
                )
        kb_squat_result.save()

    def _update_best_kb_squat_result(self):
        best_kb_squat_result, _ = BestKBSquatResult.objects.get_or_create(player=self)
        best_kb_squat_result.update_best_result()

    def _update_best_see_saw_press_result(self):
        best_see_saw_result, _ = BestSeeSawPressResult.objects.get_or_create(player=self)
        best_see_saw_result.update_best_results()

    def _update_overall_result(self):
        for category in self.categories.all():
            update_overall_results(category)

    def get_max_pistol_squat_weight(self):
        return max(
            self.pistol_squat_weight_1 or 0,
            self.pistol_squat_weight_2 or 0,
            self.pistol_squat_weight_3 or 0,
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self._updating_results:
            self.update_results()

    def __str__(self):
        return f"{self.name} {self.surname}"

    def snatch_results(self):
        if self.snatch_kettlebell_weight and self.snatch_repetitions:
            return self.snatch_kettlebell_weight * self.snatch_repetitions
        return None

    def tgu_body_percent_weight(self):
        max_tgu_weight = max(self.tgu_weight_1 or 0, self.tgu_weight_2 or 0, self.tgu_weight_3 or 0)
        return (max_tgu_weight / self.weight) * 100 if max_tgu_weight and self.weight else None

    def get_max_tgu_weight(self):
        return max(self.tgu_weight_1 or 0, self.tgu_weight_2 or 0, self.tgu_weight_3 or 0)

    def see_saw_press_body_percent_weight_left(self, attempt):
        weight = getattr(self, f"see_saw_press_weight_left_{attempt}")
        return weight if weight and self.weight else None

    def see_saw_press_body_percent_weight_right(self, attempt):
        weight = getattr(self, f"see_saw_press_weight_right_{attempt}")
        return weight if weight and self.weight else None


class SnatchResult(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    result = models.FloatField(null=True, blank=True)
    position = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.player} - Snatch: {self.result if self.result is not None else 'N/A'}"


class TGUResult(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    result_1 = models.FloatField(default=0)
    result_2 = models.FloatField(default=0)
    result_3 = models.FloatField(default=0)
    position = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.player} - TGU Results"

    def get_max_result(self):
        return max(self.result_1 or 0, self.result_2 or 0, self.result_3 or 0)

    # def calculate_bw_percentage(self):
    #     if self.player.weight:
    #         max_result = self.get_max_result()
    #         return (max_result / self.player.weight) * 100
    #     return 0
    def calculate_bw_percentage(self):
        return self.player.calculate_bw_percentage(self.get_max_result())


class PistolSquatResult(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    result_1 = models.FloatField(default=0)
    result_2 = models.FloatField(default=0)
    result_3 = models.FloatField(default=0)
    position = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.player} - Pistol Squat Results"

    def get_max_result(self):
        return max(self.result_1 or 0, self.result_2 or 0, self.result_3 or 0)

    # def calculate_bw_percentage(self):
    #     if self.player.weight:
    #         max_result = self.get_max_result()
    #         return (max_result / self.player.weight) * 100
    #     return 0
    def calculate_bw_percentage(self):
        return self.player.calculate_bw_percentage(self.get_max_result())


class SeeSawPressResult(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    result_left_1 = models.FloatField(default=0)
    result_right_1 = models.FloatField(default=0)
    result_left_2 = models.FloatField(default=0)
    result_right_2 = models.FloatField(default=0)
    result_left_3 = models.FloatField(default=0)
    result_right_3 = models.FloatField(default=0)
    position = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.player} - See Saw Press Results"

    def get_attempt_result(self, attempt_number):
        left = getattr(self, f"result_left_{attempt_number}")
        right = getattr(self, f"result_right_{attempt_number}")
        return (left * 3) + (right * 3) if left > 0 and right > 0 else 0

    def get_max_result(self):
        valid_attempts = [
            self.result_left_1 + self.result_right_1 if self.result_left_1 > 0 and self.result_right_1 > 0 else 0,
            self.result_left_2 + self.result_right_2 if self.result_left_2 > 0 and self.result_right_2 > 0 else 0,
            self.result_left_3 + self.result_right_3 if self.result_left_3 > 0 and self.result_right_3 > 0 else 0,
        ]
        return max(valid_attempts)

    def calculate_bw_percentage(self):
        return self.player.calculate_bw_percentage(self.get_max_result())


class BestSeeSawPressResult(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE)
    best_left = models.FloatField(default=0)
    best_right = models.FloatField(default=0)

    def update_best_results(self):
        see_saw_result = self.player.seesawpressresult_set.first()
        if see_saw_result:
            self.best_left = max(
                see_saw_result.result_left_1,
                see_saw_result.result_left_2,
                see_saw_result.result_left_3,
            )
            self.best_right = max(
                see_saw_result.result_right_1,
                see_saw_result.result_right_2,
                see_saw_result.result_right_3,
            )
            self.save()

    def __str__(self):
        return f"{self.player} - Best See Saw Press: Left {self.best_left}, Right {self.best_right}"


class KBSquatResult(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    result_left_1 = models.FloatField(default=0)
    result_right_1 = models.FloatField(default=0)
    result_left_2 = models.FloatField(default=0)
    result_right_2 = models.FloatField(default=0)
    result_left_3 = models.FloatField(default=0)
    result_right_3 = models.FloatField(default=0)
    position = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.player} - KB Squat Results"

    def get_max_result(self):
        valid_attempts = [
            self.result_left_1 + self.result_right_1 if self.result_left_1 > 0 and self.result_right_1 > 0 else 0,
            self.result_left_2 + self.result_right_2 if self.result_left_2 > 0 and self.result_right_2 > 0 else 0,
            self.result_left_3 + self.result_right_3 if self.result_left_3 > 0 and self.result_right_3 > 0 else 0,
        ]
        return max(valid_attempts)

    def calculate_bw_percentage(self):
        return self.player.calculate_bw_percentage(self.get_max_result())

    def get_attempt_result(self, attempt_number):
        left = getattr(self, f"result_left_{attempt_number}")
        right = getattr(self, f"result_right_{attempt_number}")
        return max(left, right) if left > 0 and right > 0 else 0


class BestKBSquatResult(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE)
    best_result = models.FloatField(default=0)

    def update_best_result(self):
        kb_squat_result = self.player.kbsquatresult_set.first()
        if kb_squat_result:
            self.best_result = kb_squat_result.get_max_result()
            self.save()

    def __str__(self):
        return f"{self.player} - Best KB Squat: {self.best_result}"


class OverallResult(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE)
    snatch_points = models.FloatField(default=0)
    tgu_points = models.FloatField(default=0)
    see_saw_press_points = models.FloatField(default=0)
    kb_squat_points = models.FloatField(default=0)
    pistol_squat_points = models.FloatField(default=0)
    tiebreak_points = models.FloatField(default=0)
    total_points = models.FloatField(default=0)
    final_position = models.IntegerField(null=True, blank=True)

    def calculate_total_points(self):
        self.total_points = round(
            self.snatch_points
            + self.tgu_points
            + self.see_saw_press_points
            + self.kb_squat_points
            + self.pistol_squat_points
            + self.tiebreak_points,
            1,
        )

    def save(self, *args, **kwargs):
        self.calculate_total_points()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.player} - Total: {self.total_points:.1f}"


from django.db.models import Case, F, FloatField, When


def update_overall_results(category):
    disciplines = category.get_disciplines()
    players = Player.objects.filter(categories=category)

    for player in players:
        overall_result, created = OverallResult.objects.get_or_create(player=player)
        overall_result.snatch_points = 0
        overall_result.tgu_points = 0
        overall_result.see_saw_press_points = 0
        overall_result.kb_squat_points = 0
        overall_result.pistol_squat_points = 0
        overall_result.tiebreak_points = 0
        overall_result.total_points = 0
        overall_result.final_position = None
        overall_result.save()

    discipline_models = {
        SNATCH: SnatchResult,
        TGU: TGUResult,
        SEE_SAW_PRESS: SeeSawPressResult,
        KB_SQUAT: KBSquatResult,
        PISTOL_SQUAT: PistolSquatResult,
    }

    for discipline in disciplines:
        if discipline in discipline_models:
            model = discipline_models[discipline]
            if discipline == SNATCH:
                results = model.objects.filter(player__in=players).order_by("-result")
            else:
                if discipline in [TGU, PISTOL_SQUAT]:
                    max_result = Greatest("result_1", "result_2", "result_3")
                else:  # SEE_SAW_PRESS, KB_SQUAT
                    max_result = Greatest(
                        F("result_left_1") + F("result_right_1"),
                        F("result_left_2") + F("result_right_2"),
                        F("result_left_3") + F("result_right_3"),
                    )

                results = (
                    model.objects.filter(player__in=players)
                    .annotate(
                        bw_percentage=Case(
                            When(player__weight__gt=0, then=max_result * 100.0 / F("player__weight")),
                            default=0,
                            output_field=FloatField(),
                        )
                    )
                    .order_by("-bw_percentage")
                )

            for position, result in enumerate(results, start=1):
                overall_result = OverallResult.objects.get(player=result.player)
                if discipline == SNATCH:
                    overall_result.snatch_points = position
                elif discipline == TGU:
                    overall_result.tgu_points = position
                elif discipline == SEE_SAW_PRESS:
                    overall_result.see_saw_press_points = position
                elif discipline == KB_SQUAT:
                    overall_result.kb_squat_points = position
                elif discipline == PISTOL_SQUAT:
                    overall_result.pistol_squat_points = position
                overall_result.save()

    for player in players:
        overall_result = OverallResult.objects.get(player=player)
        overall_result.tiebreak_points = -0.5 if player.tiebreak else 0
        overall_result.save()

    final_results = OverallResult.objects.filter(player__in=players).order_by("total_points")
    for position, result in enumerate(final_results, start=1):
        result.final_position = position
        result.save()
