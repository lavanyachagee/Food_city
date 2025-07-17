import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk # For Treeview for better table display
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import datetime, timedelta
import numpy as np # For statistical calculations like mode

# --- Data Management Class ---
# S (Single Responsibility Principle): This class is solely responsible for data loading, saving, and providing
# filtered/aggregated data to the UI components. It doesn't handle any UI logic.
class DataManager:
    """Manages all sales data operations, including loading, saving, and querying."""
    def __init__(self, data_file="sales_data.csv"):
        self.data_file = data_file
        self.sales_data = self._load_data()

    def _load_data(self):
        """Loads sales data from the specified CSV file. Returns empty DataFrame if file not found or error."""
        if os.path.exists(self.data_file):
            try:
                # Assuming CSV has columns: Date, Branch, Product, Quantity, UnitPrice, Total
                # 'Date' is parsed as datetime, 'Total' and 'Quantity' as numeric
                df = pd.read_csv(self.data_file, parse_dates=['Date'])
                df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
                df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
                df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
                # Drop rows where essential numeric data is missing
                df.dropna(subset=['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'], inplace=True)
                return df
            except Exception as e:
                messagebox.showerror("Data Load Error", f"Failed to load data from {self.data_file}: {e}\nStarting with empty data.")
                # Return an empty DataFrame with expected columns if loading fails
                return pd.DataFrame(columns=['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'])
        else:
            # Return an empty DataFrame if file doesn't exist
            return pd.DataFrame(columns=['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'])

    def add_data(self, new_df):
        """Adds new DataFrame records to the existing sales data and saves."""
        # Basic validation: check if columns match
        required_cols = ['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total']
        if not all(col in new_df.columns for col in required_cols):
            messagebox.showerror("Import Error", "Imported file missing one or more required columns: 'Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'.")
            return False

        # Ensure 'Date' is datetime and numeric columns are correctly typed before concatenating
        try:
            new_df['Date'] = pd.to_datetime(new_df['Date'])
            new_df['Quantity'] = pd.to_numeric(new_df['Quantity'], errors='coerce')
            new_df['UnitPrice'] = pd.to_numeric(new_df['UnitPrice'], errors='coerce')
            new_df['Total'] = pd.to_numeric(new_df['Total'], errors='coerce')
            # Drop rows where essential numeric data is missing after conversion
            new_df.dropna(subset=['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'], inplace=True)
        except Exception as e:
            messagebox.showerror("Data Conversion Error", f"Error converting data types during import. Ensure 'Date' is a valid date format and numeric columns contain numbers: {e}")
            return False

        if new_df.empty:
            messagebox.showwarning("No Valid Data", "No valid records to add after processing. Check your file for empty or malformed rows.")
            return False

        self.sales_data = pd.concat([self.sales_data, new_df], ignore_index=True)
        self._save_data()
        return True

    def _save_data(self):
        """Saves the current sales data DataFrame to the CSV file."""
        try:
            self.sales_data.to_csv(self.data_file, index=False)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data to {self.data_file}: {e}")

    def get_branches(self):
        """Returns a sorted list of unique branch names."""
        return sorted(self.sales_data['Branch'].unique().tolist()) if not self.sales_data.empty else []

    def get_products(self):
        """Returns a sorted list of unique product names."""
        return sorted(self.sales_data['Product'].unique().tolist()) if not self.sales_data.empty else []

    def get_years(self):
        """Returns a sorted list of unique years present in the data."""
        if not self.sales_data.empty and 'Date' in self.sales_data.columns:
            return sorted(self.sales_data['Date'].dt.year.unique().tolist())
        return [datetime.now().year] # Provide current year as a default if no data

    def get_monthly_sales(self, branch=None, year=None, month=None):
        """
        Filters sales data by branch, year, and month, then aggregates total sales per product.
        Returns a DataFrame with 'Product' and 'Total' columns.
        """
        df = self.sales_data.copy()
        if df.empty:
            return pd.DataFrame(columns=['Product', 'Quantity', 'UnitPrice', 'Total'])

        if branch and branch != "All Branches":
            df = df[df['Branch'] == branch]
        if year:
            df = df[df['Date'].dt.year == year]
        if month:
            df = df[df['Date'].dt.month == month]

        if df.empty:
            return pd.DataFrame(columns=['Product', 'Quantity', 'UnitPrice', 'Total'])

        # Aggregate by product, sum quantity and total, average unit price
        return df.groupby('Product').agg(
            Quantity=('Quantity', 'sum'),
            UnitPrice=('UnitPrice', 'mean'), # Average unit price for summary
            Total=('Total', 'sum')
        ).reset_index()

    def get_product_price_history(self, product_name):
        """
        Retrieves historical unit prices for a specific product.
        Returns a DataFrame with 'Date' and 'UnitPrice' columns, sorted by date.
        """
        if self.sales_data.empty:
            return pd.DataFrame(columns=['Date', 'UnitPrice'])
        # Filter for the product, select relevant columns, drop duplicates for unique price points per day
        # and sort by date to show trend.
        return self.sales_data[self.sales_data['Product'] == product_name][['Date', 'UnitPrice']].drop_duplicates().sort_values(by='Date')

    def get_weekly_sales(self, start_date, end_date, branch=None):
        """
        Calculates daily sales totals for a specified week and branch.
        Returns a DataFrame with 'DayOfWeek' and 'Total' columns.
        """
        if self.sales_data.empty:
            # Return a DataFrame with all days of the week and 0 sales if no data
            return pd.DataFrame({'DayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 'Total': [0]*7})

        df = self.sales_data[(self.sales_data['Date'] >= start_date) & (self.sales_data['Date'] <= end_date)].copy()
        if branch and branch != "All Branches":
            df = df[df['Branch'] == branch]

        if df.empty:
            # Return a DataFrame with all days of the week and 0 sales if no data
            return pd.DataFrame({'DayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 'Total': [0]*7})

        df['DayOfWeek'] = df['Date'].dt.day_name()
        # Group by day of week and reindex to ensure all days are present, even if no sales
        return df.groupby('DayOfWeek')['Total'].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], fill_value=0).reset_index()

    def get_product_preferences(self, date_range=None, category=None, branch=None):
        """
        Analyzes product popularity based on units sold and revenue within filters.
        Returns a DataFrame with 'Product', 'UnitsSold', and 'Revenue' columns.
        """
        df = self.sales_data.copy()
        if df.empty:
            return pd.DataFrame(columns=['Product', 'UnitsSold', 'Revenue'])

        if date_range:
            start, end = date_range
            df = df[(df['Date'] >= start) & (df['Date'] <= end)]
        if branch and branch != "All Branches":
            df = df[df['Branch'] == branch]
        # Category filtering would require a 'Category' column in your data, which is not in dummy data
        # if category:
        #     df = df[df['Category'] == category]

        if df.empty:
            return pd.DataFrame(columns=['Product', 'UnitsSold', 'Revenue'])

        return df.groupby('Product').agg(
            UnitsSold=('Quantity', 'sum'),
            Revenue=('Total', 'sum')
        ).sort_values(by='UnitsSold', ascending=False).reset_index()

    def get_sales_distribution(self, date_range=None, branch=None, category=None):
        """
        Returns a Series of total sales amounts per transaction for distribution analysis.
        """
        df = self.sales_data.copy()
        if df.empty:
            return pd.Series(dtype='float64') # Return empty Series if no data

        if date_range:
            start, end = date_range
            df = df[(df['Date'] >= start) & (df['Date'] <= end)]
        if branch and branch != "All Branches":
            df = df[df['Branch'] == branch]
        # Category filtering would require a 'Category' column in your data
        return df['Total'] # Assuming each row is a transaction or can be treated as such for distribution


# --- Base Page Class (Inheritance & Association) ---
# O (Open/Closed Principle): New analysis pages can be added by inheriting from BasePage
# without modifying the core DashboardPage.
# D (Dependency Inversion Principle): DataManager is injected into BasePage (and its subclasses).
class BasePage(tk.Toplevel):
    """
    Base class for all analysis and utility pages.
    Handles common window properties and ensures return to dashboard.
    """
    def __init__(self, master, data_manager, title="Application Page"):
        super().__init__(master)
        self.master = master # Association: BasePage has a reference to the MainApp (master)
        self.data_manager = data_manager # Association: BasePage has a reference to the DataManager
        self.title(title)
        self.geometry("900x700") # Increased size for better chart/table visibility
        self.protocol("WM_DELETE_WINDOW", self.on_close) # Handle window close button
        self.transient(master) # Make this window appear on top of the master
        self.grab_set() # Make modal (optional, but good for analysis pages)

        # Configure columns and rows to expand
        self.grid_rowconfigure(0, weight=0) # For controls
        self.grid_rowconfigure(1, weight=1) # For chart
        self.grid_rowconfigure(2, weight=1) # For table
        self.grid_columnconfigure(0, weight=1)

    def on_close(self):
        """Handles closing the page, returning focus to the dashboard."""
        self.destroy() # Close this window
        self.master.deiconify() # Show the main dashboard again
        self.master.lift() # Bring main window to front


# --- 1. Login Page ---
class LoginPage(tk.Toplevel):
    """
    Handles user authentication.
    S (Single Responsibility Principle): Only concerned with login logic.
    """
    def __init__(self, master, data_manager):
        super().__init__(master)
        self.master = master
        self.data_manager = data_manager # DataManager is injected but not directly used by Login
        self.title("Login")
        self.geometry("400x280")
        self.grab_set() # Make this window modal
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.resizable(False, False)

        # Frame for better organization
        login_frame = tk.Frame(self, padx=20, pady=20)
        login_frame.pack(expand=True)

        tk.Label(login_frame, text="Sampath Food City", font=("Arial", 14, "bold")).pack(pady=15)

        tk.Label(login_frame, text="Username:", font=("Arial", 10)).pack(anchor="w", pady=(10, 2))
        self.username_entry = tk.Entry(login_frame, width=30, font=("Arial", 10))
        self.username_entry.pack(pady=2)
        self.username_entry.focus_set() # Set focus to username field

        tk.Label(login_frame, text="Password:", font=("Arial", 10)).pack(anchor="w", pady=(10, 2))
        self.password_entry = tk.Entry(login_frame, show="*", width=30, font=("Arial", 10))
        self.password_entry.pack(pady=2)

        self.login_button = tk.Button(login_frame, text="Login", command=self.attempt_login, font=("Arial", 10, "bold"), bg="#4CAF50", fg="white", relief="raised")
        self.login_button.pack(pady=15)

        self.error_label = tk.Label(login_frame, text="", fg="red", font=("Arial", 9))
        self.error_label.pack(pady=5)

        # Hardcoded credentials for demonstration
        # Clean Coding: In a real application, these would be securely stored (e.g., hashed in a database)
        self.valid_users = {"admin": "admin123", "analyst": "analyst123"}

        # Bind <Return> key to login attempt
        self.username_entry.bind("<Return>", lambda event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        """Checks entered credentials against hardcoded valid users."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username in self.valid_users and self.valid_users[username] == password:
            messagebox.showinfo("Login Success", f"Welcome, {username}!", parent=self)
            self.master.show_dashboard(username) # Pass user role/info to dashboard
            self.destroy()
        else:
            self.error_label.config(text="Invalid credentials")
            self.password_entry.delete(0, tk.END) # Clear password field on failure

    def on_close(self):
        """If user closes login window, exit the entire application."""
        self.master.destroy()

# --- 2. Dashboard (Main Menu Page) ---
class DashboardPage(tk.Frame):
    """
    Central navigation hub for the application.
    Composition: MainApp has a DashboardPage.
    """
    def __init__(self, master, data_manager, user_role="Analyst"):
        super().__init__(master)
        self.master = master
        self.data_manager = data_manager
        self.user_role = user_role
        self.pack(fill="both", expand=True)

        # Configure grid for responsive layout
        self.grid_rowconfigure(0, weight=0) # Title
        self.grid_rowconfigure(1, weight=0) # Welcome message
        self.grid_rowconfigure(2, weight=1) # Button frame
        self.grid_rowconfigure(3, weight=0) # Summary
        self.grid_rowconfigure(4, weight=0) # Logout button
        self.grid_columnconfigure(0, weight=1)

        tk.Label(self, text="Sales Analysis Dashboard", font=("Arial", 20, "bold")).grid(row=0, column=0, pady=20)
        tk.Label(self, text=f"Welcome, {user_role.capitalize()}!", font=("Arial", 14)).grid(row=1, column=0, pady=10)

        button_frame = tk.Frame(self)
        button_frame.grid(row=2, column=0, pady=20, sticky="nsew")
        button_frame.grid_columnconfigure(0, weight=1) # Center buttons horizontally

        # Define buttons and their commands
        self.buttons_config = [
            ("Monthly Sales", self.open_monthly_sales),
            ("Price Analysis", self.open_price_analysis),
            ("Weekly Sales", self.open_weekly_sales),
            ("Product Preference", self.open_product_preference),
            ("Sales Distribution", self.open_sales_distribution),
            ("Data Import", self.open_data_import),
            ("Data Export", self.open_data_export),
        ]

        # Optional: Conditional access for admin
        if self.user_role == "admin":
            self.buttons_config.append(("Settings", self.open_settings))

        # Create buttons
        self.action_buttons = []
        for i, (text, command) in enumerate(self.buttons_config):
            btn = tk.Button(button_frame, text=text, command=command, width=25, height=2,
                      font=("Arial", 11), bg="#ADD8E6", fg="black", relief="ridge")
            btn.grid(row=i, column=0, pady=5)
            self.action_buttons.append(btn)


        self.summary_label = tk.Label(self, text="", font=("Arial", 11), fg="blue")
        self.summary_label.grid(row=3, column=0, pady=15)
        self.update_summary() # Optional: display summary

        tk.Button(self, text="Logout / Exit", command=self.logout_exit, font=("Arial", 12, "bold"), bg="#FF6347", fg="white", relief="raised").grid(row=4, column=0, pady=20)

        self.update_button_states() # Initial state update

    def update_button_states(self):
        """Disables/enables analysis buttons based on data availability."""
        has_data = not self.data_manager.sales_data.empty
        for text, _ in self.buttons_config:
            if text in ["Data Import", "Logout / Exit", "Settings"]: # These are always enabled
                continue
            # Find the button and set its state
            for btn in self.action_buttons:
                if btn.cget("text") == text:
                    btn.config(state=tk.NORMAL if has_data else tk.DISABLED)
                    break

    def update_summary(self):
        """Updates the dashboard summary with current data insights."""
        if not self.data_manager.sales_data.empty:
            total_sales = self.data_manager.sales_data['Total'].sum()
            # Get top product by total sales for a more meaningful summary
            top_product_df = self.data_manager.sales_data.groupby('Product')['Total'].sum().nlargest(1)
            if not top_product_df.empty:
                top_product_name = top_product_df.index[0]
                summary_text = f"Total Sales (All Time): Rs. {total_sales:,.2f} | Top Product: {top_product_name}"
            else:
                summary_text = "No sales data available for summary." # Should not happen if data is not empty
        else:
            summary_text = "No sales data available. Please import data using 'Data Import'."

        self.summary_label.config(text=summary_text)

    # --- Dashboard Navigation Methods ---
    # These methods hide the dashboard and open the respective analysis pages.
    def open_monthly_sales(self):
        MonthlySalesPage(self.master, self.data_manager)

    def open_price_analysis(self):
        PriceAnalysisPage(self.master, self.data_manager)

    def open_weekly_sales(self):
        WeeklySalesPage(self.master, self.data_manager)

    def open_product_preference(self):
        ProductPreferencePage(self.master, self.data_manager)

    def open_sales_distribution(self):
        SalesDistributionPage(self.master, self.data_manager)

    def open_data_import(self):
        DataImportPage(self.master, self.data_manager)

    def open_data_export(self):
        DataExportPage(self.master, self.data_manager)

    def open_settings(self):
        SettingsPage(self.master, self.data_manager)

    def logout_exit(self):
        """Initiates the exit confirmation process."""
        self.master.withdraw() # Hide main window
        ExitConfirmationPage(self.master)

# --- 3. Monthly Sales Analysis Page ---
class MonthlySalesPage(BasePage):
    """
    Displays monthly sales performance per branch, with table and bar chart.
    L (Liskov Substitution Principle): Can be treated as a BasePage.
    """
    def __init__(self, master, data_manager):
        super().__init__(master, data_manager, "Monthly Sales Analysis")

        # Controls Frame
        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=0, pady=10, sticky="ew")
        control_frame.grid_columnconfigure((0,1,2,3,4,5,6,7), weight=1) # Distribute space evenly

        tk.Label(control_frame, text="Branch:").grid(row=0, column=0, padx=5)
        self.branch_var = tk.StringVar(self)
        self.branch_dropdown = tk.OptionMenu(control_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=1, padx=5)

        tk.Label(control_frame, text="Year:").grid(row=0, column=2, padx=5)
        self.year_var = tk.StringVar(self)
        self.year_dropdown = tk.OptionMenu(control_frame, self.year_var, "Loading...")
        self.year_dropdown.grid(row=0, column=3, padx=5)

        tk.Label(control_frame, text="Month:").grid(row=0, column=4, padx=5)
        self.month_var = tk.StringVar(self)
        self.months = [
            "All Months", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        self.month_dropdown = tk.OptionMenu(control_frame, self.month_var, *self.months)
        self.month_var.set("All Months")
        self.month_dropdown.grid(row=0, column=5, padx=5)

        tk.Button(control_frame, text="Generate Report", command=self.generate_report).grid(row=0, column=6, padx=10)
        tk.Button(control_frame, text="Export Report (PDF)", command=self.export_report_pdf).grid(row=0, column=7, padx=10)

        # Chart Area
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Table Area (using Treeview for better tabular display)
        self.tree_frame = tk.Frame(self)
        self.tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Product", "Quantity", "UnitPrice", "Total"), show="headings")
        self.tree.heading("Product", text="Product")
        self.tree.heading("Quantity", text="Quantity")
        self.tree.heading("UnitPrice", text="Unit Price")
        self.tree.heading("Total", text="Total Sales")

        # Adjust column widths (example values)
        self.tree.column("Product", width=200, anchor="w")
        self.tree.column("Quantity", width=100, anchor="center")
        self.tree.column("UnitPrice", width=120, anchor="e")
        self.tree.column("Total", width=120, anchor="e")

        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")

        self.last_report_df = pd.DataFrame() # To store data for export
        self.refresh_dropdowns() # Initial population of dropdowns

    def refresh_dropdowns(self):
        """Populates or updates the branch and year dropdowns."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        years = sorted(self.data_manager.get_years(), reverse=True) # Latest year first

        # Update Branch Dropdown
        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch, command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)

        # Update Year Dropdown
        self.year_dropdown['menu'].delete(0, 'end')
        for year in years:
            self.year_dropdown['menu'].add_command(label=str(year), command=tk._setit(self.year_var, str(year)))
        if years:
            self.year_var.set(str(years[0]))
        else:
            self.year_var.set(str(datetime.now().year)) # Default to current year
            self.year_dropdown.config(state=tk.DISABLED)

        # Enable dropdowns if data exists, otherwise disable
        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)
        self.year_dropdown.config(state=state)
        self.month_dropdown.config(state=state)


    def generate_report(self):
        """Generates and displays the monthly sales report based on selected filters."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to generate reports.", parent=self)
            self.ax.clear()
            self.canvas.draw()
            self._clear_treeview()
            return

        selected_branch = self.branch_var.get()
        selected_year_str = self.year_var.get()
        selected_month_name = self.month_var.get()

        selected_year = int(selected_year_str) if selected_year_str and selected_year_str != "All Years" else None
        selected_month = None
        if selected_month_name != "All Months":
            selected_month = datetime.strptime(selected_month_name, "%B").month

        report_data = self.data_manager.get_monthly_sales(selected_branch, selected_year, selected_month)
        self.last_report_df = report_data # Store for export

        if report_data.empty:
            messagebox.showinfo("No Data", "No sales data found for the selected criteria.", parent=self)
            self.ax.clear()
            self.canvas.draw()
            self._clear_treeview()
            return

        # Update Table (Treeview)
        self._clear_treeview()
        for index, row in report_data.iterrows():
            self.tree.insert("", "end", values=(
                row['Product'],
                f"{row['Quantity']:.0f}",
                f"Rs. {row['UnitPrice']:.2f}",
                f"Rs. {row['Total']:.2f}"
            ))

        # Update Chart
        self.ax.clear()
        self.ax.bar(report_data['Product'], report_data['Total'], color='skyblue')
        self.ax.set_title(f'Total Sales per Product ({selected_month_name} {selected_year_str})')
        self.ax.set_xlabel('Product')
        self.ax.set_ylabel('Total Sales (Rs.)')
        self.fig.autofmt_xdate(rotation=45)
        plt.tight_layout()
        self.canvas.draw()

    def _clear_treeview(self):
        """Clears all existing items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def export_report_pdf(self):
        """Exports the current report as a PDF."""
        if self.last_report_df.empty:
            messagebox.showwarning("No Data", "Generate a report first before exporting.", parent=self)
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save Monthly Sales Report"
            )
            if file_path:
                # Save the matplotlib figure as PDF
                self.fig.savefig(file_path, bbox_inches='tight')
                messagebox.showinfo("Export Success", f"Report saved to {file_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {e}", parent=self)

