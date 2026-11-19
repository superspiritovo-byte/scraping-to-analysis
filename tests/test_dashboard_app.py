import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "dashboard.py"


class DashboardAppTests(unittest.TestCase):
    def test_default_filters_empty_reset_and_sort(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "50")
        self.assertEqual(len(app.dataframe[0].value), 50)
        app.slider(key="budget").set_value((5000.0, 8000.0)).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "9")
        self.assertEqual(len(app.dataframe[0].value), 9)
        app.selectbox(key="order").select("价格从低到高").run()
        self.assertTrue(app.dataframe[0].value["页面展示价格（元）"].is_monotonic_increasing)
        app.text_input(key="keyword").set_value("不存在的商品XYZ").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "0")
        self.assertGreater(len(app.info), 0)
        app.button(key="reset_filters").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "50")
        app.checkbox(key="duplicates").check().run()
        self.assertEqual(app.metric[0].value, "2")
        app.multiselect(key="notes").set_value([]).run()
        self.assertEqual(app.metric[0].value, "0")


if __name__ == "__main__":
    unittest.main()
