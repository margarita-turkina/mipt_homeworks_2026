#!/usr/bin/env python

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

KEY_TYPE = "type"
KEY_AMOUNT = "amount"
KEY_DATE = "date"
KEY_CATEGORY = "category"
TYPE_INCOME = "income"
TYPE_COST = "cost"

DateTuple = tuple[int, int, int]
TxValue = float | str | DateTuple
Transaction = dict[str, TxValue]
CategorySums = dict[str, float]
StatsTotals = tuple[float, float, float, CategorySums]

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

financial_transactions_storage: list[Transaction] = []


def _is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def _get_days_in_month(year: int) -> list[int]:
    """Return days in each month for given year."""
    feb_days = 29 if _is_leap_year(year) else 28
    return [31, feb_days, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _is_valid_amount(raw_amount: str) -> bool:
    normalized = raw_amount.replace(",", ".")
    return normalized.replace(".", "", 1).isdigit()


def _get_valid_categories() -> list[str]:
    valid_cats = []
    for m_cat, sub_list in EXPENSE_CATEGORIES.items():
        valid_cats.extend([f"{m_cat}::{s_cat}" for s_cat in sub_list])
    return valid_cats


def _store_failed() -> None:
    failed: Transaction = {}
    financial_transactions_storage.append(failed)


def _parse_transaction_date(item: Transaction) -> DateTuple | None:
    if not item:
        return None
    date_val = item[KEY_DATE]
    if isinstance(date_val, tuple):
        return date_val
    if isinstance(date_val, str):
        return extract_date(date_val)
    return None


def _is_on_or_before(item_date: DateTuple, target_date: DateTuple) -> bool:
    day, month, year = item_date
    target_day, target_month, target_year = target_date
    if year != target_year:
        return year < target_year
    if month != target_month:
        return month < target_month
    return day <= target_day


def extract_date(maybe_dt: str) -> DateTuple | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None
    if not all(p.isdigit() for p in parts):
        return None

    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])
    if month < 1 or month > MAX_MONTH or year < 0:
        return None

    days_in_month = _get_days_in_month(year)
    if 1 <= day <= days_in_month[month - 1]:
        return (day, month, year)
    return None


def income_handler(amount: float, income_date: str) -> str:
    date_tuple = extract_date(income_date)
    if date_tuple is None:
        _store_failed()
        return INCORRECT_DATE_MSG
    if amount <= 0:
        _store_failed()
        return NONPOSITIVE_VALUE_MSG
    financial_transactions_storage.append({KEY_TYPE: TYPE_INCOME, KEY_AMOUNT: amount, KEY_DATE: date_tuple})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    date_tuple = extract_date(income_date)
    if date_tuple is None:
        _store_failed()
        return INCORRECT_DATE_MSG
    if amount <= 0:
        _store_failed()
        return NONPOSITIVE_VALUE_MSG
    if category_name not in _get_valid_categories():
        _store_failed()
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append(
        {
            KEY_TYPE: TYPE_COST,
            KEY_CATEGORY: category_name,
            KEY_AMOUNT: amount,
            KEY_DATE: date_tuple,
        }
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines = []
    for main_cat, sub_cats in EXPENSE_CATEGORIES.items():
        lines.extend([f"{main_cat}::{sub_cat}" for sub_cat in sub_cats])
    return "\n".join(lines)


def _calculate_capital_and_monthly(item: Transaction, target_d: int, target_m: int, target_y: int) -> StatsTotals:
    total_capital: float = 0
    month_income: float = 0
    month_expense: float = 0
    category_sums: CategorySums = {}

    parsed_date = _parse_transaction_date(item)
    if parsed_date is None:
        return total_capital, month_income, month_expense, category_sums

    amount = item.get(KEY_AMOUNT)
    if not isinstance(amount, (int, float)):
        return total_capital, month_income, month_expense, category_sums

    target_date = (target_d, target_m, target_y)
    if _is_on_or_before(parsed_date, target_date):
        if item[KEY_TYPE] == TYPE_INCOME:
            total_capital += amount
        else:
            total_capital -= amount

    _, item_m, item_y = parsed_date
    if item_m == target_m and item_y == target_y:
        if item[KEY_TYPE] == TYPE_INCOME:
            month_income += amount
        else:
            month_expense += amount
            category = item.get(KEY_CATEGORY, "")
            if isinstance(category, str):
                display_name = category.split("::")[-1]
                category_sums[display_name] = category_sums.get(display_name, 0) + amount

    return total_capital, month_income, month_expense, category_sums


def _format_value(val: float) -> str:
    """Format value: use integer notation for whole numbers, otherwise use float with comma."""
    if val.is_integer():
        return str(int(val))
    text = format(val, "g")
    return text.replace(".", ",")


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


def _aggregate_stats(target_d: int, target_m: int, target_y: int) -> StatsTotals:
    total_capital: float = 0
    month_income: float = 0
    month_expense: float = 0
    category_sums: CategorySums = {}

    for item in financial_transactions_storage:
        capital, inc, exp, cats = _calculate_capital_and_monthly(item, target_d, target_m, target_y)
        total_capital += capital
        month_income += inc
        month_expense += exp
        for cat_name, cat_sum in cats.items():
            category_sums[cat_name] = category_sums.get(cat_name, 0) + cat_sum

    return total_capital, month_income, month_expense, category_sums


def stats_handler(report_date: str) -> str:
    extracted = extract_date(report_date)
    if extracted is None:
        return INCORRECT_DATE_MSG
    totals = _aggregate_stats(*extracted)
    return _format_stats_output(report_date, *totals)


def process_income_command(parts: list[str]) -> None:
    if len(parts) != INCOME_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    if not _is_valid_amount(parts[1]):
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = float(parts[1].replace(",", "."))
    if amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return
    if not extract_date(parts[2]):
        print(INCORRECT_DATE_MSG)
        return
    print(income_handler(amount, parts[2]))


def _cost_command_error(parts: list[str]) -> tuple[str | None, bool]:
    if len(parts) != COST_ARGS_COUNT or not _is_valid_amount(parts[2]):
        return UNKNOWN_COMMAND_MSG, False
    cat = parts[1]
    amount = float(parts[2].replace(",", "."))
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG, False
    if cat not in _get_valid_categories():
        return NOT_EXISTS_CATEGORY, True
    if not extract_date(parts[3]):
        return INCORRECT_DATE_MSG, False
    print(cost_handler(cat, amount, parts[3]))
    return None, False


def process_cost_command(parts: list[str]) -> None:
    if len(parts) == COST_CATEGORIES_ARGS and parts[1] == "categories":
        print(cost_categories_handler())
        return
    message, show_categories = _cost_command_error(parts)
    if message is None:
        return
    print(message)
    if show_categories:
        print(cost_categories_handler())


def process_stats_command(parts: list[str]) -> None:
    if len(parts) != STATS_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    if not extract_date(parts[1]):
        print(INCORRECT_DATE_MSG)
        return
    print(stats_handler(parts[1]))


def _run_command(parts: list[str]) -> None:
    cmd = parts[0]
    if cmd == "income":
        process_income_command(parts)
    elif cmd == "cost":
        process_cost_command(parts)
    elif cmd == "stats":
        process_stats_command(parts)
    else:
        print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    running = True
    while running:
        line = input().strip()
        if not line:
            continue
        _run_command(line.split())


if __name__ == "__main__":
    main()