# --- 4. Price Analysis Page ---
class PriceAnalysisPage(BasePage):
    """
    Analyzes price fluctuations of individual products with a line graph and historical table.
    """
    def __init__(self, master, data_manager):
        super().__init__(master, data_manager, "Price Analysis")

        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=0, pady=10, sticky="ew")
        control_frame.grid_columnconfigure((0,1,2), weight=1)

        tk.Label(control_frame, text="Select Product:").grid(row=0, column=0, padx=5)
        self.product_var = tk.StringVar(self)
        self.product_dropdown = tk.OptionMenu(control_frame, self.product_var, "Loading...")
        self.product_dropdown.grid(row=0, column=1, padx=5)

        tk.Button(control_frame, text="Analyze Price", command=self.analyze_price).grid(row=0, column=2, padx=10)

        # Chart Area
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Stats Labels
        self.stats_frame = tk.Frame(self)
        self.stats_frame.grid(row=2, column=0, pady=10, sticky="ew")
        self.stats_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.avg_price_label = tk.Label(self.stats_frame, text="Average Price: N/A")
        self.avg_price_label.grid(row=0, column=0, padx=10)
        self.max_price_label = tk.Label(self.stats_frame, text="Max Price: N/A")
        self.max_price_label.grid(row=0, column=1, padx=10)
        self.min_price_label = tk.Label(self.stats_frame, text="Min Price: N/A")
        self.min_price_label.grid(row=0, column=2, padx=10)
        self.current_price_label = tk.Label(self.stats_frame, text="Current Price: N/A")
        self.current_price_label.grid(row=0, column=3, padx=10)

        # Table Area (Treeview)
        self.tree_frame = tk.Frame(self)
        self.tree_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Date", "Price"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Price", text="Price (Rs.)")
        self.tree.column("Date", width=150, anchor="center")
        self.tree.column("Price", width=150, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")
        self.refresh_dropdowns() # Initial population of dropdowns

    def refresh_dropdowns(self):
        """Populates or updates the product dropdown."""
        products = self.data_manager.get_products()
        self.product_dropdown['menu'].delete(0, 'end')
        if products:
            for product in products:
                self.product_dropdown['menu'].add_command(label=product, command=tk._setit(self.product_var, product))
            self.product_var.set(products[0]) # Set default if products exist
            self.product_dropdown.config(state=tk.NORMAL)
        else:
            self.product_var.set("No Products Available")
            self.product_dropdown.config(state=tk.DISABLED)

    def analyze_price(self):
        """Fetches and displays price history for the selected product."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to analyze prices.", parent=self)
            self.ax.clear()
            self.canvas.draw()
            self.update_stats(None, None, None, None)
            self._clear_treeview()
            return

        selected_product = self.product_var.get()
        if not selected_product or selected_product == "No Products Available":
            messagebox.showwarning("Selection Error", "Please select a product.", parent=self)
            return

        price_history_df = self.data_manager.get_product_price_history(selected_product)

        if price_history_df.empty:
            messagebox.showinfo("No Data", f"No price history found for {selected_product}.", parent=self)
            self.ax.clear()
            self.canvas.draw()
            self.update_stats(None, None, None, None)
            self._clear_treeview()
            return

        # Update Chart
        self.ax.clear()
        self.ax.plot(price_history_df['Date'], price_history_df['UnitPrice'], marker='o', linestyle='-')
        self.ax.set_title(f'Price Fluctuation for {selected_product}')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Unit Price (Rs.)')
        self.fig.autofmt_xdate()
        plt.tight_layout()
        self.canvas.draw()

        # Update Stats
        avg_price = price_history_df['UnitPrice'].mean()
        max_price = price_history_df['UnitPrice'].max()
        min_price = price_history_df['UnitPrice'].min()
        current_price = price_history_df.iloc[-1]['UnitPrice'] # Last recorded price
        self.update_stats(avg_price, max_price, min_price, current_price)

        # Update Table
        self._clear_treeview()
        for index, row in price_history_df.iterrows():
            self.tree.insert("", "end", values=(row['Date'].strftime('%Y-%m-%d'), f"Rs. {row['UnitPrice']:.2f}"))

    def update_stats(self, avg, max_val, min_val, current):
        """Updates the statistical labels for price analysis."""
        self.avg_price_label.config(text=f"Average Price: Rs. {avg:.2f}" if avg is not None else "Average Price: N/A")
        self.max_price_label.config(text=f"Max Price: Rs. {max_val:.2f}" if max_val is not None else "Max Price: N/A")
        self.min_price_label.config(text=f"Min Price: Rs. {min_val:.2f}" if min_val is not None else "Min Price: N/A")
        self.current_price_label.config(text=f"Current Price: Rs. {current:.2f}" if current is not None else "Current Price: N/A")

    def _clear_treeview(self):
        """Clears all existing items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

# --- 5. Weekly Sales Summary Page ---
class WeeklySalesPage(BasePage):
    """
    Provides an overview of sales trends during a specific week.
    """
    def __init__(self, master, data_manager):
        super().__init__(master, data_manager, "Weekly Sales Summary")

        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=0, pady=10, sticky="ew")
        control_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)

        tk.Label(control_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5)
        self.start_date_entry = tk.Entry(control_frame)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5)
        self.end_date_entry = tk.Entry(control_frame)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="Branch:").grid(row=0, column=4, padx=5)
        self.branch_var = tk.StringVar(self)
        self.branch_dropdown = tk.OptionMenu(control_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=5, padx=5)

        tk.Button(control_frame, text="Generate Summary", command=self.generate_summary).grid(row=1, column=0, columnspan=6, pady=10)

        # Chart Area
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=10) # Re-grid after button row

        # Summary Labels
        self.summary_frame = tk.Frame(self)
        self.summary_frame.grid(row=2, column=0, pady=10, sticky="ew")
        self.summary_frame.grid_columnconfigure((0,1), weight=1)

        self.total_revenue_label = tk.Label(self.summary_frame, text="Total Revenue: N/A")
        self.total_revenue_label.grid(row=0, column=0, padx=10)
        self.avg_daily_sales_label = tk.Label(self.summary_frame, text="Average Daily Sales: N/A")
        self.avg_daily_sales_label.grid(row=0, column=1, padx=10)

        # Table Area (Treeview)
        self.tree_frame = tk.Frame(self)
        self.tree_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("DayOfWeek", "TotalSales"), show="headings")
        self.tree.heading("DayOfWeek", text="Day of Week")
        self.tree.heading("TotalSales", text="Total Sales (Rs.)")
        self.tree.column("DayOfWeek", width=150, anchor="center")
        self.tree.column("TotalSales", width=150, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")
        self.refresh_dropdowns() # Initial population of dropdowns

    def refresh_dropdowns(self):
        """Populates or updates the branch dropdown."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch, command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)

        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)

    def generate_summary(self):
        """Generates and displays the weekly sales summary."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to generate weekly summaries.", parent=self)
            self.ax.clear()
            self.canvas.draw()
            self.update_summary_labels(None, None)
            self._clear_treeview()
            return

        try:
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.", parent=self)
                return

            selected_branch = self.branch_var.get()

            weekly_sales_df = self.data_manager.get_weekly_sales(start_date, end_date, selected_branch)

            if weekly_sales_df.empty or weekly_sales_df['Total'].sum() == 0:
                messagebox.showinfo("No Data", "No sales data found for the selected week and branch.", parent=self)
                self.ax.clear()
                self.canvas.draw()
                self.update_summary_labels(None, None)
                self._clear_treeview()
                return

            # Update Chart
            self.ax.clear()
            self.ax.bar(weekly_sales_df['DayOfWeek'], weekly_sales_df['Total'], color='lightgreen')
            self.ax.set_title(f'Weekly Sales Summary ({start_date_str} to {end_date_str})')
            self.ax.set_xlabel('Day of Week')
            self.ax.set_ylabel('Total Sales (Rs.)')
            plt.tight_layout()
            self.canvas.draw()

            # Update Summary
            total_revenue = weekly_sales_df['Total'].sum()
            num_days_with_sales = (weekly_sales_df['Total'] > 0).sum()
            avg_daily_sales = total_revenue / num_days_with_sales if num_days_with_sales > 0 else 0
            self.update_summary_labels(total_revenue, avg_daily_sales)

            # Update Table
            self._clear_treeview()
            for index, row in weekly_sales_df.iterrows():
                self.tree.insert("", "end", values=(row['DayOfWeek'], f"Rs. {row['Total']:.2f}"))

        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-%d.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}", parent=self)

    def update_summary_labels(self, total_revenue, avg_daily_sales):
        """Updates the summary labels for weekly sales."""
        self.total_revenue_label.config(text=f"Total Revenue: Rs. {total_revenue:,.2f}" if total_revenue is not None else "Total Revenue: N/A")
        self.avg_daily_sales_label.config(text=f"Average Daily Sales: Rs. {avg_daily_sales:,.2f}" if avg_daily_sales is not None else "Average Daily Sales: N/A")

    def _clear_treeview(self):
        """Clears all existing items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

# --- 6. Product Preference Analysis Page ---
class ProductPreferencePage(BasePage):
    """
    Highlights most popular products based on units sold and revenue.
    """
    def __init__(self, master, data_manager):
        super().__init__(master, data_manager, "Product Preference Analysis")

        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=0, pady=10, sticky="ew")
        control_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)

        tk.Label(control_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5)
        self.start_date_entry = tk.Entry(control_frame)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5)
        self.end_date_entry = tk.Entry(control_frame)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="Branch:").grid(row=0, column=4, padx=5)
        self.branch_var = tk.StringVar(self)
        self.branch_dropdown = tk.OptionMenu(control_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=5, padx=5)

        tk.Button(control_frame, text="Analyze Preferences", command=self.analyze_preferences).grid(row=1, column=0, columnspan=3, pady=10)
        tk.Button(control_frame, text="Export Report", command=self.export_report).grid(row=1, column=3, columnspan=3, pady=10)

        # Chart Area
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # Table Area (Treeview)
        self.tree_frame = tk.Frame(self)
        self.tree_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Product", "UnitsSold", "Revenue"), show="headings")
        self.tree.heading("Product", text="Product")
        self.tree.heading("UnitsSold", text="Units Sold")
        self.tree.heading("Revenue", text="Revenue (Rs.)")
        self.tree.column("Product", width=200, anchor="w")
        self.tree.column("UnitsSold", width=100, anchor="center")
        self.tree.column("Revenue", width=120, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")

        self.last_report_data = None # To hold data for export
        self.refresh_dropdowns() # Initial population of dropdowns

    def refresh_dropdowns(self):
        """Populates or updates the branch dropdown."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch, command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)

        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)

    def analyze_preferences(self):
        """Analyzes and displays product preferences."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to analyze product preferences.", parent=self)
            self.ax.clear()
            self.canvas.draw()
            self._clear_treeview()
            self.last_report_data = None
            return

        try:
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.", parent=self)
                return

            selected_branch = self.branch_var.get()
            date_range = (start_date, end_date)

            preference_df = self.data_manager.get_product_preferences(date_range, branch=selected_branch)

            if preference_df.empty:
                messagebox.showinfo("No Data", "No product preference data found for the selected criteria.", parent=self)
                self.ax.clear()
                self.canvas.draw()
                self._clear_treeview()
                self.last_report_data = None
                return

            self.last_report_data = preference_df.copy()

            # Update Table
            self._clear_treeview()
            for index, row in preference_df.iterrows():
                self.tree.insert("", "end", values=(
                    row['Product'],
                    f"{row['UnitsSold']:.0f}",
                    f"Rs. {row['Revenue']:.2f}"
                ))

            # Update Chart (Top 10 Products by Units Sold)
            top_10 = preference_df.head(10)
            self.ax.clear()
            if not top_10.empty:
                self.ax.pie(top_10['UnitsSold'], labels=top_10['Product'], autopct='%1.1f%%', startangle=90, pctdistance=0.85)
                self.ax.set_title('Top 10 Product Preferences by Units Sold')
                self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            else:
                self.ax.text(0.5, 0.5, "No data for chart", horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
            plt.tight_layout()
            self.canvas.draw()

        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-%d.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}", parent=self)

    def _clear_treeview(self):
        """Clears all existing items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def export_report(self):
        """Exports the product preference report to CSV/Excel."""
        if self.last_report_data is None or self.last_report_data.empty:
            messagebox.showwarning("No Data", "Generate a report first before exporting.", parent=self)
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
            title="Save Product Preference Report"
        )
        if file_path:
            try:
                if file_path.endswith(".csv"):
                    self.last_report_data.to_csv(file_path, index=False)
                elif file_path.endswith(".xlsx"):
                    self.last_report_data.to_excel(file_path, index=False)
                messagebox.showinfo("Export Success", f"Report saved to {file_path}", parent=self)
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export report: {e}", parent=self)

