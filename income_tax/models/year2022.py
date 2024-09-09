import re
from pydantic import BaseModel, Field, computed_field, field_validator

from income_tax.custom_types import SSN, WholeDollar, make_whole_number
from income_tax.models.data_models import (
    StateOfResidenceEnum,
    poverty_lines,
    applicable_figures,
)
from pypdffill.mappers import FieldMapper, PdfForm  # type: ignore[import-untyped]


class MonthlyCalculationRow(BaseModel):
    a: WholeDollar = Field(
        description="Monthly premiums, Form(s) 1095-A, lines 21-32, column A"
    )
    b: WholeDollar = Field(
        description="Monthly applicable SLCSP Premium, Form(s) 1095-A, lines 21-32, column B"
    )
    c: WholeDollar = Field(description="From 8b")
    f: WholeDollar = Field(
        description="Monthly advance payment, Form(s) 1095-A, lines 21-32, column C"
    )

    @computed_field  # type: ignore[misc]
    @property
    def monthly_max_premium_assist(self) -> WholeDollar:
        """Lines 12-23(d)."""
        assistance = self.b - self.c
        return assistance if assistance > 0 else 0

    @computed_field  # type: ignore[misc]
    @property
    def monthly_allowed_tax_credit(self) -> WholeDollar:
        """Line 12-23(e)."""
        return min([self.a, self.monthly_max_premium_assist])


class MonthlyCalculationTable(BaseModel):
    january: MonthlyCalculationRow | None = None
    february: MonthlyCalculationRow | None = None
    march: MonthlyCalculationRow | None = None
    april: MonthlyCalculationRow | None = None
    may: MonthlyCalculationRow | None = None
    june: MonthlyCalculationRow | None = None
    july: MonthlyCalculationRow | None = None
    august: MonthlyCalculationRow | None = None
    september: MonthlyCalculationRow | None = None
    october: MonthlyCalculationRow | None = None
    november: MonthlyCalculationRow | None = None
    december: MonthlyCalculationRow | None = None

    @property
    def total_tax_credit(self) -> WholeDollar:
        credit_sum = WholeDollar(0)
        for field in self.model_fields:
            field_value = getattr(self, field)
            if field_value is None:
                continue
            print(type(field_value))
            credit_sum += WholeDollar(field_value.monthly_allowed_tax_credit)
        return credit_sum

    @property
    def total_advance_payment(self) -> WholeDollar:
        advance_sum = WholeDollar(0)
        for field in self.model_fields_set:
            field_value = getattr(self, field)
            advance_sum += WholeDollar(field_value.f)

        return advance_sum


class Form8962(BaseModel):
    name_on_return: str
    ssn: SSN = Field(description="Social Security Number")
    tax_family_size: int = Field(
        description="Tax family size, see instructions (Part I, Line 1)"
    )
    modified_agi: WholeDollar = Field(
        description="Modified AGI, see instructions (Part I, Line 2a)"
    )
    dependents_modified_agi: WholeDollar | None = Field(
        default=None,
        description="Total of dependents' modified AGI, see instructions (Part I, Line 2b)",
    )
    state_of_residence: StateOfResidenceEnum = Field(
        description="Use Table 1-1, 1-2, or 1-3 Headings"
    )
    another_taxpayer_or_alternative_calculation: bool = Field(
        description="Allocating with another taxpayer or alternative calculation for year of marriage (Part II, Line 9)"
    )
    line_10: bool = Field(
        description="Use line 11 or 12-23, see instructions (Part II, Line 10)"
    )
    annual_enrollment_premiums: WholeDollar | None = Field(
        default=None, description="Form(s) 1095-A, line 33A (Part II, Line 11(a))"
    )
    annual_slcsp_premium: WholeDollar | None = Field(
        default=None, description="Form(s) 1095-A, line 33B (Part II, Line 11(b))"
    )
    annual_advance_payment: WholeDollar | None = Field(
        default=None, description="Form(s) 1095-A, line 33C (Part II, Line 11(f))"
    )
    monthly_calculation: MonthlyCalculationTable | None = None

    @field_validator("ssn")
    @classmethod
    def validate_ssn_pattern(cls, value: SSN) -> SSN:
        if re.match(r"^\d{3}-\d{2}-\d{4}$|^\d{9}$", value.get_secret_value()) is None:
            msg = "Entered value of SSN is not valid."
            raise ValueError(msg)
        return value

    @computed_field  # type: ignore[misc]
    @property
    def household_income(self) -> WholeDollar:
        income = self.modified_agi
        return (
            income
            if self.dependents_modified_agi is None
            else income + self.dependents_modified_agi
        )

    @computed_field  # type: ignore[misc]
    @property
    def poverty_line(self) -> WholeDollar:
        return poverty_lines.get_poverty_rate(
            self.state_of_residence, self.tax_family_size
        )

    @computed_field  # type: ignore[misc]
    @property
    def percent_of_poverty_line(self) -> int:
        percentage = self.household_income / self.poverty_line
        return make_whole_number(percentage * 100) if percentage <= 4.0 else 401

    @computed_field  # type: ignore[misc]
    @property
    def applicable_figure(self) -> float:
        return applicable_figures.get_figure(self.percent_of_poverty_line)

    @computed_field  # type: ignore[misc]
    @property
    def annual_contribution(self) -> int:
        """Line 8a.

        Multiplication of Household Income (Line 3) by Applicable Figure (Line 7)
        """
        return int(round(self.household_income * self.applicable_figure, 0))

    @computed_field  # type: ignore[misc]
    @property
    def monthly_contribution(self) -> int:
        """Line 8b.

        Annual contribution divided by 12 (months)
        """
        return int(round(self.annual_contribution / 12, 0))

    @computed_field  # type: ignore[misc]
    @property
    def line_11_c(self) -> WholeDollar | None:
        return self.annual_contribution if self.line_10 else None

    @computed_field  # type: ignore[misc]
    @property
    def annual_max_premium_assist(self) -> WholeDollar | None:
        """Line 11(d)."""
        if self.line_10:
            assert self.line_11_c is not None
            assert self.annual_slcsp_premium is not None
            assistance = self.line_11_c - self.annual_slcsp_premium
            return assistance if assistance > 0 else 0
        return None

    @computed_field  # type: ignore[misc]
    @property
    def annual_allowed_tax_credit(self) -> WholeDollar | None:
        """Line 11(e)."""
        if self.line_10:
            assert self.annual_enrollment_premiums is not None
            assert self.annual_max_premium_assist is not None
            return min(
                [self.annual_enrollment_premiums, self.annual_max_premium_assist]
            )
        return None

    @computed_field  # type: ignore[misc]
    @property
    def total_tax_credit(self) -> WholeDollar:
        """Part II, Line 24"""
        annual_allowed_tax_credit = self.annual_allowed_tax_credit
        if annual_allowed_tax_credit is None:
            assert self.monthly_calculation is not None
            return self.monthly_calculation.total_tax_credit
        return annual_allowed_tax_credit

    @computed_field  # type: ignore[misc]
    @property
    def total_advance_payment(self) -> WholeDollar:
        """Part II, Line 25"""
        total_advance_payment = self.annual_advance_payment
        if total_advance_payment is None:
            assert self.monthly_calculation is not None
            return self.monthly_calculation.total_advance_payment
        return total_advance_payment

    @computed_field  # type: ignore[misc]
    @property
    def net_tax_credit(self) -> WholeDollar | None:
        if (total_tax_credit := self.total_tax_credit) > (
            total_advance_payment := self.total_advance_payment
        ):
            return WholeDollar(total_tax_credit - total_advance_payment)
        if total_tax_credit == total_advance_payment:
            return 0
        return None


