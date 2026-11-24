import json
import math
import tkinter as tk
import shutil
import os
from datetime import datetime
from tkinter import messagebox, ttk
from tkinter import filedialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from tkcalendar import DateEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FILE_NAME = "expenses.json"
BACKUP_FILE = "expenses_backup.json"
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

BG_COLOR = "#ECFDF5"
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
editing_index = None
total_expense = 0.0
visible_expense_indices = []


def recalculate_total():
    global total_expense
    total_expense = sum(amount for *_, amount in expenses)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def create_backup():
    if os.path.exists(FILE_NAME):
        shutil.copy2(FILE_NAME, BACKUP_FILE)

def save_expenses():
    try:
        create_backup()
        with open(FILE_NAME, "w") as file:
            json.dump(expenses, file)
    except OSError as error:
        messagebox.showerror("Save Error", f"Expenses could not be saved.\n{error}")

def restore_backup():
    if not os.path.exists(BACKUP_FILE):
        messagebox.showwarning("Backup", "No backup found!")
        return

    confirm = messagebox.askyesno(
        "Restore Backup",
        "Are you sure you want to restore the previous data?"
    )

    if confirm:
        shutil.copy2(BACKUP_FILE, FILE_NAME)
        expenses.clear()
        load_expenses()
        show_expenses()
        messagebox.showinfo("Backup", "Backup restored successfully!")

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
    if not math.isfinite(amount) or amount <= 0:
        return None
    return category, date, name, amount


def load_expenses():
    try:
        with open(FILE_NAME, "r") as file:
            saved = json.load(file)
        if not isinstance(saved, list):
            raise ValueError("Expense data must be a list.")
    except FileNotFoundError:
        recalculate_total()
        return
    except (json.JSONDecodeError, ValueError, TypeError):
        messagebox.showwarning(
            "Data Warning",
            "Expense file is damaged or has an invalid format.",
        )
        recalculate_total()
        return

    for item in saved:
        parsed = _parse_expense(item)
        if parsed:
            expenses.append(parsed)
    recalculate_total()


# ---------------------------------------------------------------------------
# UI actions
# ---------------------------------------------------------------------------
def set_form_mode(is_editing):
    if is_editing:
        add_btn.config(text="✔  Update Expense")
    else:
        add_btn.config(text="＋  Add Expense")


def reset_form():
    global editing_index
    editing_index = None
    category_var.set(PLACEHOLDER_CATEGORY)
    expense_name.delete(0, tk.END)
    expense_amount.delete(0, tk.END)
    expense_date.set_date(datetime.today())
    set_form_mode(False)


def show_expenses(event=None):
    global visible_expense_indices
    expense_list.delete(0, tk.END)
    visible_expense_indices = []

    selected_month = month_dropdown.get()
    if not selected_month or selected_month == PLACEHOLDER_MONTH:
        total_label.config(text="Please choose a month")
        monthly_value.config(text="₹0.00")
        entries_value.config(text="0")
        category_left_value.config(text="No data")
        category_right_value.config(text="")
        return

    month_total = 0.0
    month_entries = 0
    category_totals = {}
    for index, (category, date, name, amount) in enumerate(expenses):
        expense_month = datetime.strptime(date, DATE_FORMAT).strftime("%B %Y")
        if expense_month != selected_month:
            continue
        visible_expense_indices.append(index)
        expense_list.insert(tk.END, f"{category} | {name} | ₹{amount:.2f} | {date}")
        month_total += amount
        month_entries += 1
        category_totals[category] = category_totals.get(category, 0) + amount

    total_label.config(text=f"Total Expense ({selected_month}): ₹{month_total:,.2f}")

    if not visible_expense_indices:
        expense_list.insert(tk.END, "No expenses found for this month")

    for row_number in range(expense_list.size()):
        row_color = "#FFFFFF" if row_number % 2 == 0 else "#ECFDF5"
        expense_list.itemconfig(row_number, bg=row_color)

    monthly_value.config(text=f"₹{month_total:,.2f}")
    entries_value.config(text=str(month_entries))

    if category_totals:
        category_items = list(category_totals.items())
        left_categories = category_items[:3]
        right_categories = category_items[3:6]

        left_text = "\n".join(f"{cat}: ₹{amt:,.0f}" for cat, amt in left_categories)
        right_text = "\n".join(f"{cat}: ₹{amt:,.0f}" for cat, amt in right_categories)
    else:
        left_text = "No data"
        right_text = ""

    category_left_value.config(text=left_text)
    category_right_value.config(text=right_text)


