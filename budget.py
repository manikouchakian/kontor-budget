import json 
import os 


"""
Monthly Budget Manager

This program tracks monthly income and expenses,
calculates savings rate and a management score,
and compares results with the previous month.
"""


DATA_FILE = "data.json"

CATEGORIES = ["rent", "food", "investment", "health_insurance", "gas", "installments"]


def validate_month(month : str) -> str:



    if not isinstance(month, str):
        raise ValueError("Month must be string in YYYY_MM")
    
    parts = month.strip().split("-")
    if len (parts) != 2 :
        raise ValueError("Month must be in format YYYY-MM")
    
    year_str , mon_str = parts 
    if len(year_str) != 4 or not year_str.isdigit():
        raise ValueError("Year must be 4 digits. ")
    if len(mon_str) != 2 or not mon_str.isdigit():
        raise ValueError("Month must be 2 digits.")
    
    year = int(year_str)
    mon = int(mon_str)

    if year < 1900 or year > 3000 : 
        raise ValueError("year out of supported range. ")
    if mon < 1 or mon > 12 : 
        raise ValueError("Month must be between 01 and 12")
    
    return f"{year:04d}-{mon:02d}"



def validate_amount(text: str) -> float : 



    if not isinstance(text, str):
        raise ValueError("Amount must be provided as a text. ")
    
    cleaned = text.strip().replace(",", ".")
    if cleaned == "":
        raise ValueError("Amount cannot be empty")
    
    try:
        value = float(cleaned)
    except ValueError as exc :
        raise ValueError("Amount must be a number") from exc
    
    if value < 0:
        raise ValueError("Amount cannot be negative")
    
    return value 



def previous_month(month: str) -> str:   # Handle year change when month is January
    m = validate_month(month)
    year = int(m[:4])
    mon = int(m[5:7])
    if mon == 1 :
        return f"{year - 1 :04d}-12"
    return f"{year:04d}-{mon - 1 :02d}"


def load_data(filename : str =  DATA_FILE) -> dict:
    """
    Load budget data from a JSON file.
    Return an empty dict if the file does n ot exist or is invalid
    """

    if not os.path.exists(filename):
        return {}
    
    with open(filename, "r") as f : 
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}
        
    if isinstance(data, dict):
        return data
    return {}


def save_data(data: dict, filename: str = DATA_FILE) -> None:
    """
    Save budget data to a JSON file.
    """

    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def calculate_summary(income : float, expenses: dict) -> dict:
    """
    Calculate total expenses, remaining balance,
    category percentages, and savings rate.
    """
# Validate input values 
    if income < 0:
        raise ValueError("income can not be negative")
# Calculate total expenses
    total = 0.0

    for _, v in expenses.items():
        if v < 0 : 
            raise ValueError("Expenses can not be negative")
        total += float(v)
    remaining = income - total   # Remaining balance after expenses

    percentages = {}  # Calculate percentage of income for each expense category

    if income > 0:
        for k, v in expenses.items():
            percentages[k] = (float(v) / income) * 100.0
            savings_rate = remaining / income   # savings rate as a ratio of remaining income
    else:
        for k in expenses.keys():
            percentages[k] = 0.0
        savings_rate = 0.0

    return {
        "total_expenses" : total,
        "remaining" : remaining, 
        "percentages" : percentages,
        "savings_rate" : savings_rate,
    }

def clamp(value: float, lo: float, hi: float) -> float:
    if value < lo :
        return lo 
    if value > hi : 
        return hi 
    return value 

def calculate_score(income : float , remaining : float , target_rate : float = 0.30) -> int:
    """
    Calculate a management score (0-100) based on savings rate.
    a score of 100 represents meeting or exceeding the target savings rate.
    """
    if income <= 0:
        return 0
    if remaining <= 0:
        return 0 
    
    rate = remaining / income 
    score = (rate / target_rate) * 100.0  # convert savings rate to a score relative to the target rate
    score = clamp(score, 0.0, 100.0)
    return int(round(score))


def score_label(score: int) -> str:
    if score < 40:
        return "Weak"
    if score < 60:
        return "OK"
    if score < 80:
        return "Good"
    return "Excellent"