# --- 7. Sales Distribution Analysis Page ---
class SalesDistributionPage(BasePage):
    """
    Visualizes how total sales amounts are distributed across transactions using a histogram.
    """
    def __init__(self, master, data_manager):
        super().__init__(master, data_manager, "Sales Distribution Analysis")

        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=0, pady=10, sticky="ew")
        control_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)

        tk.Label(control_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5)
        self.start_date_entry = tk.Entry(control_frame)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5)
        self.end_date_entry = tk.Entry(control_frame)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="Branch:").grid(row=0, column=4, padx=5)
        self.branch_var = tk.StringVar(self)
        self.branch_dropdown = tk.OptionMenu(control_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=5, padx=5)

        tk.Button(control_frame, text="Analyze Distribution", command=self.analyze_distribution).grid(row=1, column=0, columnspan=6, pady=10)

        # Chart Area
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # Stats Labels
        self.stats_frame = tk.Frame(self)
        self.stats_frame.grid(row=3, column=0, pady=10, sticky="ew")
        self.stats_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)

        self.mean_label = tk.Label(self.stats_frame, text="Mean: N/A")
        self.mean_label.grid(row=0, column=0, padx=5)
        self.median_label = tk.Label(self.stats_frame, text="Median: N/A")
        self.median_label.grid(row=0, column=1, padx=5)
        self.mode_label = tk.Label(self.stats_frame, text="Mode: N/A")
        self.mode_label.grid(row=0, column=2, padx=5)
        self.min_label = tk.Label(self.stats_frame, text="Min: N/A")
        self.min_label.grid(row=0, column=3, padx=5)
        self.max_label = tk.Label(self.stats_frame, text="Max: N/A")
        self.max_label.grid(row=0, column=4, padx=5)
        self.std_dev_label = tk.Label(self.stats_frame, text="Std Dev: N/A")
        self.std_dev_label.grid(row=0, column=5, padx=5)
        self.refresh_dropdowns() # Initial population of dropdowns


    def refresh_dropdowns(self):
        """Populates or updates the branch dropdown."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch, command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)

        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)

    def analyze_distribution(self):
        """Analyzes and displays sales amount distribution."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to analyze sales distribution.", parent=self)
            self.ax.clear()
            self.canvas.draw()
            self.update_stats(None, None, None, None, None, None)
            return

        try:
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.", parent=self)
                return

            selected_branch = self.branch_var.get()
            date_range = (start_date, end_date)

            sales_amounts = self.data_manager.get_sales_distribution(date_range, branch=selected_branch)

            if sales_amounts.empty:
                messagebox.showinfo("No Data", "No sales distribution data found for the selected criteria.", parent=self)
                self.ax.clear()
                self.canvas.draw()
                self.update_stats(None, None, None, None, None, None)
                return

            # Update Chart (Histogram)
            self.ax.clear()
            self.ax.hist(sales_amounts, bins=30, edgecolor='black', alpha=0.7)
            self.ax.set_title('Sales Amount Distribution')
            self.ax.set_xlabel('Sales Amount (Rs.)')
            self.ax.set_ylabel('Frequency')
            plt.tight_layout()
            self.canvas.draw()

            # Update Stats
            mean_val = sales_amounts.mean()
            median_val = sales_amounts.median()
            # Mode can return multiple values, take the first if available
            mode_val = sales_amounts.mode()[0] if not sales_amounts.mode().empty else np.nan
            min_val = sales_amounts.min()
            max_val = sales_amounts.max()
            std_dev_val = sales_amounts.std()
            self.update_stats(mean_val, median_val, mode_val, min_val, max_val, std_dev_val)

        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-%d.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}", parent=self)

    def update_stats(self, mean, median, mode, min_val, max_val, std_dev):
        """Updates the statistical labels for sales distribution."""
        self.mean_label.config(text=f"Mean: Rs. {mean:,.2f}" if mean is not None else "Mean: N/A")
        self.median_label.config(text=f"Median: Rs. {median:,.2f}" if median is not None else "Median: N/A")
        # Handle mode display gracefully if it's NaN
        self.mode_label.config(text=f"Mode: Rs. {mode:,.2f}" if pd.notna(mode) else "Mode: N/A")
        self.min_label.config(text=f"Min: Rs. {min_val:,.2f}" if min_val is not None else "Min: N/A")
        self.max_label.config(text=f"Max: Rs. {max_val:,.2f}" if max_val is not None else "Max: N/A")
        self.std_dev_label.config(text=f"Std Dev: Rs. {std_dev:,.2f}" if std_dev is not None else "Std Dev: N/A")