def add_expense():
    global editing_index

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
    if editing_index is not None:
        if 0 <= editing_index < len(expenses):
            expenses[editing_index] = (category, date, name, amount)
        editing_index = None
    else:
        expenses.append((category, date, name, amount))

    recalculate_total()
    save_expenses()

    added_month_str = datetime.strptime(date, DATE_FORMAT).strftime("%B %Y")
    if added_month_str in month_dropdown["values"]:
        month_dropdown.set(added_month_str)

    show_expenses()
    reset_form()

def export_pdf():
    selected_month = month_dropdown.get()

    if not selected_month or selected_month == PLACEHOLDER_MONTH:
        messagebox.showwarning("Warning", "Please choose a month first.")
        return

    month_expenses = [
        item for item in expenses
        if datetime.strptime(item[1], DATE_FORMAT).strftime("%B %Y") == selected_month
    ]
    month_expenses.sort(
        key=lambda item: datetime.strptime(item[1], DATE_FORMAT)
    )
    
    if not month_expenses:
        messagebox.showinfo("Information", "No expenses found for this month.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Files", "*.pdf")],
        initialfile=selected_month.replace(" ", "_") + "_Report.pdf"
    )

    if not file_path:
        return

    pdf = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 50

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "Expense Tracker Report")

    y -= 30
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, selected_month)

    month_total = sum(item[3] for item in month_expenses)

    y -= 35
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, f"Total Expense: Rs. {month_total:,.2f}")

    category_totals = {}

    for category, date, name, amount in month_expenses:
        category_totals[category] = category_totals.get(category, 0) + amount

    y -= 35
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Category-wise Summary")

    y -= 22
    pdf.setFont("Helvetica", 10)

    for category, amount in category_totals.items():
        pdf.drawString(60, y, f"{category}: Rs. {amount:,.2f}")
        y -= 18

    y -= 15
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Date-wise Expense List")

    y -= 22
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(50, y, "Category")
    pdf.drawString(160, y, "Name")
    pdf.drawString(350, y, "Date")
    pdf.drawString(450, y, "Amount")

    y -= 18
    pdf.setFont("Helvetica", 9)

    for category, date, name, amount in month_expenses:
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 9)

        pdf.drawString(50, y, category[:18])
        pdf.drawString(160, y, name[:30])
        pdf.drawString(350, y, date)
        pdf.drawString(450, y, f"Rs. {amount:,.2f}")
        y -= 18

    pdf.save()

    messagebox.showinfo("Success", "PDF report saved successfully!")

def clear_expense():
    selected_month = month_dropdown.get()

    if not selected_month or selected_month == PLACEHOLDER_MONTH:
        messagebox.showwarning("Warning", "Please choose a month first.")
        return

    month_expenses = [
        item
        for item in expenses
        if datetime.strptime(item[1], DATE_FORMAT).strftime("%B %Y") == selected_month
    ]

    if not month_expenses:
        messagebox.showinfo("Information", f"No expenses to clear for {selected_month}.")
        return

    if not messagebox.askyesno(
        "Clear This Month",
        f"Are you sure you want to delete all expenses for {selected_month}?",
    ):
        return

    expenses[:] = [
        item
        for item in expenses
        if datetime.strptime(item[1], DATE_FORMAT).strftime("%B %Y") != selected_month
    ]

    recalculate_total()
    visible_expense_indices.clear()
    save_expenses()
    reset_form()
    show_expenses()


def delete_selected():
    if not visible_expense_indices:
        messagebox.showinfo("Information", "There are no expenses to delete.")
        return

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
    recalculate_total()
    save_expenses()
    reset_form()
    show_expenses()


