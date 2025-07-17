import os
import sys
import unittest
import coverage
from tkinter import Tk
import pandas as pd

# --- Import your classes ---
from main import DataManager, MonthlySalesPage

# --- 1. UNIT TESTS FOR DATA MANAGER ---
class TestDataManager(unittest.TestCase):
    def setUp(self):
        self.manager = DataManager(data_file="test_sales_data.csv")

    def test_load_data_returns_dataframe(self):
        self.assertIsInstance(self.manager.sales_data, pd.DataFrame)

    def test_get_branches_returns_list(self):
        branches = self.manager.get_branches()
        self.assertIsInstance(branches, list)

    def test_add_data_valid(self):
        new_data = pd.DataFrame({
            "Date": ["2024-06-01"],
            "Branch": ["Colombo"],
            "Product": ["Milk"],
            "Quantity": [5],
            "UnitPrice": [150],
            "Total": [750]
        })
        result = self.manager.add_data(new_data)
        self.assertTrue(result)
        self.assertEqual(len(self.manager.sales_data), 1)

    def test_get_products_returns_list(self):
        products = self.manager.get_products()
        self.assertIsInstance(products, list)

    def test_get_years_returns_list(self):
        years = self.manager.get_years()
        self.assertIsInstance(years, list)
        if not self.manager.sales_data.empty:
            self.assertIn(self.manager.sales_data['Date'].dt.year.iloc[0], years)

    def test_get_monthly_sales_returns_dataframe(self):
        report = self.manager.get_monthly_sales(branch="All Branches", year=2024, month=None)
        self.assertIsInstance(report, pd.DataFrame)
        expected_columns = ['Product', 'Quantity', 'UnitPrice', 'Total']
        for col in expected_columns:
            self.assertIn(col, report.columns)

class TestAnalysisMethods(unittest.TestCase):
    def setUp(self):
        self.manager = DataManager(data_file="test_sales_data.csv")
        # Ensure data exists (use mock data if needed)
        if self.manager.sales_data.empty:
            test_data = pd.DataFrame({
                "Date": pd.to_datetime(["2024-06-01", "2024-06-02", "2024-06-03", "2024-06-04"]),
                "Branch": ["Colombo", "Kandy", "Colombo", "Kandy"],
                "Product": ["Milk", "Bread", "Milk", "Eggs"],
                "Quantity": [5, 10, 2, 12],
                "UnitPrice": [150, 50, 160, 30],
                "Total": [750, 500, 320, 360]
            })
            self.manager.add_data(test_data)

    def test_monthly_sales_analysis(self):
        df = self.manager.get_monthly_sales(branch="Colombo", year=2024, month=6)
        self.assertFalse(df.empty)
        self.assertIn("Product", df.columns)

    def test_price_analysis(self):
        df = self.manager.get_product_price_history("Milk")
        self.assertFalse(df.empty)
        self.assertIn("UnitPrice", df.columns)

    def test_weekly_sales_analysis(self):
        start = pd.Timestamp("2024-06-01")
        end = pd.Timestamp("2024-06-07")
        df = self.manager.get_weekly_sales(start, end, branch="All Branches")
        self.assertFalse(df.empty)
        self.assertIn("DayOfWeek", df.columns)

    def test_product_preference_analysis(self):
        start = pd.Timestamp("2024-06-01")
        end = pd.Timestamp("2024-06-07")
        df = self.manager.get_product_preferences(date_range=(start, end), branch="All Branches")
        self.assertFalse(df.empty)
        self.assertIn("Product", df.columns)

    def test_sales_distribution_analysis(self):
        start = pd.Timestamp("2024-06-01")
        end = pd.Timestamp("2024-06-07")
        series = self.manager.get_sales_distribution(date_range=(start, end), branch="All Branches")
        self.assertFalse(series.empty)
        self.assertIsInstance(series, pd.Series)

# --- 2. INTEGRATION TESTS ---
class TestMonthlySalesPageIntegration(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.data_manager = DataManager(data_file="test_sales_data.csv")
        self.page = MonthlySalesPage(self.root, self.data_manager)

    def test_generate_report_with_valid_filters(self):
        self.page.branch_var.set("Colombo")
        self.page.year_var.set("2024")
        self.page.month_var.set("All Months")
        self.page.generate_report()
        tree_items = self.page.tree.get_children()
        self.assertGreaterEqual(len(tree_items), 0)

    def tearDown(self):
        self.root.destroy()

# --- 3. RUN TESTS WITH COVERAGE ---
def run_tests_with_coverage():
    cov = coverage.Coverage(source=["main"])
    cov.start()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDataManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMonthlySalesPageIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    cov.stop()
    cov.save()

    print("\n--- CODE COVERAGE REPORT ---\n")
    cov.report()
    cov.html_report(directory="coverage_report")
    print(f"HTML report saved to {os.path.abspath('coverage_report/index.html')}")

    return result

# --- 4. MAIN ENTRY POINT ---
if __name__ == "__main__":
    print("🚀 Running unit and integration tests...\n")
    test_result = run_tests_with_coverage()

    if test_result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed.")
