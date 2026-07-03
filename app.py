import streamlit as st
import yfinance as yf
from tradingview_ta import TA_Handler, Interval, Exchange
from ddgs import DDGS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd

st.set_page_config(page_title="Stock Market Analyzer", layout="wide")

st.title("Stock Market Analyzer")
st.markdown("Get detailed market analysis, buy/sell recommendations, and Reddit sentiment for any stock ticker.")

ticker_input = st.text_input("Enter a Stock Ticker (e.g., AAPL, TSLA, MSFT):").upper().strip()

def get_reddit_opinion(ticker):
    analyzer = SentimentIntensityAnalyzer()
    results = []
    try:
        with DDGS() as ddgs:
            # We search for the ticker and some keywords to find stock opinions on Reddit
            for r in ddgs.text(f"site:reddit.com {ticker} stock opinion", max_results=20):
                results.append(r['body'])
    except Exception as e:
        return "Error fetching Reddit data", 0

    if not results:
        return "No recent Reddit discussions found.", 0

    scores = [analyzer.polarity_scores(text)['compound'] for text in results]
    avg_score = sum(scores) / len(scores)

    if avg_score > 0.15:
        sentiment = "Positive 🟢"
    elif avg_score < -0.15:
        sentiment = "Negative 🔴"
    else:
        sentiment = "Neutral 🟡"
    
    return sentiment, avg_score

def get_tradingview_analysis(ticker):
    try:
        # We try NASDAQ first, if it fails we could try NYSE, but TradingView TA often handles this.
        handler = TA_Handler(
            symbol=ticker,
            exchange="NASDAQ",
            screener="america",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        return analysis.summary
    except Exception:
        try:
            handler = TA_Handler(
                symbol=ticker,
                exchange="NYSE",
                screener="america",
                interval=Interval.INTERVAL_1_DAY
            )
            analysis = handler.get_analysis()
            return analysis.summary
        except Exception as e:
            return None

if ticker_input:
    with st.spinner(f"Analyzing {ticker_input}..."):
        # 1. YFinance Info
        ticker = yf.Ticker(ticker_input)
        
        try:
            info = ticker.info
            fast_info = ticker.fast_info
            
            if 'shortName' not in info and not fast_info.last_price:
                st.error("Invalid ticker or data unavailable.")
                st.stop()
                
            name = info.get('shortName', ticker_input)
            current_price = fast_info.last_price
            market_cap = info.get('marketCap', 'N/A')
            pe_ratio = info.get('trailingPE', 'N/A')
            fifty_two_high = info.get('fiftyTwoWeekHigh', 'N/A')
            fifty_two_low = info.get('fiftyTwoWeekLow', 'N/A')
            yf_rec = info.get('recommendationKey', 'N/A')
            
            # Format numbers
            if isinstance(market_cap, (int, float)):
                if market_cap >= 1e12:
                    market_cap_str = f"${market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    market_cap_str = f"${market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:
                    market_cap_str = f"${market_cap/1e6:.2f}M"
                else:
                    market_cap_str = f"${market_cap:,.2f}"
            else:
                market_cap_str = market_cap

            # 2. TradingView TA
            tv_summary = get_tradingview_analysis(ticker_input)
            
            # 3. YF News
            news = ticker.news[:5] if ticker.news else []
            
            # 4. Reddit Opinion
            reddit_sentiment, reddit_score = get_reddit_opinion(ticker_input)

            # Display Data
            st.header(f"{name} ({ticker_input})")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", f"${current_price:.2f}")
            with col2:
                st.metric("Market Cap", market_cap_str)
            with col3:
                st.metric("P/E Ratio", f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else pe_ratio)
            with col4:
                st.metric("52W Range", f"${fifty_two_low} - ${fifty_two_high}")

            st.divider()

            st.subheader("Buy / Sell Recommendation")
            rec_col1, rec_col2 = st.columns(2)
            
            with rec_col1:
                st.markdown("### Analyst Recommendation (Yahoo Finance)")
                if yf_rec and yf_rec != 'N/A':
                    st.info(f"**{yf_rec.upper()}**")
                else:
                    st.write("Data not available")

            with rec_col2:
                st.markdown("### Technical Analysis (TradingView)")
                if tv_summary:
                    tv_rec = tv_summary.get('RECOMMENDATION', 'N/A')
                    st.info(f"**{tv_rec}**")
                    st.write(f"Buy: {tv_summary.get('BUY', 0)} | Sell: {tv_summary.get('SELL', 0)} | Neutral: {tv_summary.get('NEUTRAL', 0)}")
                else:
                    st.write("Technical analysis data not available.")

            st.divider()

            st.subheader("Reddit Opinion")
            st.markdown(f"**Overall Sentiment:** {reddit_sentiment}")
            st.caption(f"Sentiment Score: {reddit_score:.2f} (Range: -1 to 1)")
            st.write("Based on recent discussions on Reddit.")

            st.divider()

            st.subheader("Analysis Overview & News")
            st.write(f"Company Business Summary: {info.get('longBusinessSummary', 'Not available.')}")
            
            st.markdown("**Latest News:**")
            for n in news:
                title = n.get('content', {}).get('title')
                link = n.get('content', {}).get('clickThroughUrl', {}).get('url')
                if title:
                    if link:
                        st.markdown(f"- [{title}]({link})")
                    else:
                        st.markdown(f"- {title}")

        except Exception as e:
            st.error(f"An error occurred while fetching data: {e}")