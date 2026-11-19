import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("dashboard_data"), "缺少看板数据模块")
        import dashboard_data
        self.model = dashboard_data

    def test_real_sample_and_price_boundaries(self):
        df = self.model.load_data(Path(__file__).resolve().parents[1] / "taobao_laptops_50.csv")
        self.assertEqual(len(df), 50)
        selected = self.model.filter_data(df, "", (5000, 8000), df["价格说明"].unique().tolist(), False)
        self.assertEqual(len(selected), 9)
        self.assertAlmostEqual(df[self.model.PRICE].median(), 4063.5)
        self.assertEqual(df["同名待核查"].sum(), 2)

    def test_literal_keyword_and_combined_filters(self):
        df = pd.DataFrame({"名称": ["A[1]", "A[1]", "Other"], self.model.PRICE: [5000, 8000, 6000], "价格说明": ["国补后", "优惠后", "国补后"], "同名待核查": [True, True, False]})
        selected = self.model.filter_data(df, "[1]", (5000, 8000), ["国补后"], True)
        self.assertEqual(selected[self.model.PRICE].tolist(), [5000])
        self.assertTrue(self.model.filter_data(df, "", (0, 10000), [], False).empty)

    def test_encoding_validation_and_safe_links(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "data.csv"
            pd.DataFrame({"名称": ["电脑"], self.model.PRICE: [5000], "价格说明": [None], "商品链接": ["javascript:alert(1)"]}).to_csv(path, index=False, encoding="gb18030")
            df = self.model.load_data(path)
            self.assertEqual(df.iloc[0]["价格说明"], "未标注")
            self.assertEqual(df.iloc[0]["商品链接"], "")
            pd.DataFrame({"名称": ["坏数据"], self.model.PRICE: [-1], "价格说明": [""], "商品链接": [""]}).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                self.model.load_data(path)


if __name__ == "__main__":
    unittest.main()
