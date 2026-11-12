import json
import math
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from tkcalendar import DateEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FILE_NAME = "expenses.json"
DATE_FORMAT = "%d-%m-%Y"
MAX_NAME_LENGTH = 100
MAX_AMOUNT = 1_000_000_000
PLACEHOLDER_CATEGORY = "-- Select Category --"
PLACEHOLDER_MONTH = "Choose Month"

CATEGORIES = [
    PLACEHOLDER_CATEGORY,
    "Daily Products",
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "Other",
]

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

BG_COLOR = "#F1F5F9"
CARD_BG = "white"
LABEL_FG = "#333333"
ENTRY_BG = "#F8FAFC"
ENTRY_BORDER = "#CBD5E1"
ENTRY_FOCUS = "#2563EB"
PRIMARY = "#2563EB"
PRIMARY_ACTIVE = "#1D4ED8"

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
expenses = []
total_expense = 0.0
visible_expense_indices = []


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def save_expenses():
    try:
        with open(FILE_NAME, "w") as file:
            json.dump(expenses, file)
    except OSError as error:
        messagebox.showerror("Save Error", f"Expenses could not be saved.\n{error}")


def _parse_expense(item):
    """Return a validated (category, date, name, amount) tuple, or None."""
    if not isinstance(item, (list, tuple)) or len(item) != 4:
        return None
    category, date, name, amount = item
    try:
        datetime.strptime(date, DATE_FORMAT)
        amount = float(amount)
    except (ValueError, TypeError):
        return None
    if amount <= 0:
        return None
    return category, date, name, amount


def load_expenses():
    global total_expense
    try:
        with open(FILE_NAME, "r") as file:
            saved = json.load(file)
        if not isinstance(saved, list):
            raise ValueError("Expense data must be a list.")
    except FileNotFoundError:
        return
    except (json.JSONDecodeError, ValueError, TypeError):
        messagebox.showwarning(
            "Data Warning",
            "Expense file is damaged or has an invalid format.",
        )
        return

    for item in saved:
        parsed = _parse_expense(item)
        if parsed:
            expenses.append(parsed)
            total_expense += parsed[3]


# ---------------------------------------------------------------------------
# UI actions
# ---------------------------------------------------------------------------
def show_expenses(event=None):
    global visible_expense_indices
    expense_list.delete(0, tk.END)
    visible_expense_indices = []

    selected_month = month_dropdown.get()
    if selected_month == PLACEHOLDER_MONTH:
        total_label.config(text="Please choose a month")
        return

    month_total = 0.0
    for index, (category, date, name, amount) in enumerate(expenses):
        expense_month = datetime.strptime(date, DATE_FORMAT).strftime("%B %Y")
        if expense_month != selected_month:
            continue
        visible_expense_indices.append(index)
        expense_list.insert(tk.END, f"{category} | {name} | ₹{amount:.2f} | {date}")
        month_total += amount

    total_label.config(text=f"Total Expense ({selected_month}): ₹{month_total:,.2f}")


def add_expense():
    global total_expense

    name = expense_name.get().strip()
    if len(name) > MAX_NAME_LENGTH:
        messagebox.showwarning(
            "Name Too Long",
            f"Expense name must be {MAX_NAME_LENGTH} characters or less.",
        )
        return

    category = category_var.get()
    if category == PLACEHOLDER_CATEGORY:
        messagebox.showwarning("Warning", "Please select a category.")
        return

    amount_text = expense_amount.get().strip()
    if not name or not amount_text:
        messagebox.showwarning("Warning", "Please enter expense name and amount.")
        return

    try:
        amount = float(amount_text)
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid amount.")
        return

    if not math.isfinite(amount) or amount <= 0 or amount > MAX_AMOUNT:
        messagebox.showwarning(
            "Invalid Amount",
            f"Please enter an amount greater than 0 and not exceeding ₹{MAX_AMOUNT:,}.",
        )
        return

    date = expense_date.get_date().strftime(DATE_FORMAT)
    expenses.append((category, date, name, amount))
    total_expense += amount

    save_expenses()

    # Automatically switch month dropdown to the added expense's month so it shows up immediately
    added_month_str = datetime.strptime(date, DATE_FORMAT).strftime("%B %Y")
    month_dropdown.set(added_month_str)

    show_expenses()

    expense_name.delete(0, tk.END)
    expense_amount.delete(0, tk.END)
    expense_date.set_date(datetime.today())
    expense_name.focus()


def clear_expense():
    global total_expense
    if not expenses:
        messagebox.showinfo("Information", "There are no expenses to clear.")
        return
    if not messagebox.askyesno(
        "Clear Expenses", "Are you sure you want to clear all expenses?"
    ):
        return

    expenses.clear()
    total_expense = 0.0
    visible_expense_indices.clear()
    save_expenses()
    show_expenses()


def delete_selected():
    global total_expense
    selected = expense_list.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Please select an expense to delete.")
        return

    list_index = selected[0]
    if list_index >= len(visible_expense_indices):
        messagebox.showwarning("Error", "Please select the expense again.")
        show_expenses()
        return

    actual_index = visible_expense_indices[list_index]
    if actual_index >= len(expenses):
        messagebox.showwarning("Error", "Expense list has changed. Please try again.")
        show_expenses()
        return

    expenses.pop(actual_index)
    total_expense = sum(amount for *_, amount in expenses)
    save_expenses()
    show_expenses()


# ---------------------------------------------------------------------------
# Widget helpers
# ---------------------------------------------------------------------------
def make_label(parent, text, **kwargs):
    defaults = dict(font=("Arial", 11, "bold"), bg=CARD_BG, fg=LABEL_FG)
    defaults.update(kwargs)
    return tk.Label(parent, text=text, **defaults)


