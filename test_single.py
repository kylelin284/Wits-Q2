#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試單一股票PDF下載 Test Single Stock PDF Download
"""

from stock_pdf_crawler import StockPDFCrawler
import logging

# 配置日誌 Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_single_stock():
    """
    測試單一股票下載 Test single stock download
    """
    company_id = "2049"  # 可以修改為任何股票代碼 Can modify to any stock ID
    
    logger.info("開始測試股票代碼: %s", company_id)
    
    # 初始化爬蟲 Initialize crawler
    crawler = StockPDFCrawler(download_path="./test_pdfs")
    
    try:
        # 執行爬取 Execute crawling
        success = crawler.crawl_stock_pdf(company_id, timeout=60)
        
        if success:
            logger.info("✅ 測試成功! 股票 %s 的PDF已下載", company_id)
        else:
            logger.error("❌ 測試失敗! 股票 %s 的PDF下載失敗", company_id)
            
    except Exception as e:
        logger.error("測試過程中發生錯誤: %s", str(e))


if __name__ == "__main__":
    test_single_stock() 