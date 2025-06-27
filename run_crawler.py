#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票PDF爬蟲執行腳本 Stock PDF Crawler Runner
簡化的執行介面，方便自定義股票代碼
"""

from stock_pdf_crawler import StockPDFCrawler
import logging

# 配置簡單日誌 Configure simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def crawl_single_stock(company_id):
    """
    爬取單一股票資料 Crawl single stock data
    
    Args:
        company_id (str): 股票代碼 Stock company ID
    """
    logger.info("開始爬取股票代碼: %s", company_id)
    
    # 初始化爬蟲 Initialize crawler
    crawler = StockPDFCrawler(download_path="./pdfs")
    
    # 執行爬取 Execute crawling
    success = crawler.crawl_stock_pdf(company_id)
    
    if success:
        logger.info("成功完成股票 %s 的PDF下載", company_id)
    else:
        logger.error("股票 %s 的PDF下載失敗", company_id)
    
    return success


def crawl_multiple_stocks(company_ids):
    """
    批量爬取多支股票 Batch crawl multiple stocks
    
    Args:
        company_ids (list): 股票代碼列表 List of stock company IDs
    """
    results = {}
    
    for company_id in company_ids:
        logger.info("處理股票代碼: %s", company_id)
        results[company_id] = crawl_single_stock(company_id)
        
        # 避免請求過於頻繁 Avoid too frequent requests
        import time
        time.sleep(3)
    
    # 輸出結果摘要 Output results summary
    logger.info("=== 爬取結果摘要 Crawling Results Summary ===")
    for company_id, success in results.items():
        status = "成功" if success else "失敗"
        logger.info("股票 %s: %s", company_id, status)


if __name__ == "__main__":
    # 方式1：單一股票 Method 1: Single stock
    # crawl_single_stock("2049")
    
    # 方式2：多支股票 Method 2: Multiple stocks
    # stock_list = [
        # "2049",  # 上銀
        # "2330",  # 台積電
        # "2454",  # 聯發科
        # 在這裡添加更多股票代碼 Add more stock IDs here
    # ]
    stock_list = ["2409","2330","0001","2454","2317","2308","2382","3034","2379","2303"]
    crawl_multiple_stocks(stock_list)
    
    # 方式3：互動式輸入 Method 3: Interactive input
    # while True:
    #     company_id = input("請輸入股票代碼 (輸入 'quit' 結束): ").strip()
    #     if company_id.lower() == 'quit':
    #         break
    #     if company_id:
    #         crawl_single_stock(company_id) 