def edit_selected():
    global editing_index

    if not visible_expense_indices:
        messagebox.showinfo("Information", "There are no expenses to edit.")
        return

    selected = expense_list.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Please select an expense to edit.")
        return

    list_index = selected[0]
    if list_index >= len(visible_expense_indices):
        messagebox.showwarning("Error", "Please select the expense again.")
        show_expenses()
        return

    actual_index = visible_expense_indices[list_index]
    editing_index = actual_index

    category, date, name, amount = expenses[actual_index]

    category_var.set(category)
    expense_name.delete(0, tk.END)
    expense_name.insert(0, name)

    expense_amount.delete(0, tk.END)
    expense_amount.insert(0, str(amount))

    expense_date.set_date(datetime.strptime(date, DATE_FORMAT))
    set_form_mode(True)


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
        font=("Segoe UI", 12),
        bd=0,
        relief="flat",
        bg=ENTRY_BG,
        fg="#334155",
        highlightthickness=1,
        highlightbackground="#D1FAE5",
        highlightcolor="#059669",
    )


# ---------------------------------------------------------------------------
# Build UI
# ---------------------------------------------------------------------------
root = tk.Tk()
style = ttk.Style()
style.theme_use("clam")

root.title("Expense Tracker")
root.geometry("750x850")
root.state("zoomed")
root.minsize(550, 650)
root.configure(bg=BG_COLOR)

# --- Scrollable Page ---
main_canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0)
main_scrollbar = tk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
main_canvas.configure(yscrollcommand=main_scrollbar.set)

main_scrollbar.pack(side="right", fill="y")
main_canvas.pack(side="left", fill="both", expand=True)

scrollable_frame = tk.Frame(main_canvas, bg=BG_COLOR)
canvas_window = main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")


def update_scroll_region(event):
    main_canvas.configure(scrollregion=main_canvas.bbox("all"))


scrollable_frame.bind("<Configure>", update_scroll_region)


def resize_scrollable_frame(event):
    main_canvas.itemconfig(canvas_window, width=event.width)


main_canvas.bind("<Configure>", resize_scrollable_frame)


def on_mousewheel(event):
    main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


main_canvas.bind("<Enter>", lambda e: main_canvas.bind_all("<MouseWheel>", on_mousewheel))
main_canvas.bind("<Leave>", lambda e: main_canvas.unbind_all("<MouseWheel>"))

tk.Label(
    scrollable_frame,
    text="Expense Tracker",
    font=("Segoe UI", 22, "bold"),
    bg=BG_COLOR,
    fg="#0F172A",
).pack(pady=(25, 5))

tk.Label(
    scrollable_frame,
    text="Manage your daily expenses easily",
    font=("Segoe UI", 11),
    bg=BG_COLOR,
    fg="#64748B",
).pack(pady=(0, 18))

# --- Dashboard ---
dashboard_frame = tk.Frame(scrollable_frame, bg=BG_COLOR)
dashboard_frame.pack(padx=35, pady=6, fill="x")

# Monthly Expense Card
monthly_card = tk.Frame(
    dashboard_frame,
    bg=CARD_BG,
    highlightthickness=1,
    highlightbackground="#D1FAE5",
)
monthly_card.pack(side="left", expand=True, fill="both", padx=(0, 8))
tk.Label(
    monthly_card,
    text="Monthly Expense",
    font=("Arial", 11),
    bg=CARD_BG,
    fg=LABEL_FG,
).pack(pady=(8, 5))

monthly_value = tk.Label(
    monthly_card,
    text="₹0.00",
    font=("Arial", 20, "bold"),
    bg=CARD_BG,
    fg="#059669",
)
monthly_value.pack(pady=(0, 12))

# Total Entries Card
entries_card = tk.Frame(
    dashboard_frame,
    bg=CARD_BG,
    highlightthickness=1,
    highlightbackground="#D1FAE5",
)
entries_card.pack(side="left", expand=True, fill="both", padx=(8, 0))

tk.Label(
    entries_card,
    text="Total Entries",
    font=("Arial", 11),
    bg=CARD_BG,
    fg=LABEL_FG,
).pack(pady=(8, 5))

entries_value = tk.Label(
    entries_card,
    text="0",
    font=("Arial", 20, "bold"),
    bg=CARD_BG,
    fg="#0F766E",
)
entries_value.pack(pady=(0, 12))

# Category-wise Expense Card
category_card = tk.Frame(
    dashboard_frame,
    bg=CARD_BG,
    highlightthickness=1,
    highlightbackground="#D1FAE5",
)
category_card.pack(side="left", expand=True, fill="both", padx=(8, 0))