# --- 8. Data Import Page ---
class DataImportPage(BasePage):
    """
    Allows users to import new sales data from CSV/Excel files.
    """
    def __init__(self, master, data_manager):
        super().__init__(master, data_manager, "Data Import")

        self.file_path = ""
        self.preview_df = None

        tk.Label(self, text="Upload New Sales Data", font=("Arial", 16, "bold")).pack(pady=20)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Choose File", command=self.choose_file, font=("Arial", 10)).pack(side="left", padx=10)
        self.file_label = tk.Label(button_frame, text="No file selected", font=("Arial", 10))
        self.file_label.pack(side="left", padx=10)

        tk.Button(self, text="Preview Data", command=self.preview_data, font=("Arial", 10)).pack(pady=10)

        self.preview_text = tk.Text(self, wrap="word", height=15, width=80, font=("Courier New", 9))
        self.preview_text.pack(pady=10, fill="both", expand=True, padx=10)

        self.save_button = tk.Button(self, text="Save to System", command=self.save_data, state=tk.DISABLED, font=("Arial", 11, "bold"), bg="#28a745", fg="white")
        self.save_button.pack(pady=20)

        self.status_label = tk.Label(self, text="", fg="green", font=("Arial", 10))
        self.status_label.pack(pady=10)

    def choose_file(self):
        """Opens a file dialog for selecting CSV/Excel files."""
        self.file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if self.file_path:
            self.file_label.config(text=os.path.basename(self.file_path))
            self.save_button.config(state=tk.DISABLED) # Disable until preview is successful
            self.preview_text.delete(1.0, tk.END) # Clear previous preview
            self.status_label.config(text="")
        else:
            self.file_label.config(text="No file selected")

    def preview_data(self):
        """Reads and displays a preview of the selected data file."""
        if not self.file_path:
            messagebox.showwarning("No File", "Please choose a file first.", parent=self)
            return

        try:
            if self.file_path.endswith(".csv"):
                df = pd.read_csv(self.file_path)
            elif self.file_path.endswith(".xlsx"):
                df = pd.read_excel(self.file_path)
            else:
                messagebox.showerror("Invalid File", "Unsupported file type. Please select CSV or Excel.", parent=self)
                return

            self.preview_df = df # Store for saving

            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "Preview of the first 5 rows:\n\n")
            self.preview_text.insert(tk.END, df.head().to_string())
            self.preview_text.insert(tk.END, f"\n\nTotal records in preview: {len(df)}")

            # Check for required columns and enable save button if all are present
            required_cols = ['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total']
            if all(col in df.columns for col in required_cols):
                self.save_button.config(state=tk.NORMAL) # Enable save button
                self.status_label.config(text="File ready for import. Review data before saving.", fg="blue")
            else:
                missing_cols = [col for col in required_cols if col not in df.columns]
                self.save_button.config(state=tk.DISABLED)
                self.status_label.config(text=f"Missing required columns: {', '.join(missing_cols)}", fg="red")

        except Exception as e:
            messagebox.showerror("Preview Error", f"Error reading file: {e}", parent=self)
            self.preview_df = None
            self.save_button.config(state=tk.DISABLED)
            self.status_label.config(text="Error during preview.", fg="red")


    def save_data(self):
        """Saves the previewed data to the system via DataManager."""
        if self.preview_df is None or self.preview_df.empty:
            messagebox.showwarning("No Data", "No data to save. Please preview a file first.", parent=self)
            return

        if self.data_manager.add_data(self.preview_df):
            self.status_label.config(text=f"{len(self.preview_df)} records successfully uploaded and saved!", fg="green")
            self.save_button.config(state=tk.DISABLED) # Disable after saving
            self.file_label.config(text="No file selected")
            self.preview_text.delete(1.0, tk.END)
            messagebox.showinfo("Import Success", "Data imported and saved successfully!", parent=self)
            self.master.dashboard_page.update_summary() # Update dashboard summary
            self.master.update_all_page_dropdowns() # Update dropdowns in all open pages
        else:
            self.status_label.config(text="Data upload failed. Check console for errors.", fg="red")


