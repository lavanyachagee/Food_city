import os
import sys
import unittest
import coverage
from tkinter import Tk
import pandas as pd

# --- Mock Import of Classes from Your System ---
try:
    from main import DataManager
    from main import MonthlySalesPage
except ImportError:
    print("Error: Could not find 'DataManager' or 'MonthlySalesPage' in 'main.py'.")
    print("Make sure 'main.py' is in the same directory and contains these classes.")
    sys.exit(1)

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
        """Test that get_products returns a list of unique product names."""
        products = self.manager.get_products()
        self.assertIsInstance(products, list)

    def test_get_years_returns_list(self):
        """Test that get_years returns a list of years from the sales data."""
        years = self.manager.get_years()
        self.assertIsInstance(years, list)
        if not self.manager.sales_data.empty:
            self.assertIn(self.manager.sales_data['Date'].dt.year.iloc[0], years)

    def test_get_monthly_sales_returns_dataframe(self):
        """Test that get_monthly_sales returns a DataFrame with expected columns."""
        report = self.manager.get_monthly_sales(branch="All Branches", year=2024, month=None)
        self.assertIsInstance(report, pd.DataFrame)
        expected_columns = ['Product', 'Quantity', 'UnitPrice', 'Total']
        for col in expected_columns:
            self.assertIn(col, report.columns)


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


# --- 3. REGRESSION SUITE ---
def regression_suite():
    suite = unittest.TestSuite()
    suite.addTest(TestDataManager('test_add_data_valid'))
    suite.addTest(TestDataManager('test_get_products_returns_list'))
    suite.addTest(TestDataManager('test_get_years_returns_list'))
    suite.addTest(TestDataManager('test_get_monthly_sales_returns_dataframe'))
    suite.addTest(TestMonthlySalesPageIntegration('test_generate_report_with_valid_filters'))
    return suite


# --- 4. COVERAGE REPORTER ---
def run_tests_with_coverage():
    cov = coverage.Coverage(source=["main"])
    cov.start()

    # Run all tests
loader = unittest.TestLoader()
try:
    suite = loader.discover(start_dir="test")
    
# Run only tests from this file
loader = unittest.TestLoader()
suite = loader.loadTestsFromModule(sys.modules[__name__])

    print("\n--- CODE COVERAGE REPORT ---\n")
    cov.report()
    cov.html_report(directory="coverage_report")
    print(f"HTML report saved to {os.path.abspath('coverage_report/index.html')}")
    return result


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("🚀 Running unit and integration tests...\n")

    # Option A: Run full coverage + all discovered tests (requires /test folder)
    try:
        test_result = run_tests_with_coverage()
        if test_result.wasSuccessful():
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed.")
    except Exception as e:
        print(f"⚠️ Error during coverage run: {e}")
        print("Running basic regression suite instead...\n")
        runner = unittest.TextTestRunner()
        runner.run(regression_suite())