tk.Label(
    category_card,
    text="Category-wise Expense",
    font=("Arial", 11),
    bg=CARD_BG,
    fg=LABEL_FG,
).pack(pady=(8, 5))

category_columns = tk.Frame(category_card, bg=CARD_BG)
category_columns.pack(fill="x", padx=5, pady=(0, 10))

category_left_value = tk.Label(
    category_columns,
    text="",
    font=("Arial", 9, "bold"),
    bg=CARD_BG,
    fg="#0F766E",
    justify="left",
)
category_left_value.pack(side="left", expand=True)

category_right_value = tk.Label(
    category_columns,
    text="",
    font=("Arial", 9, "bold"),
    bg=CARD_BG,
    fg="#0F766E",
    justify="left",
)
category_right_value.pack(side="left", expand=True)

# --- Input card ---
input_frame = tk.Frame(
    scrollable_frame,
    bg=CARD_BG,
    bd=0,
    highlightthickness=1,
    highlightbackground="#D1FAE5",
)
input_frame.pack(padx=35, pady=(5, 10), fill="x", ipady=5)

make_label(input_frame, "Category").pack(anchor="w", padx=20, pady=(12, 4))
category_var = tk.StringVar(value=PLACEHOLDER_CATEGORY)
category_menu = tk.OptionMenu(input_frame, category_var, *CATEGORIES)
category_menu.config(
    font=("Arial", 11),
    bg="#ECFDF5",
    fg="#0F766E",
    activebackground="#D1FAE5",
    activeforeground="#0F766E",
    anchor="w",
    bd=0,
    cursor="hand2",
)
category_menu.pack(padx=20, fill="x")

make_label(input_frame, "Expense Name").pack(anchor="w", padx=20, pady=(12, 4))
expense_name = make_entry(input_frame)
expense_name.pack(padx=20, fill="x", ipady=8)


def validate_amount(value):
    if value == "":
        return True
    if value.count(".") > 1:
        return False
    return value.replace(".", "", 1).isdigit()


amount_check = root.register(validate_amount)

# Amount and Date Row
details_frame = tk.Frame(input_frame, bg=CARD_BG)
details_frame.pack(padx=20, fill="x", pady=(12, 0))

# Amount - Left Side
amount_frame = tk.Frame(details_frame, bg=CARD_BG)
amount_frame.pack(side="left", expand=True, fill="x", padx=(0, 8))

make_label(amount_frame, "Amount").pack(anchor="w", pady=(0, 4))

expense_amount = make_entry(amount_frame)
expense_amount.pack(fill="x", ipady=8)
expense_amount.config(validate="key", validatecommand=(amount_check, "%P"))

# Date - Right Side
date_frame = tk.Frame(details_frame, bg=CARD_BG)
date_frame.pack(side="left", expand=True, fill="x", padx=(8, 0))

make_label(date_frame, "Date").pack(anchor="w", pady=(0, 4))

expense_date = DateEntry(
    date_frame,
    width=18,
    font=("Arial", 12),
    date_pattern="dd-mm-yyyy",
    background="#059669",
    foreground="white",
    borderwidth=1,
    maxdate=datetime.today(),
)
expense_date.pack(fill="x", ipady=4)


def keep_date_calendar_open(event):
    event.widget._top_cal.overrideredirect(False)


expense_date.bind("<<DateEntryPopup>>", keep_date_calendar_open)

add_btn = tk.Button(
    input_frame,
    text="＋  Add Expense",
    command=add_expense,
    font=("Segoe UI", 11, "bold"),
    bg="#059669",
    fg="white",
    activebackground="#047857",
    activeforeground="white",
    bd=0,
    cursor="hand2",
)
add_btn.pack(padx=20, pady=15, fill="x", ipady=10)

# --- Month selector & Display Section ---
control_frame = tk.Frame(scrollable_frame, bg=BG_COLOR)
control_frame.pack(padx=35, fill="x", pady=5, expand=False)

tk.Label(
    control_frame,
    text="Select Month:",
    font=("Arial", 11, "bold"),
    bg=BG_COLOR,
    fg=LABEL_FG,
).pack(side="left", padx=(0, 10))