# --- 9. Data Export Page ---
class DataExportPage(BasePage):
    """
    Allows users to export processed/filtered data to various formats.
    """
    def __init__(self, master, data_manager):
        super().__init__(master, data_manager, "Data Export")

        tk.Label(self, text="Export Sales Data", font=("Arial", 16, "bold")).pack(pady=20)

        filter_frame = tk.Frame(self)
        filter_frame.pack(pady=10)
        filter_frame.grid_columnconfigure((0,1,2,3,4,5,6,7), weight=1) # Even distribution

        tk.Label(filter_frame, text="Branch:").grid(row=0, column=0, padx=5)
        self.branch_var = tk.StringVar(self)
        self.branch_dropdown = tk.OptionMenu(filter_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=1, padx=5)

        tk.Label(filter_frame, text="Product:").grid(row=0, column=2, padx=5)
        self.product_var = tk.StringVar(self)
        self.product_dropdown = tk.OptionMenu(filter_frame, self.product_var, "Loading...")
        self.product_dropdown.grid(row=0, column=3, padx=5)

        tk.Label(filter_frame, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5)
        self.start_date_entry = tk.Entry(filter_frame)
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5)
        self.start_date_entry.insert(0, "2020-01-01") # Default start date

        tk.Label(filter_frame, text="End Date (YYYY-MM-DD):").grid(row=1, column=2, padx=5, pady=5)
        self.end_date_entry = tk.Entry(filter_frame)
        self.end_date_entry.grid(row=1, column=3, padx=5, pady=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d')) # Default end date

        export_button_frame = tk.Frame(self)
        export_button_frame.pack(pady=20)

        tk.Button(export_button_frame, text="Export as CSV", command=lambda: self.export_data("csv"), font=("Arial", 10), bg="#007bff", fg="white").pack(side="left", padx=10)
        tk.Button(export_button_frame, text="Export as Excel", command=lambda: self.export_data("xlsx"), font=("Arial", 10), bg="#28a745", fg="white").pack(side="left", padx=10)
        tk.Button(export_button_frame, text="Export as PDF (Summary)", command=lambda: self.export_data("pdf"), font=("Arial", 10), bg="#dc3545", fg="white").pack(side="left", padx=10)

        self.status_label = tk.Label(self, text="", fg="blue", font=("Arial", 10))
        self.status_label.pack(pady=10)
        self.refresh_dropdowns() # Initial population of dropdowns

    def refresh_dropdowns(self):
        """Populates or updates the branch and product dropdowns."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        products = ["All Products"] + self.data_manager.get_products()

        # Update Branch Dropdown
        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch, command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)

        # Update Product Dropdown
        self.product_dropdown['menu'].delete(0, 'end')
        for product in products:
            self.product_dropdown['menu'].add_command(label=product, command=tk._setit(self.product_var, product))
        if products:
            self.product_var.set(products[0])
        else:
            self.product_var.set("No Products Available")
            self.product_dropdown.config(state=tk.DISABLED)

        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)
        self.product_dropdown.config(state=state)


    def export_data(self, file_format):
        """Filters data based on criteria and exports to the chosen format."""
        if self.data_manager.sales_data.empty:
            messagebox.showwarning("No Data", "No data available to export. Please import data first.", parent=self)
            return

        try:
            selected_branch = self.branch_var.get()
            selected_product = self.product_var.get()
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.", parent=self)
                return

            filtered_df = self.data_manager.sales_data.copy()

            if selected_branch != "All Branches":
                filtered_df = filtered_df[filtered_df['Branch'] == selected_branch]
            if selected_product != "All Products":
                filtered_df = filtered_df[filtered_df['Product'] == selected_product]

            filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

            if filtered_df.empty:
                messagebox.showwarning("No Data", "No data found for the selected filters to export.", parent=self)
                return

            file_types = {
                "csv": [("CSV files", "*.csv")],
                "xlsx": [("Excel files", "*.xlsx")],
                "pdf": [("PDF files", "*.pdf")]
            }
            default_ext = "." + file_format
            file_path = filedialog.asksaveasfilename(
                defaultextension=default_ext,
                filetypes=file_types.get(file_format, [("All files", "*.*")]),
                title=f"Save Data as {file_format.upper()}"
            )

            if file_path:
                if file_format == "csv":
                    filtered_df.to_csv(file_path, index=False)
                elif file_format == "xlsx":
                    filtered_df.to_excel(file_path, index=False)
                elif file_format == "pdf":
                    # For PDF export, we'll save a simple table summary of the data.
                    # Full dataframe to PDF is complex and typically requires external libraries like ReportLab or FPDF.
                    fig, ax = plt.subplots(figsize=(11, 8.5)) # Standard paper size
                    ax.axis('off')
                    ax.set_title(f"Sales Data Export ({start_date_str} to {end_date_str})", fontsize=14, pad=20)

                    # Prepare data for table: limit columns and rows for readability in PDF
                    display_df = filtered_df.head(20).copy() # Show first 20 rows
                    if 'Date' in display_df.columns:
                        display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d') # Format date for display

                    table = ax.table(cellText=display_df.values, colLabels=display_df.columns, loc='center', cellLoc='left')
                    table.auto_set_font_size(False)
                    table.set_fontsize(8)
                    table.scale(1.2, 1.2) # Adjust size

                    fig.savefig(file_path, bbox_inches='tight', pad_inches=0.5)
                    plt.close(fig) # Close the figure to free memory

                self.status_label.config(text=f"Report downloaded successfully to {file_path}!")
            else:
                self.status_label.config(text="Export cancelled.", fg="orange")

        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-%d.", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export: {e}", parent=self)

# --- 10. Settings Page (Optional) ---
class SettingsPage(BasePage):
    """
    Placeholder for system settings like changing password or theme.
    """
    def __init__(self, master, data_manager):
        super().__init__(master, data_manager, "Settings")
        tk.Label(self, text="Settings Page (Under Construction)", font=("Arial", 18, "bold")).pack(pady=50)
        tk.Label(self, text="This page would allow you to configure user preferences, change passwords, \nset default branches, or choose themes (e.g., dark/light mode).", font=("Arial", 11)).pack()

# --- 11. Exit Confirmation Page ---
class ExitConfirmationPage(tk.Toplevel):
    """
    Confirms user's intention to exit the application.
    """
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Exit Confirmation")
        self.geometry("350x180")
        self.grab_set() # Make modal
        self.protocol("WM_DELETE_WINDOW", self.on_no) # If closed, treat as 'No'
        self.resizable(False, False)
        self.transient(master) # Make it appear on top of the main window

        tk.Label(self, text="Are you sure you want to exit the application?", font=("Arial", 12, "bold")).pack(pady=30)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Yes, Exit", command=self.on_yes, font=("Arial", 10, "bold"), bg="#dc3545", fg="white", relief="raised").pack(side="left", padx=15)
        tk.Button(button_frame, text="No, Stay", command=self.on_no, font=("Arial", 10, "bold"), bg="#6c757d", fg="white", relief="raised").pack(side="left", padx=15)

    def on_yes(self):
        """Destroys the main application window, exiting the program."""
        self.master.destroy() # Destroy the main application window
        self.destroy() # Close this confirmation window

    def on_no(self):
        """Closes the confirmation window and returns to the main application."""
        self.destroy() # Close this confirmation window
        self.master.deiconify() # Show the main application window again
        self.master.lift() # Bring main window to front

# --- Main Application Class ---
class MainApp(tk.Tk):
    """
    The main application window, managing the overall flow and pages.
    Composition: MainApp creates and holds instances of DataManager and DashboardPage.
    """
    def __init__(self):
        super().__init__()
        self.title("Sales Analysis System")
        self.geometry("900x700") # Initial size for the main window
        self.withdraw() # Hide main window initially until login is complete

        self.data_manager = DataManager() # Composition: MainApp 'has-a' DataManager
        self.dashboard_page = None # Will hold the dashboard instance

        # Keep track of open analysis pages to update their dropdowns
        self.open_analysis_windows = []
        self.bind("<Map>", self._on_window_map) # Event to track when a Toplevel window is opened

        self.show_login()

    def _on_window_map(self, event):
        """Callback when any Toplevel window is mapped (opened)."""
        # Check if the event is from a Toplevel and it's an analysis page
        if isinstance(event.widget, tk.Toplevel) and hasattr(event.widget, 'refresh_dropdowns'):
            if event.widget not in self.open_analysis_windows:
                self.open_analysis_windows.append(event.widget)
                # print(f"Added {event.widget.title()} to open windows list.")

        # Clean up closed windows from the list
        self.open_analysis_windows = [win for win in self.open_analysis_windows if win.winfo_exists()]


    def show_login(self):
        """Displays the login page."""
        LoginPage(self, self.data_manager)

    def show_dashboard(self, user_role):
        """
        Displays the dashboard page after successful login.
        Destroys any existing dashboard and creates a new one to refresh content.
        """
        if self.dashboard_page:
            self.dashboard_page.destroy()
        self.deiconify() # Show the main window
        self.dashboard_page = DashboardPage(self, self.data_manager, user_role)
        self.dashboard_page.lift() # Bring to front

    def update_all_page_dropdowns(self):
        """
        Triggers the refresh of dropdowns in all currently open analysis pages.
        Also updates the dashboard summary and button states.
        """
        self.dashboard_page.update_summary()
        self.dashboard_page.update_button_states()

        # Filter out any windows that might have been closed
        self.open_analysis_windows = [win for win in self.open_analysis_windows if win.winfo_exists()]

        for page in self.open_analysis_windows:
            if hasattr(page, 'refresh_dropdowns'):
                page.refresh_dropdowns()
                # If the page has a generate_report/analyze_price/etc. method,
                # you might want to call it to refresh the content too,
                # but this could be heavy and might require more complex state management.
                # For now, we only refresh dropdowns.
                # print(f"Refreshed dropdowns for {page.title()}")


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
