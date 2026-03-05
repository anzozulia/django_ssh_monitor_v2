from django import forms

from apps.alerts.models import AlertRule, Condition, MetricType


class AlertRuleForm(forms.ModelForm):
    BYTE_METRICS = {
        MetricType.RAM_USED,
        MetricType.RAM_FREE,
        MetricType.RAM_AVAILABLE,
        MetricType.RAM_CACHED,
        MetricType.SWAP_USED,
        MetricType.SWAP_FREE,
        MetricType.DISK_USED,
        MetricType.DISK_FREE,
    }
    UPTIME_METRICS = {MetricType.UPTIME}
    UNIT_CHOICES = [
        ("B", "Bytes"),
        ("KB", "KB"),
        ("MB", "MB"),
        ("GB", "GB"),
        ("TB", "TB"),
        ("h", "Hours"),
        ("d", "Days"),
        ("w", "Weeks"),
        ("mo", "Months"),
    ]
    UNIT_FACTORS = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }
    UPTIME_FACTORS = {
        "h": 3600,
        "d": 86400,
        "w": 7 * 86400,
        "mo": 30 * 86400,
    }

    threshold_unit = forms.ChoiceField(choices=UNIT_CHOICES, required=False, initial="GB")
    REMINDER_UNIT_CHOICES = [("minutes", "Minutes"), ("hours", "Hours")]
    reminder_interval_unit = forms.ChoiceField(
        choices=REMINDER_UNIT_CHOICES,
        required=False,
        initial="minutes",
    )
    use_dismissal_threshold = forms.BooleanField(required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        metric_choices: list[tuple[str, list[tuple[str, str]]]] = [
            (
                "CPU / Load",
                [
                    (MetricType.CPU_LOAD_1, "CPU Load (1 min)"),
                    (MetricType.CPU_LOAD_5, "CPU Load (5 min)"),
                    (MetricType.CPU_LOAD_15, "CPU Load (15 min)"),
                ],
            ),
            (
                "Memory (RAM) - Percent",
                [
                    (MetricType.RAM_PERCENT, "RAM Usage %"),
                    (MetricType.RAM_AVAILABLE_PCT, "RAM Available %"),
                    (MetricType.RAM_FREE_PCT, "RAM Free %"),
                ],
            ),
            (
                "Memory (RAM) - Bytes",
                [
                    (MetricType.RAM_USED, "RAM Used (bytes)"),
                    (MetricType.RAM_AVAILABLE, "RAM Available (bytes)"),
                    (MetricType.RAM_FREE, "RAM Free (bytes)"),
                    (MetricType.RAM_CACHED, "RAM Cached (bytes)"),
                ],
            ),
            (
                "Swap",
                [
                    (MetricType.SWAP_PERCENT, "Swap Usage %"),
                    (MetricType.SWAP_FREE_PCT, "Swap Free %"),
                    (MetricType.SWAP_USED, "Swap Used (bytes)"),
                    (MetricType.SWAP_FREE, "Swap Free (bytes)"),
                ],
            ),
            (
                "Disk",
                [
                    (MetricType.DISK_PERCENT, "Disk Usage %"),
                    (MetricType.DISK_FREE_PCT, "Disk Free %"),
                    (MetricType.DISK_USED, "Disk Used (bytes)"),
                    (MetricType.DISK_FREE, "Disk Free (bytes)"),
                ],
            ),
            (
                "System / Connectivity",
                [
                    (MetricType.UPTIME, "Uptime"),
                ],
            ),
        ]
        # Keep system-only metric editable if such a rule is opened directly.
        if self.instance.pk and self.instance.metric_type == MetricType.CUSTOM:
            metric_choices[-1][1].append((MetricType.CUSTOM, "System (internal)"))

        self.fields["metric_type"].choices = [group for group in metric_choices if group[1]]
        self.fields["reminder_interval_minutes"].required = False
        self.fields["reminder_interval_minutes"].min_value = 0

        metric_type = self.initial.get("metric_type") or self.data.get("metric_type") or self.instance.metric_type
        if not self.is_bound:
            self.initial["use_dismissal_threshold"] = bool(
                self.instance.pk
                and (
                    self.instance.dismissal_threshold_value is not None
                    or self.instance.dismissal_threshold_value_2 is not None
                )
            )
        if not self.is_bound and self.instance.pk:
            if self.instance.reminder_interval_minutes and self.instance.reminder_interval_minutes % 60 == 0:
                self.initial["reminder_interval_unit"] = "hours"
                self.initial["reminder_interval_minutes"] = self.instance.reminder_interval_minutes // 60
            else:
                self.initial["reminder_interval_unit"] = "minutes"
            if metric_type in self.BYTE_METRICS:
                unit = self._best_byte_unit_for_value(self.instance.threshold_value)
                factor = self.UNIT_FACTORS[unit]
                self.initial["threshold_unit"] = unit
                if self.instance.threshold_value is not None:
                    self.initial["threshold_value"] = self.instance.threshold_value / factor
                if self.instance.threshold_value_2 is not None:
                    self.initial["threshold_value_2"] = self.instance.threshold_value_2 / factor
                if self.instance.dismissal_threshold_value is not None:
                    self.initial["dismissal_threshold_value"] = self.instance.dismissal_threshold_value / factor
                if self.instance.dismissal_threshold_value_2 is not None:
                    self.initial["dismissal_threshold_value_2"] = self.instance.dismissal_threshold_value_2 / factor
            elif metric_type in self.UPTIME_METRICS:
                unit = self._best_uptime_unit_for_value(self.instance.threshold_value)
                factor = self.UPTIME_FACTORS[unit]
                self.initial["threshold_unit"] = unit
                if self.instance.threshold_value is not None:
                    self.initial["threshold_value"] = self.instance.threshold_value / factor
                if self.instance.threshold_value_2 is not None:
                    self.initial["threshold_value_2"] = self.instance.threshold_value_2 / factor
                if self.instance.dismissal_threshold_value is not None:
                    self.initial["dismissal_threshold_value"] = self.instance.dismissal_threshold_value / factor
                if self.instance.dismissal_threshold_value_2 is not None:
                    self.initial["dismissal_threshold_value_2"] = self.instance.dismissal_threshold_value_2 / factor
        elif not self.is_bound and metric_type in self.UPTIME_METRICS:
            self.initial["threshold_unit"] = "d"

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = (
                    "h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 py-2.5 "
                    "text-theme-sm text-gray-900 focus:border-brand-300 focus:ring-3 "
                    "focus:ring-brand-500/10 focus:outline-hidden"
                )
            elif field.widget.input_type == "checkbox":
                field.widget.attrs["class"] = "peer sr-only"
                if field_name == "use_dismissal_threshold":
                    field.widget.attrs["x-model"] = "useDismissalThreshold"

    class Meta:
        model = AlertRule
        fields = [
            "name",
            "severity",
            "metric_type",
            "metric_param",
            "condition",
            "threshold_value",
            "threshold_value_2",
            "dismissal_threshold_value",
            "dismissal_threshold_value_2",
            "threshold_unit",
            "reminder_interval_minutes",
            "notify_on_dismissal",
        ]

    def clean(self):
        cleaned = super().clean()
        metric_type = cleaned.get("metric_type")
        unit = cleaned.get("threshold_unit") or "B"
        condition = cleaned.get("condition")
        v1 = cleaned.get("threshold_value")
        v2 = cleaned.get("threshold_value_2")
        d1 = cleaned.get("dismissal_threshold_value")
        d2 = cleaned.get("dismissal_threshold_value_2")
        use_dismissal_threshold = cleaned.get("use_dismissal_threshold")
        reminder_interval = cleaned.get("reminder_interval_minutes")
        reminder_unit = cleaned.get("reminder_interval_unit") or "minutes"
        if reminder_interval in (None, ""):
            cleaned["reminder_interval_minutes"] = 0
            self.instance.reminder_interval_minutes = 0
        else:
            reminder_minutes = reminder_interval * 60 if reminder_unit == "hours" else reminder_interval
            cleaned["reminder_interval_minutes"] = reminder_minutes
            self.instance.reminder_interval_minutes = reminder_minutes

        if metric_type in self.BYTE_METRICS:
            factor = self.UNIT_FACTORS.get(unit, 1)
            if v1 is not None:
                cleaned["threshold_value"] = v1 * factor
                self.instance.threshold_value = cleaned["threshold_value"]
            if v2 is not None:
                cleaned["threshold_value_2"] = v2 * factor
                self.instance.threshold_value_2 = cleaned["threshold_value_2"]
            if d1 is not None:
                cleaned["dismissal_threshold_value"] = d1 * factor
                self.instance.dismissal_threshold_value = cleaned["dismissal_threshold_value"]
            if d2 is not None:
                cleaned["dismissal_threshold_value_2"] = d2 * factor
                self.instance.dismissal_threshold_value_2 = cleaned["dismissal_threshold_value_2"]
            v1 = cleaned.get("threshold_value")
            v2 = cleaned.get("threshold_value_2")
            d1 = cleaned.get("dismissal_threshold_value")
            d2 = cleaned.get("dismissal_threshold_value_2")
        elif metric_type in self.UPTIME_METRICS:
            factor = self.UPTIME_FACTORS.get(unit, 1)
            if v1 is not None:
                cleaned["threshold_value"] = v1 * factor
                self.instance.threshold_value = cleaned["threshold_value"]
            if v2 is not None:
                cleaned["threshold_value_2"] = v2 * factor
                self.instance.threshold_value_2 = cleaned["threshold_value_2"]
            if d1 is not None:
                cleaned["dismissal_threshold_value"] = d1 * factor
                self.instance.dismissal_threshold_value = cleaned["dismissal_threshold_value"]
            if d2 is not None:
                cleaned["dismissal_threshold_value_2"] = d2 * factor
                self.instance.dismissal_threshold_value_2 = cleaned["dismissal_threshold_value_2"]
            v1 = cleaned.get("threshold_value")
            v2 = cleaned.get("threshold_value_2")
            d1 = cleaned.get("dismissal_threshold_value")
            d2 = cleaned.get("dismissal_threshold_value_2")

        if condition in {"in_range", "out_of_range"} and v2 is None:
            self.add_error("threshold_value_2", "Second threshold is required for range conditions.")
        if condition in {"in_range", "out_of_range"} and v1 is not None and v2 is not None and v1 > v2:
            self.add_error("threshold_value_2", "Second threshold must be greater than or equal to first.")

        if metric_type == MetricType.CUSTOM:
            cleaned["dismissal_threshold_value"] = None
            cleaned["dismissal_threshold_value_2"] = None
            self.instance.dismissal_threshold_value = None
            self.instance.dismissal_threshold_value_2 = None
            return cleaned

        if not use_dismissal_threshold:
            cleaned["dismissal_threshold_value"] = None
            cleaned["dismissal_threshold_value_2"] = None
            self.instance.dismissal_threshold_value = None
            self.instance.dismissal_threshold_value_2 = None
            return cleaned

        if condition in {Condition.IN_RANGE, Condition.OUT_OF_RANGE}:
            if d1 is None:
                self.add_error(
                    "dismissal_threshold_value",
                    "Dismissal lower bound is required for range conditions.",
                )
            if d2 is None:
                self.add_error(
                    "dismissal_threshold_value_2",
                    "Dismissal upper bound is required for range conditions.",
                )
            if d1 is not None and d2 is not None and d1 > d2:
                self.add_error(
                    "dismissal_threshold_value_2",
                    "Dismissal upper bound must be greater than or equal to dismissal lower bound.",
                )
            if (
                condition == Condition.IN_RANGE
                and v1 is not None
                and v2 is not None
                and d1 is not None
                and d2 is not None
            ):
                if d1 > v1:
                    self.add_error(
                        "dismissal_threshold_value",
                        "For 'Within range', dismissal lower bound must be less than or equal to From.",
                    )
                if d2 < v2:
                    self.add_error(
                        "dismissal_threshold_value_2",
                        "For 'Within range', dismissal upper bound must be greater than or equal to To.",
                    )
            if (
                condition == Condition.OUT_OF_RANGE
                and v1 is not None
                and v2 is not None
                and d1 is not None
                and d2 is not None
            ):
                if d1 < v1:
                    self.add_error(
                        "dismissal_threshold_value",
                        "For 'Outside range', dismissal lower bound must be greater than or equal to From.",
                    )
                if d2 > v2:
                    self.add_error(
                        "dismissal_threshold_value_2",
                        "For 'Outside range', dismissal upper bound must be less than or equal to To.",
                    )
        else:
            cleaned["dismissal_threshold_value_2"] = None
            self.instance.dismissal_threshold_value_2 = None
            if d1 is None:
                self.add_error("dismissal_threshold_value", "Dismissal threshold is required.")
            elif v1 is not None:
                if condition in {Condition.GT, Condition.GTE} and d1 >= v1:
                    self.add_error(
                        "dismissal_threshold_value",
                        "Dismissal threshold must be lower than trigger threshold for 'greater than' conditions.",
                    )
                elif condition in {Condition.LT, Condition.LTE} and d1 <= v1:
                    self.add_error(
                        "dismissal_threshold_value",
                        "Dismissal threshold must be greater than trigger threshold for 'less than' conditions.",
                    )
                elif condition == Condition.EQ and d1 <= 0:
                    self.add_error(
                        "dismissal_threshold_value",
                        "For equals condition, dismissal threshold must be a positive tolerance value.",
                    )
        return cleaned

    @classmethod
    def _best_byte_unit_for_value(cls, value: float | None) -> str:
        if value is None:
            return "GB"
        abs_value = abs(value)
        if abs_value >= cls.UNIT_FACTORS["TB"]:
            return "TB"
        if abs_value >= cls.UNIT_FACTORS["GB"]:
            return "GB"
        if abs_value >= cls.UNIT_FACTORS["MB"]:
            return "MB"
        if abs_value >= cls.UNIT_FACTORS["KB"]:
            return "KB"
        return "B"

    @classmethod
    def _best_uptime_unit_for_value(cls, value: float | None) -> str:
        if value is None:
            return "d"
        abs_value = abs(value)
        if abs_value >= cls.UPTIME_FACTORS["mo"]:
            return "mo"
        if abs_value >= cls.UPTIME_FACTORS["w"]:
            return "w"
        if abs_value >= cls.UPTIME_FACTORS["d"]:
            return "d"
        return "h"


class DefaultAlertTemplateForm(AlertRuleForm):
    """Alias form to keep default-template views explicit while reusing AlertRule form."""
