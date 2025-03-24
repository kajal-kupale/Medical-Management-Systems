import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import time
import random
from datetime import datetime, date, timedelta

# ---------------------------
# Database Handler Classes
# ---------------------------
class AdminDB:
    def __init__(self, db_path="admin.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def check_login(self, username, password):
        self.cursor.execute("SELECT * FROM log WHERE username=? AND password=?", (username, password))
        return self.cursor.fetchone()

    def insert_valued_customer(self, name, address, vc_id):
        self.cursor.execute("INSERT INTO log (username, password) VALUES (?,?)", (name, vc_id))
        self.conn.commit()


class MedicineDB:
    def __init__(self, db_path="medicine.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def fetch_all_medicines(self):
        self.cursor.execute("SELECT * FROM med")
        return self.cursor.fetchall()

    def insert_medicine(self, data):
        # data should be a tuple with 9 items
        self.cursor.execute("INSERT INTO med VALUES (?,?,?,?,?,?,?,?,?)", data)
        self.conn.commit()

    def delete_medicine(self, sl_no):
        self.cursor.execute("DELETE FROM med WHERE sl_no=?", (sl_no,))
        self.conn.commit()

    def update_medicine(self, field, new_value, sl_no):
        sql = f"UPDATE med SET {field} = ? WHERE sl_no = ?"
        self.cursor.execute(sql, (new_value, sl_no))
        self.conn.commit()

    def search_by_symptom(self, symptom):
        self.cursor.execute("SELECT * FROM med WHERE purpose=?", (symptom,))
        return self.cursor.fetchall()

    def get_medicine_by_sl(self, sl_no):
        self.cursor.execute("SELECT * FROM med WHERE sl_no=?", (sl_no,))
        return self.cursor.fetchone()

    def update_quantity(self, sl_no, new_qty):
        self.cursor.execute("UPDATE med SET qty_left=? WHERE sl_no=?", (new_qty, sl_no))
        self.conn.commit()


# ---------------------------
# Main Application Class
# ---------------------------
class MedicalManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medical Management System")
        self.geometry("1024x768")
        self.resizable(False, False)

        # Set up a custom style for a modern look.
        style = ttk.Style()
        style.theme_use("clam")
        # Content area: light background, modern font.
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", foreground="#333333", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=5)
        style.map("TButton",
                  background=[("active", "#3c8dbc")],
                  foreground=[("active", "#ffffff")])

        # Sidebar style (we use tk.Frame directly for custom background).
        self.sidebar_bg = "#2c3e50"
        self.sidebar_fg = "#ecf0f1"
        self.sidebar_font = ("Segoe UI", 10, "bold")

        # Database handlers
        self.admin_db = AdminDB()
        self.medicine_db = MedicineDB()
        self.current_user_role = None  # 'admin' or 'customer'

        # Initially, show the login page.
        self.login_page = LoginPage(self)
        self.login_page.pack(fill="both", expand=True)

    def show_main_app(self):
        # Destroy the login page and create the main app layout.
        self.login_page.destroy()
        self.main_app = MainAppFrame(self)
        self.main_app.pack(fill="both", expand=True)


# ---------------------------
# Login Page (Full-screen Centered)
# ---------------------------
class LoginPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.configure(padding=40)

        # Center the login form using pack with expand.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        form_frame = ttk.Frame(self, padding=20)
        form_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = ttk.Label(form_frame, text="Medical Management System", font=("Segoe UI", 18, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(form_frame, text="Username:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=5)

        login_btn = ttk.Button(form_frame, text="Login", command=self.check_login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=20)

    def check_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        result = self.parent.admin_db.check_login(username, password)
        if result:
            self.parent.current_user_role = "admin" if username.lower() == "admin" else "customer"
            self.parent.show_main_app()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


# ---------------------------
# Main App Frame with Sidebar and Content Area
# ---------------------------
class MainAppFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Configure grid: 2 columns (sidebar and content)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Create sidebar
        self.sidebar = tk.Frame(self, bg=self.parent.sidebar_bg, width=220)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        # Create content area
        self.content = ttk.Frame(self)
        self.content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Build sidebar navigation buttons
        self.build_sidebar()

        # Dictionary of pages for easy switching
        self.pages = {}
        for P in (DashboardPage, StockPage, BillingPage, SearchPage, ExpiryCheckPage):
            page = P(self.content, self)
            self.pages[P.__name__] = page
            page.grid(row=0, column=0, sticky="nsew")
        self.show_page("DashboardPage")

    def build_sidebar(self):
        # Sidebar header
        header = tk.Label(self.sidebar, text="Navigation", bg=self.parent.sidebar_bg,
                          fg=self.parent.sidebar_fg, font=("Segoe UI", 14, "bold"))
        header.pack(pady=(20, 10))

        # List of (Button Text, Page Name)
        nav_items = [
            ("Dashboard", "DashboardPage"),
            ("Stock", "StockPage"),
            ("Billing", "BillingPage"),
            ("Search", "SearchPage"),
            ("Expiry Check", "ExpiryCheckPage")
        ]
        for text, page in nav_items:
            btn = tk.Button(self.sidebar, text=text, bg=self.parent.sidebar_bg, fg=self.parent.sidebar_fg,
                            activebackground="#34495e", activeforeground=self.parent.sidebar_fg,
                            font=self.parent.sidebar_font, bd=0,
                            command=lambda p=page: self.show_page(p))
            btn.pack(fill="x", padx=20, pady=5)

        # Spacer and Logout button at bottom
        spacer = tk.Label(self.sidebar, bg=self.parent.sidebar_bg)
        spacer.pack(expand=True)
        logout_btn = tk.Button(self.sidebar, text="Logout", bg="#e74c3c", fg="white",
                               activebackground="#c0392b", font=self.parent.sidebar_font, bd=0,
                               command=self.logout)
        logout_btn.pack(fill="x", padx=20, pady=20)

    def show_page(self, page_name):
        page = self.pages[page_name]
        page.tkraise()

    def logout(self):
        answer = messagebox.askyesno("Logout", "Do you really want to logout?")
        if answer:
            self.destroy()
            # Recreate login page on parent
            self.parent.login_page = LoginPage(self.parent)
            self.parent.login_page.pack(fill="both", expand=True)


# ---------------------------
# Dashboard Page
# ---------------------------
class DashboardPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ttk.Label(self, text="Welcome to the Dashboard", font=("Segoe UI", 16, "bold"))
        label.pack(pady=40)
        # Additional dashboard content can be added here.


# ---------------------------
# Stock Maintenance Page
# ---------------------------
class StockPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title = ttk.Label(self, text="Stock Maintenance", font=("Segoe UI", 16, "bold"))
        title.pack(pady=10)

        # Create a Treeview for stock items
        columns = ("sl_no", "name", "type", "qty_left", "cost", "purpose", "exp_date", "rack", "mfg")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=90)
        self.tree.pack(padx=20, pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_stock).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Add", command=self.add_product).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_product).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Modify", command=self.modify_product).grid(row=0, column=3, padx=5)

        self.refresh_stock()

    def refresh_stock(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        medicines = self.controller.parent.medicine_db.fetch_all_medicines()
        for med in medicines:
            self.tree.insert("", "end", values=med)

    def add_product(self):
        AddProductWindow(self.controller.parent)

    def delete_product(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Delete", "Select a product to delete.")
            return
        values = self.tree.item(selected, "values")
        if messagebox.askyesno("Confirm", f"Delete product '{values[1]}'?"):
            self.controller.parent.medicine_db.delete_medicine(values[0])
            self.refresh_stock()

    def modify_product(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Modify", "Select a product to modify.")
            return
        values = self.tree.item(selected, "values")
        ModifyProductWindow(self.controller.parent, values)


# ---------------------------
# Billing Page
# ---------------------------
class BillingPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bill_items = []  # list of tuples (sl_no, name, quantity)

        title = ttk.Label(self, text="Billing System", font=("Segoe UI", 16, "bold"))
        title.pack(pady=10)

        cust_frame = ttk.Frame(self)
        cust_frame.pack(pady=10)
        ttk.Label(cust_frame, text="Customer Name:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_name = ttk.Entry(cust_frame, width=30)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(cust_frame, text="Address:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_address = ttk.Entry(cust_frame, width=30)
        self.entry_address.grid(row=1, column=1, padx=5, pady=5)

        med_frame = ttk.Frame(self)
        med_frame.pack(pady=10)
        self.med_tree = ttk.Treeview(med_frame, columns=("sl_no", "name", "qty_left", "cost", "rack"),
                                     show="headings", height=5)
        for col in ("sl_no", "name", "qty_left", "cost", "rack"):
            self.med_tree.heading(col, text=col.capitalize())
            self.med_tree.column(col, width=100)
        self.med_tree.grid(row=0, column=0, columnspan=4, padx=5, pady=5)
        ttk.Button(med_frame, text="Refresh Stock", command=self.refresh_stock).grid(row=1, column=0, padx=5)
        ttk.Button(med_frame, text="Add to Bill", command=self.add_to_bill).grid(row=1, column=1, padx=5)
        ttk.Label(med_frame, text="Quantity:").grid(row=1, column=2, padx=5)
        self.entry_qty = ttk.Entry(med_frame, width=10)
        self.entry_qty.grid(row=1, column=3, padx=5)
        
        self.txt_bill = tk.Text(self, width=80, height=10)
        self.txt_bill.pack(pady=10)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Print & Save Bill", command=self.print_and_save_bill).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Reset Bill", command=self.reset_bill).grid(row=0, column=1, padx=5)

        self.refresh_stock()

    def refresh_stock(self):
        for item in self.med_tree.get_children():
            self.med_tree.delete(item)
        medicines = self.controller.parent.medicine_db.fetch_all_medicines()
        for med in medicines:
            self.med_tree.insert("", "end", values=(med[0], med[1], med[3], med[4], med[7]))

    def add_to_bill(self):
        selected = self.med_tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Select a medicine.")
            return
        qty = self.entry_qty.get().strip()
        if not qty.isdigit() or int(qty) <= 0:
            messagebox.showwarning("Quantity", "Enter a valid quantity.")
            return
        values = self.med_tree.item(selected, "values")
        self.bill_items.append((values[0], values[1], int(qty)))
        self.entry_qty.delete(0, tk.END)
        self.generate_bill_summary()

    def generate_bill_summary(self):
        self.txt_bill.delete("1.0", tk.END)
        total = 0.0
        summary = "Bill Summary\n" + "="*40 + "\n"
        for sl_no, name, qty in self.bill_items:
            med = self.controller.parent.medicine_db.get_medicine_by_sl(sl_no)
            if med:
                price = float(med[4])
                cost = price * qty
                total += cost
                summary += f"{name}: {qty} x PHP {price:.2f} = PHP {cost:.2f}\n"
        summary += "="*40 + f"\nTotal: PHP {total:.2f}\n"
        self.txt_bill.insert(tk.END, summary)

    def reset_bill(self):
        self.bill_items.clear()
        self.txt_bill.delete("1.0", tk.END)

    def print_and_save_bill(self):
        content = self.txt_bill.get("1.0", tk.END)
        bill_no = random.randint(100, 999)
        filename = f"bill_{bill_no}.txt"
        with open(filename, "w") as f:
            f.write(content)
        messagebox.showinfo("Bill Saved", f"Bill saved as {filename}.")
        # Update stock quantities
        for sl_no, _, qty in self.bill_items:
            med = self.controller.parent.medicine_db.get_medicine_by_sl(sl_no)
            if med:
                new_qty = max(0, int(med[3]) - qty)
                self.controller.parent.medicine_db.update_quantity(sl_no, new_qty)
        self.reset_bill()
        self.refresh_stock()


# ---------------------------
# Search Page
# ---------------------------
class SearchPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title = ttk.Label(self, text="Search Medicines", font=("Segoe UI", 16, "bold"))
        title.pack(pady=10)

        search_frame = ttk.Frame(self)
        search_frame.pack(pady=10)
        ttk.Label(search_frame, text="Symptom/Purpose:").grid(row=0, column=0, padx=5, pady=5)
        self.symptom_box = ttk.Combobox(search_frame, values=self.get_symptom_list(), state="readonly", width=30)
        self.symptom_box.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="Search", command=self.search_medicines).grid(row=0, column=2, padx=5, pady=5)

        self.results_text = tk.Text(self, width=80, height=10)
        self.results_text.pack(pady=10)

    def get_symptom_list(self):
        meds = self.controller.parent.medicine_db.fetch_all_medicines()
        return sorted(set(med[5] for med in meds))

    def search_medicines(self):
        symptom = self.symptom_box.get()
        results = self.controller.parent.medicine_db.search_by_symptom(symptom)
        self.results_text.delete("1.0", tk.END)
        if results:
            for med in results:
                self.results_text.insert(tk.END,
                    f"ID: {med[0]}, Name: {med[1]}, Cost: PHP {med[4]}, Rack: {med[7]}, MFG: {med[8]}\n")
        else:
            self.results_text.insert(tk.END, "No results found.")


# ---------------------------
# Expiry Check Page
# ---------------------------
class ExpiryCheckPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title = ttk.Label(self, text="Expiry Check", font=("Segoe UI", 16, "bold"))
        title.pack(pady=10)

        today_str = date.today().strftime("%d/%m/%Y")
        ttk.Label(self, text=f"Today's Date: {today_str}").pack(pady=5)

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)
        ttk.Label(form_frame, text="Medicine:").grid(row=0, column=0, padx=5, pady=5)
        self.med_box = ttk.Combobox(form_frame, values=self.get_medicine_names(), state="readonly", width=30)
        self.med_box.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(form_frame, text="Check", command=self.check_expiry).grid(row=0, column=2, padx=5, pady=5)

        self.result_label = ttk.Label(self, text="", foreground="red", font=("Segoe UI", 12, "bold"))
        self.result_label.pack(pady=10)

    def get_medicine_names(self):
        meds = self.controller.parent.medicine_db.fetch_all_medicines()
        return [med[1] for med in meds]

    def check_expiry(self):
        med_name = self.med_box.get()
        meds = self.controller.parent.medicine_db.fetch_all_medicines()
        for med in meds:
            if med[1] == med_name:
                try:
                    exp_str = med[6]  # Expected format "DD/MM/YY"
                    exp_date = datetime.strptime(exp_str, "%d/%m/%y").date()
                    today = date.today()
                    if today > exp_date:
                        self.result_label.config(text=f"Medicine '{med_name}' expired on {exp_str}!")
                    else:
                        self.result_label.config(text=f"Medicine '{med_name}' is valid (expires on {exp_str}).")
                except Exception as e:
                    self.result_label.config(text="Date format error.")
                break


# ---------------------------
# Auxiliary Windows for Stock Management
# ---------------------------
class AddProductWindow(tk.Toplevel):
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.title("Add New Product")
        self.resizable(False, False)
        self.parent_app = parent_app

        labels = ["Name", "Type", "Qty Left", "Cost", "Purpose", "Expiry Date (DD/MM/YY)", "Rack", "MFG"]
        self.entries = {}
        for i, text in enumerate(labels):
            ttk.Label(self, text=f"{text}:").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(self, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[text] = entry

        ttk.Button(self, text="Submit", command=self.submit).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def submit(self):
        meds = self.parent_app.medicine_db.fetch_all_medicines()
        try:
            new_sl = int(meds[-1][0]) + 1 if meds else 1
        except Exception:
            new_sl = 1
        data = (
            new_sl,
            self.entries["Name"].get(),
            self.entries["Type"].get(),
            self.entries["Qty Left"].get(),
            self.entries["Cost"].get(),
            self.entries["Purpose"].get(),
            self.entries["Expiry Date (DD/MM/YY)"].get(),
            self.entries["Rack"].get(),
            self.entries["MFG"].get(),
        )
        self.parent_app.medicine_db.insert_medicine(data)
        messagebox.showinfo("Success", "Product added successfully.")
        self.destroy()


class ModifyProductWindow(tk.Toplevel):
    def __init__(self, parent_app, med_values):
        super().__init__(parent_app)
        self.title("Modify Product")
        self.resizable(False, False)
        self.parent_app = parent_app
        self.med_values = med_values

        fields = ["Name", "Type", "Qty Left", "Cost", "Purpose", "Expiry Date", "Rack", "MFG"]
        self.entries = {}
        ttk.Label(self, text=f"Modifying Product ID {med_values[0]}", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )
        for i, field in enumerate(fields):
            ttk.Label(self, text=f"{field}:").grid(row=i+1, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(self, width=30)
            entry.insert(0, med_values[i+1])
            entry.grid(row=i+1, column=1, padx=5, pady=5)
            self.entries[field] = entry

        ttk.Button(self, text="Save Changes", command=self.save_changes).grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

    def save_changes(self):
        sl_no = self.med_values[0]
        new_values = (
            self.entries["Name"].get(),
            self.entries["Type"].get(),
            self.entries["Qty Left"].get(),
            self.entries["Cost"].get(),
            self.entries["Purpose"].get(),
            self.entries["Expiry Date"].get(),
            self.entries["Rack"].get(),
            self.entries["MFG"].get(),
        )
        fields = ("name", "type", "qty_left", "cost", "purpose", "exp_date", "rack", "mfg")
        for field, value in zip(fields, new_values):
            self.parent_app.medicine_db.update_medicine(field, value, sl_no)
        messagebox.showinfo("Updated", "Product updated successfully.")
        self.destroy()


# ---------------------------
# Run the Application
# ---------------------------
if __name__ == "__main__":
    app = MedicalManagementApp()
    app.mainloop()