Form8962PDF = PdfForm(
    name="Form8962",
    fields=[FieldMapper(field_name="name", widget_type="text", widget_name="f1_1[0]")],
    blank_pdf_path="income_tax/forms/f8962.pdf",
)


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table

    my_form = Form8962(
        name_on_return="Karl Wooster",
        ssn=SSN(secret_value="123-45-6789"),
        tax_family_size=4,
        modified_agi=77194,
        state_of_residence=StateOfResidenceEnum.CONTIGUOUS_48_AND_DC,
        another_taxpayer_or_alternative_calculation=False,
        line_10=False,
    )

    _january = MonthlyCalculationRow(
        a=700, b=500, c=my_form.monthly_contribution, f=100
    )
    _february = _january.model_copy()
    _march = _january.model_copy()
    _april = _january.model_copy()

    _my_table = MonthlyCalculationTable(
        january=_january, february=_february, march=_march, april=_april
    )

    my_form.monthly_calculation = _my_table

    table = Table(title="Calculated Values")

    table.add_column("Line #", justify="left", no_wrap=True)
    table.add_column("Label", justify="right")
    table.add_column("Value", justify="right")

    table.add_row("3", "Household Income", f"${my_form.household_income}")
    table.add_row("4", "Federal Poverty Line", f"${my_form.poverty_line}")
    table.add_row("5", "Percent of Poverty Line", f"{my_form.percent_of_poverty_line}%")
    table.add_row("7", "Applicable Figure", f"{my_form.applicable_figure:.4f}")
    table.add_row("8a", "Annual Contribution", f"${my_form.annual_contribution}")
    table.add_row("8b", "Monthly Contribution", f"${my_form.monthly_contribution}")

    console = Console()
    console.print(
        f"Form 8962 for [bold magenta]{my_form.name_on_return}[/bold magenta]"
    )

    console.print(table)

    if my_form.monthly_calculation is not None:
        monthly_calcs = Table(title="Monthly Calculation")
        monthly_calcs.add_column("Line #", justify="center")
        monthly_calcs.add_column("a", justify="right")
        monthly_calcs.add_column("b", justify="right")
        monthly_calcs.add_column("c", justify="right")
        monthly_calcs.add_column("d", justify="right")
        monthly_calcs.add_column("e", justify="right")
        monthly_calcs.add_column("f", justify="right")

        calcs = my_form.monthly_calculation

        for row in calcs.model_fields_set:
            calc_row = getattr(my_form.monthly_calculation, row)
            monthly_calcs.add_row(
                f"{row.title()}",
                f"{calc_row.a:.0f}",
                f"{calc_row.b:.0f}",
                f"{calc_row.c:.0f}",
                f"{calc_row.monthly_max_premium_assist:.0f}",
                f"{calc_row.monthly_allowed_tax_credit:.0f}",
                f"{calc_row.f:.0f}",
            )

        monthly_calcs.add_row(
            "24", "", "", "", "", "", f"{my_form.total_tax_credit:.0f}"
        )
        monthly_calcs.add_row(
            "25", "", "", "", "", "", f"{my_form.total_advance_payment:.0f}"
        )
        monthly_calcs.add_row(
            "26",
            "",
            "",
            "",
            "",
            "",
            f"{my_form.net_tax_credit or '-'}",
        )

        console.print(monthly_calcs)