def make_entry(parent):
    return tk.Entry(
        parent,
        font=("Arial", 12),
        bd=0,
        relief="flat",
        bg=ENTRY_BG,
        fg="#334155",
        highlightthickness=1,
        highlightbackground=ENTRY_BORDER,
        highlightcolor=ENTRY_FOCUS,
    )


# ---------------------------------------------------------------------------
# Build UI
# ---------------------------------------------------------------------------
root = tk.Tk()
root.title("Expense Tracker")
root.geometry("750x850")
root.minsize(550, 650)
root.configure(bg=BG_COLOR)

tk.Label(
    root, text="Expense Tracker",
    font=("Arial", 26, "bold"), bg=BG_COLOR, fg="#1E3A8A",
).pack(pady=(20, 4))

tk.Label(
    root, text="Track your daily expenses easily",
    font=("Arial", 11), bg=BG_COLOR, fg="#64748B",
).pack(pady=(0, 15))

# --- Input card ---
input_frame = tk.Frame(
    root, bg=CARD_BG, bd=0,
    highlightthickness=1, highlightbackground="#E2E8F0",
)
input_frame.pack(padx=35, pady=(5, 10), fill="x", ipady=5)

make_label(input_frame, "Category").pack(anchor="w", padx=20, pady=(12, 4))
category_var = tk.StringVar(value=PLACEHOLDER_CATEGORY)
category_menu = tk.OptionMenu(input_frame, category_var, *CATEGORIES)
category_menu.config(font=("Arial", 11), bg=CARD_BG, anchor="w", bd=1)
category_menu.pack(padx=20, fill="x")

make_label(input_frame, "Expense Name").pack(anchor="w", padx=20, pady=(12, 4))
expense_name = make_entry(input_frame)
expense_name.pack(padx=20, fill="x", ipady=8)

make_label(input_frame, "Amount").pack(anchor="w", padx=20, pady=(12, 4))
expense_amount = make_entry(input_frame)
expense_amount.pack(padx=20, fill="x", ipady=8)

make_label(input_frame, "Date").pack(anchor="w", padx=20, pady=(12, 4))
expense_date = DateEntry(
    input_frame, width=18, font=("Arial", 12),
    date_pattern="dd-mm-yyyy",
    background="#222222", foreground="white", borderwidth=1,
)
expense_date.pack(padx=20, fill="x", ipady=4)

tk.Button(
    input_frame, text="＋  Add Expense", command=add_expense,
    font=("Arial", 11, "bold"),
    bg=PRIMARY, fg="white",
    activebackground=PRIMARY_ACTIVE, activeforeground="white",
    bd=0, cursor="hand2",
).pack(padx=20, pady=15, fill="x", ipady=8)

# --- Month selector & Display Section ---
control_frame = tk.Frame(root, bg=BG_COLOR)
control_frame.pack(padx=35, fill="x", pady=5)

tk.Label(
    control_frame, text="Select Month:",
    font=("Arial", 11, "bold"), bg=BG_COLOR, fg=LABEL_FG,
).pack(side="left", padx=(0, 10))

current_year = datetime.now().year
current_month_name = datetime.now().strftime("%B %Y")
month_options = [
    f"{month} {year}"
    for year in range(current_year - 1, current_year + 5)
    for month in MONTH_NAMES
]

month_dropdown = ttk.Combobox(
    control_frame, values=month_options, state="readonly",
    width=20, font=("Arial", 11),
)
month_dropdown.pack(side="left")
month_dropdown.set(current_month_name)
month_dropdown.bind("<<ComboboxSelected>>", show_expenses)

# --- List & Totals Card ---
list_frame = tk.Frame(
    root, bg=CARD_BG, bd=0,
    highlightthickness=1, highlightbackground="#E2E8F0",
)
list_frame.pack(padx=35, pady=10, fill="both", expand=True)

total_label = tk.Label(
    list_frame, text="", font=("Arial", 12, "bold"), bg=CARD_BG, fg="#1E3A8A"
)
total_label.pack(anchor="w", padx=20, pady=(15, 10))

list_container = tk.Frame(list_frame, bg=CARD_BG)
list_container.pack(padx=20, fill="both", expand=True)

expense_list = tk.Listbox(
    list_container, font=("Courier New", 10), bd=0, relief="flat",
    bg=ENTRY_BG, fg="#334155", selectbackground=PRIMARY,
    highlightthickness=1, highlightbackground=ENTRY_BORDER,
)
scrollbar = tk.Scrollbar(list_container, orient="vertical", command=expense_list.yview)
expense_list.config(yscrollcommand=scrollbar.set)

expense_list.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# --- Action Buttons ---
btn_frame = tk.Frame(list_frame, bg=CARD_BG)
btn_frame.pack(padx=20, pady=15, fill="x")

tk.Button(
    btn_frame, text="Delete Selected", command=delete_selected,
    font=("Arial", 10, "bold"), bg="#EF4444", fg="white",
    activebackground="#DC2626", activeforeground="white", bd=0, cursor="hand2",
).pack(side="left", ipadx=10, ipady=6)

tk.Button(
    btn_frame, text="Clear All", command=clear_expense,
    font=("Arial", 10, "bold"), bg="#64748B", fg="white",
    activebackground="#475569", activeforeground="white", bd=0, cursor="hand2",
).pack(side="right", ipadx=10, ipady=6)

# Load existing data and populate view
load_expenses()
show_expenses()

root.mainloop()
