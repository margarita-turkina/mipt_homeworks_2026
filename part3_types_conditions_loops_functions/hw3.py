#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS_COUNT = 3
MAX_MONTH = 12
INCOME_ARGS_COUNT = 3
COST_CATEGORIES_ARGS = 2
COST_ARGS_COUNT = 4
STATS_ARGS_COUNT = 2

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

financial_transactions_storage: list[dict[str, Any]] = []


def _is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _get_days_in_month(year: int) -> list[int]:
    """Return days in each month for given year."""
    feb_days = 29 if _is_leap_year(year) else 28
    return [31, feb_days, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None
    if not all(p.isdigit() for p in parts):
        return None

    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
    if m < 1 or m > MAX_MONTH or y < 0:
        return None

    days_in_month = _get_days_in_month(y)
    if 1 <= d <= days_in_month[m - 1]:
        return (d, m, y)
    return None


def income_handler(amount: float, income_date: str) -> str:
    date_tuple = extract_date(income_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    financial_transactions_storage.append(
        {"type": "income", "amount": amount, "date": date_tuple}
    )
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    date_tuple = extract_date(income_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    valid_cats = []
    for m_cat, sub_list in EXPENSE_CATEGORIES.items():
        valid_cats.extend([f"{m_cat}::{s_cat}" for s_cat in sub_list])
    if category_name not in valid_cats:
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append(
        {"type": "cost", "category": category_name, "amount": amount, "date": date_tuple}
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines = []
    for main_cat, sub_cats in EXPENSE_CATEGORIES.items():
        lines.extend([f"{main_cat}::{sub_cat}" for sub_cat in sub_cats])
    return "\n".join(lines)


def _calculate_capital_and_monthly(
    item: dict[str, Any], target_d: int, target_m: int, target_y: int
) -> tuple[float, float, float, dict[str, float]]:
    total_capital = 0
    month_income = 0
    month_expense = 0
    category_sums: dict[str, float] = {}

    extracted = extract_date(item["date"])
    if extracted is None:
        return total_capital, month_income, month_expense, category_sums
    item_d, item_m, item_y = extracted

    # Check if item date is before or on report date
    is_before_report = (
        item_y < target_y or
        (item_y == target_y and item_m < target_m) or
        (item_y == target_y and item_m == target_m and item_d <= target_d)
    )
    if is_before_report:
        if item["type"] == "income":
            total_capital += item["amount"]
        else:
            total_capital -= item["amount"]

    # Check if item is in target month
    if item_m == target_m and item_y == target_y:
        if item["type"] == "income":
            month_income += item["amount"]
        else:
            month_expense += item["amount"]
            display_name = item["category"].split("::")[-1]
            category_sums[display_name] = category_sums.get(display_name, 0) + item["amount"]

    return total_capital, month_income, month_expense, category_sums


def _format_value(val: float) -> str:
    """Format value: use integer notation for whole numbers, otherwise use float with comma."""
    if val.is_integer():
        return str(int(val))
    return f"{val:g}".replace(".", ",")


def _format_stats_output(
    report_date: str, total_capital: float, month_income: float, month_expense: float, category_sums: dict[str, float]
) -> str:
    res = [f"Your statistics as of {report_date}:", f"Total capital: {total_capital:.2f} rubles"]
    diff = month_income - month_expense
    if diff >= 0:
        res.append(f"This month, the profit amounted to {diff:.2f} rubles.")
    else:
        res.append(f"This month, the loss amounted to {abs(diff):.2f} rubles.")

    res.append(f"Income: {month_income:.2f} rubles")
    res.append(f"Expenses: {month_expense:.2f} rubles")
    res.append("\nDetails (category: amount):")

    if category_sums:
        sorted_cats = sorted(category_sums.keys())
        for i, cat in enumerate(sorted_cats, 1):
            val = category_sums[cat]
            res.append(f"{i}. {cat}: {_format_value(val)}")

    return "\n".join(res)


def stats_handler(report_date: str) -> str:
    extracted = extract_date(report_date)
    if extracted is None:
        return INCORRECT_DATE_MSG
    target_d, target_m, target_y = extracted

    total_capital = 0
    month_income = 0
    month_expense = 0
    category_sums: dict[str, float] = {}

    for item in financial_transactions_storage:
        capital, inc, exp, cats = _calculate_capital_and_monthly(item, target_d, target_m, target_y)
        total_capital += capital
        month_income += inc
        month_expense += exp
        for cat_name, cat_sum in cats.items():
            category_sums[cat_name] = category_sums.get(cat_name, 0) + cat_sum

    return _format_stats_output(report_date, total_capital, month_income, month_expense, category_sums)


def process_income_command(parts: list[str]) -> None:
    if len(parts) != INCOME_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    raw_amount = parts[1].replace(",", ".")
    if not raw_amount.replace(".", "", 1).isdigit():
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = float(raw_amount)
    if amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return
    if not extract_date(parts[2]):
        print(INCORRECT_DATE_MSG)
        return
    print(income_handler(amount, parts[2]))


def process_cost_command(parts: list[str]) -> None:
    if len(parts) == COST_CATEGORIES_ARGS and parts[1] == "categories":
        print(cost_categories_handler())
        return
    if len(parts) != COST_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    cat = parts[1]
    raw_amount = parts[2].replace(",", ".")
    if not raw_amount.replace(".", "", 1).isdigit():
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = float(raw_amount)
    if amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return
    valid_cats = []
    for m_cat, sub_list in EXPENSE_CATEGORIES.items():
        valid_cats.extend([f"{m_cat}::{s_cat}" for s_cat in sub_list])
    if cat not in valid_cats:
        print(NOT_EXISTS_CATEGORY)
        print(cost_categories_handler())
        return
    if not extract_date(parts[3]):
        print(INCORRECT_DATE_MSG)
        return
    print(cost_handler(cat, amount, parts[3]))


def process_stats_command(parts: list[str]) -> None:
    if len(parts) != STATS_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    if not extract_date(parts[1]):
        print(INCORRECT_DATE_MSG)
        return
    print(stats_handler(parts[1]))


def main() -> None:
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        if not line:
            continue

        parts = line.split()
        cmd = parts[0]

        if cmd == "income":
            process_income_command(parts)
        elif cmd == "cost":
            process_cost_command(parts)
        elif cmd == "stats":
            process_stats_command(parts)
        else:
            print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()