def compare_months(current: dict, previous: dict) -> dict :   
    """
    Compare current and previous month data
    and return differences in income, expenses and savings rate.
    """
    # compare values using the same calculation logic for both months 
    cur_income = float(current.get("income", 0.0))
    prev_income = float(previous.get("income", 0.0))
    cur_exp = current.get("expenses", {})
    prev_exp = previous.get("expenses", {})
    cur_sum = calculate_summary(cur_income, cur_exp)
    prev_sum = calculate_summary(prev_income, prev_exp)


    cat_diff = {}
    keys = set(cur_exp.keys()) | set(prev_exp.keys())

    for k in keys :
        cat_diff[k] = float(cur_exp.get(k, 0.0)) - float(prev_exp.get(k, 0.0))
    # Include all categories that apear in either month
    return { 
        "income_diff": cur_income - prev_income,
        "total_expenses_diff": cur_sum["total_expenses"] - prev_sum["total_expenses"],
        "remaining_diff": cur_sum["remaining"] - prev_sum["remaining"],
        "savings_rate_diff": cur_sum["savings_rate"] - prev_sum["savings_rate"],
        "category_diff" : cat_diff,
    }




def format_money(x: float) -> str:
    return f"{x:,.2f}"



def format_percent(x: float) -> str:
    return f"{x:.1f}%"


def format_report(month : str, income : float, expenses: dict, summary:dict , score: int, comparison: dict | None) -> str:
    """
    Format all data into a readable text report. 
    """
    lines = []  # Build a report line by line for clean formatting 
    lines.append(f"Month: {month}")
    lines.append(f"Income: {format_money(income)}")
    lines.append("Expenses:")

    for cat in CATEGORIES : 
        val = float(expenses.get(cat, 0.0))
        pct = float(summary["percentages"].get(cat, 0.0))
        lines.append(f" {cat}: {format_money(val)} ({format_percent(pct)})")

    
    lines.append("")
    lines.append(f"Total expenses : {format_money(summary['total_expenses'])}")
    lines.append(f"Remaining: {format_money(summary['remaining'])}")

    rate = summary.get("savings_rate", 0.0) * 100.0
    lines.append(f"Saving rate: {format_percent(rate)}") 
    lines.append(f"Management score: {score}/100 ({score_label(score)})")

    if comparison is None : 
        lines.append("No previous month data to compare. ")
    else:
        lines.append("")
        lines.append("Month-over-month comparison (current - previous):")
        lines.append(f"- Income change: {format_money(comparison['income_diff'])}")
        lines.append(f"- Total expenses change: {format_money(comparison['total_expenses_diff'])}")
        lines.append(f"- Remaining change: {format_money(comparison['remaining_diff'])}")  
        lines.append(f"- Saving rate change: {format_percent(comparison['savings_rate_diff'] * 100.0)}")



        diffs = comparison["category_diff"]
        if isinstance(diffs, dict) and diffs :
            sorted_items = sorted(diffs.items(), key=lambda kv: abs(kv[1]), reverse=True)
            for k, v in sorted_items[:2]:
                lines.append(f"- {k}: {format_money(v)}")

    return "\n".join(lines)


def prompt_month() -> str:

    while True :
        month = input("Enter month (YYYY-MM): ").strip()
        try:
            return validate_month(month)
        except ValueError as e :
            print(f"Invalid month: {e}")



def prompt_amount(label: str) -> float:
    while True:
        raw = input(f"{label}: ").strip()
        try:
            return validate_amount(raw)
        except ValueError as e:
            print(f"Invalid amount: {e}")



def main():
    """
    Run the Monthly Budget Manager program. 
    """
    print("Monthly Budget Manager")
    print("----------------------")

    month = prompt_month() # collect user input
    income = prompt_amount("Income")
    expenses = {}
    for cat in CATEGORIES: 
        pretty = cat.replace("-", " ").title()
        expenses[cat] = prompt_amount(pretty)

    summary = calculate_summary(income, expenses)
    score = calculate_score(income, summary["remaining"])


    data = load_data(DATA_FILE)

    prev_key = previous_month(month)
    comparison = None 
    if prev_key in data and isinstance(data[prev_key], dict):
        try:
            comparison = compare_months(

                {"income": income, "expenses": expenses},
                data[prev_key]

            )
        except ValueError:
            comparison = None 

    data[month] = {"income": income, "expenses": expenses}
    save_data(data, DATA_FILE) # save current month


    report = format_report(month, income, expenses, summary, score, comparison) 
    print("")
    print(report)  # generate report





if __name__ == "__main__" :
    main()
 