current_year = datetime.now().year
current_month_name = datetime.now().strftime("%B %Y")
month_options = [
    f"{month} {year}"
    for year in range(current_year - 1, current_year + 5)
    for month_number, month in enumerate(MONTH_NAMES, start=1)
    if year < current_year or (year == current_year and month_number <= datetime.now().month)
]
month_dropdown = ttk.Combobox(
    control_frame,
    values=month_options,
    state="readonly",
    width=20,
    font=("Arial", 11),
)
month_dropdown.pack(side="left", padx=5, pady=5)
month_dropdown.set(current_month_name)
month_dropdown.bind("<<ComboboxSelected>>", show_expenses)

# --- List & Totals Card ---
list_frame = tk.Frame(
    scrollable_frame,
    bg=CARD_BG,
    bd=0,
    highlightthickness=1,
    highlightbackground="#D1FAE5",
)
list_frame.pack(padx=35, pady=10, fill="both", expand=True)

total_label = tk.Label(
    list_frame,
    text="",
    font=("Segoe UI", 12, "bold"),
    bg="#ECFDF5",
    fg="#0F766E",
    padx=12,
    pady=6,
)
total_label.pack(fill="x", padx=20, pady=(12, 4))

# --- Expenses Records ---
records_header = tk.Frame(list_frame, bg=CARD_BG)
records_header.pack(padx=20, pady=5, fill="x")

tk.Label(
    records_header,
    text="Expenses Records",
    font=("Segoe UI", 12, "bold"),
    bg=CARD_BG,
    fg="#0F766E",
).pack(anchor="w")

list_container = tk.Frame(list_frame, bg=CARD_BG)
list_container.pack(padx=20, fill="both", expand=True)

expense_list = tk.Listbox(
    list_container,
    font=("Segoe UI", 10),
    bd=0,
    relief="flat",
    bg=ENTRY_BG,
    fg="#334155",
    selectforeground="white",
    selectbackground="#059669",
    highlightthickness=1,
    highlightbackground=ENTRY_BORDER,
    height=4,
)

scrollbar = tk.Scrollbar(list_container, orient="vertical", command=expense_list.yview)
expense_list.config(yscrollcommand=scrollbar.set)

expense_list.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# --- Action Buttons ---
btn_frame = tk.Frame(list_frame, bg=CARD_BG)
btn_frame.pack(padx=20, pady=10, fill="x")

tk.Button(
    btn_frame,
    text="Delete Selected",
    command=delete_selected,
    font=("Segoe UI", 10, "bold"),
    bg="#EF4444",
    fg="white",
    activebackground="#DC2626",
    activeforeground="white",
    bd=0,
    cursor="hand2",
).pack(side="left", ipadx=10, ipady=6)

tk.Button(
    btn_frame,
    text="Edit Selected",
    command=edit_selected,
    font=("Segoe UI", 10, "bold"),
    bg="#059669",
    fg="white",
    activebackground="#047857",
    activeforeground="white",
    bd=0,
    cursor="hand2",
).pack(side="left", padx=10, ipadx=10, ipady=6)

tk.Button(
    btn_frame,
    text="Clear This Month",
    command=clear_expense,
    font=("Segoe UI", 10, "bold"),
    bg="#64748B",
    fg="white",
    activebackground="#475569",
    activeforeground="white",
    bd=0,
    cursor="hand2",
).pack(side="right", ipadx=10, ipady=6)

tk.Button(
    btn_frame,
    text="Restore Backup",
    command=restore_backup,
    font=("Segoe UI", 10, "bold"),
    bg="#16A34A",
    fg="white",
    activebackground="#15803D",
    activeforeground="white",
    bd=0,
    cursor="hand2",
).pack(side="right", ipadx=10, ipady=6, padx=5)

# --- Export Monthly Report ---
export_frame = tk.Frame(list_frame, bg=CARD_BG)
export_frame.pack(padx=20, pady=(5, 15), fill="x")

tk.Button(
    export_frame,
    text="Download Monthly PDF",
    command=export_pdf,
    font=("Segoe UI", 10, "bold"),
    bg="#2563EB",
    fg="white",
    activebackground="#1D4ED8",
    activeforeground="white",
    bd=0,
    cursor="hand2",
).pack(fill="x", ipady=8)

# Load existing data and populate view
load_expenses()
show_expenses()

root.mainloop()
