import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from dashboard_data import PRICE, load_mysql_data


class MysqlDashboardTests(unittest.TestCase):
    def test_view_data_and_connection_cleanup(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.fetchall.return_value = [(17, '测试商品', Decimal('943.00'), '未标注', None)]
        with patch('mysql.connector.connect', return_value=connection):
            df = load_mysql_data({'user': 'root', 'password': 'example'})
        self.assertEqual(df.iloc[0][PRICE], 943.0)
        self.assertEqual(df.iloc[0]['商品链接'], '')
        self.assertIn('cleaned_product_snapshots', cursor.execute.call_args[0][0])
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_connection_error_hides_password(self):
        with patch('mysql.connector.connect', side_effect=RuntimeError('secret-password')):
            with self.assertRaises(ValueError) as caught:
                load_mysql_data({'password': 'secret-password'})
        self.assertNotIn('secret-password', str(caught.exception))
