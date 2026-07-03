import unittest
from unittest.mock import patch, MagicMock
from app import get_reddit_opinion, get_tradingview_analysis, get_finviz_recommendation

class TestStockAnalyzer(unittest.TestCase):
    
    @patch('app.DDGS')
    def test_get_reddit_opinion(self, mock_ddgs):
        # Mock the context manager and text method
        mock_instance = MagicMock()
        mock_ddgs.return_value.__enter__.return_value = mock_instance
        
        mock_instance.text.return_value = [
            {'body': 'AAPL is going to the moon, great earnings!', 'href': 'https://reddit.com/r/stocks/1'},
            {'body': 'I love this stock, amazing company.', 'href': 'https://reddit.com/r/wallstreetbets/2'}
        ]
        
        sentiment, score, links = get_reddit_opinion("AAPL")
        self.assertIn("Positive", sentiment)
        self.assertGreater(score, 0)
        self.assertEqual(len(links), 2)
        
    @patch('app.TA_Handler')
    def test_get_tradingview_analysis(self, mock_ta):
        mock_instance = MagicMock()
        mock_ta.return_value = mock_instance
        mock_instance.get_analysis.return_value.summary = {"RECOMMENDATION": "BUY"}
        
        summary = get_tradingview_analysis("AAPL")
        self.assertEqual(summary, {"RECOMMENDATION": "BUY"})
        
    @patch('app.requests.get')
    def test_get_finviz_recommendation(self, mock_get):
        mock_response = MagicMock()
        # Mock HTML snippet containing Finviz Recom structure
        mock_response.text = '<html><body><table><tr><td>Recom</td><td><b>2.10</b></td></tr></table></body></html>'
        mock_get.return_value = mock_response
        
        recom = get_finviz_recommendation("AAPL")
        self.assertEqual(recom, "BUY (2.1)")
        
    @patch('app.requests.get')
    def test_get_finviz_recommendation_strong_buy(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = '<html><body><table><tr><td>Recom</td><td><b>1.2</b></td></tr></table></body></html>'
        mock_get.return_value = mock_response
        
        recom = get_finviz_recommendation("AAPL")
        self.assertEqual(recom, "STRONG BUY (1.2)")

if __name__ == '__main__':
    unittest.main()