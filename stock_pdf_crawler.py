#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票資訊PDF爬蟲 Stock PDF Crawler
用於爬取公開資訊觀測站股票資料並保存為PDF
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 配置日誌 Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StockPDFCrawler:
    """
    股票PDF爬蟲類別 Stock PDF Crawler Class
    負責自動化瀏覽器操作，抓取股票資訊並保存為PDF
    """
    
    def __init__(self, download_path="./downloads"):
        """
        初始化爬蟲 Initialize crawler
        Args:
            download_path: PDF檔案下載路徑 PDF download path
        """
        self.download_path = os.path.abspath(download_path)
        self.driver = None
        self.base_url = "https://mops.twse.com.tw/mops/#/web/t146sb05"
        
        # 確保下載目錄存在 Ensure download directory exists
        os.makedirs(self.download_path, exist_ok=True)
        logger.info("Download path initialized: %s", self.download_path)
    
    def _setup_driver(self):
        """
        設置Chrome瀏覽器驅動 Setup Chrome webdriver
        配置無頭模式和PDF打印設定
        """
        chrome_options = Options()
        
        # 基本設定 Basic settings
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # PDF打印設定 PDF printing settings
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 設置下載路徑 Set download path
        prefs = {
            "printing.print_preview_sticky_settings.appState": {
                "recentDestinations": [{
                    "id": "Save as PDF",
                    "origin": "local",
                    "account": ""
                }],
                "selectedDestinationId": "Save as PDF",
                "version": 2
            },
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 自動安裝ChromeDriver Auto install ChromeDriver
        try:
            # 嘗試使用WebDriverManager
            driver_path = ChromeDriverManager().install()
            
            # 修復macOS ARM64上的路徑問題 Fix path issue on macOS ARM64
            if 'THIRD_PARTY_NOTICES' in driver_path:
                import os
                driver_dir = os.path.dirname(driver_path)
                # 尋找實際的chromedriver可執行文件 Find the actual chromedriver executable
                for file in os.listdir(driver_dir):
                    if file == 'chromedriver' or file.startswith('chromedriver') and not 'THIRD_PARTY' in file:
                        driver_path = os.path.join(driver_dir, file)
                        break
                logger.info("Fixed ChromeDriver path: %s", driver_path)
                
                # 修復執行權限 Fix execute permissions
                os.chmod(driver_path, 0o755)
                logger.info("Set execute permissions: %s", driver_path)
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
        except Exception as e:
            logger.error("WebDriverManager failed: %s", str(e))
            # 降級方案：嘗試使用系統PATH中的chromedriver Fallback: try system chromedriver
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Using system ChromeDriver from PATH")
            except Exception as e2:
                logger.error("System ChromeDriver also failed: %s", str(e2))
                raise Exception(f"無法初始化ChromeDriver: {str(e2)}")
        
        logger.info("Chrome driver initialized successfully")
    
    def crawl_stock_pdf(self, company_id, timeout=30):
        """
        爬取指定股票的PDF資料 Crawl PDF data for specified stock
        分別爬取基本資料、營收資訊、財報資訊三個欄位
        
        Args:
            company_id (str): 股票代碼 Stock company ID
            timeout (int): 等待超時秒數 Wait timeout in seconds
            
        Returns:
            bool: 成功返回True，失敗返回False
        """
        if not company_id:
            logger.error("Company ID cannot be empty")
            return False
            
        # 定義要爬取的欄位 Define sections to crawl
        sections = [
            {"name": "基本資料", "class": "basic_info", "filename_suffix": "basic"},
            {"name": "營收資訊", "class": "revenue_information", "filename_suffix": "revenue"},
            {"name": "財報資訊", "class": "financial_report_information", "filename_suffix": "financial"}
        ]
        
        success_count = 0
        
        try:
            self._setup_driver()
            
            # 構建完整URL Build complete URL
            url = f"{self.base_url}?companyId={company_id}"
            logger.info("Navigating to URL: %s", url)
            
            # 訪問頁面 Navigate to page
            self.driver.get(url)
            
            # 等待頁面載入 Wait for page to load
            wait = WebDriverWait(self.driver, timeout)
            
            # 等待主要內容載入 Wait for main content to load
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(3)  # 額外等待JavaScript渲染 Additional wait for JS rendering
                logger.info("Page loaded for company_id: %s", company_id)
            except TimeoutException:
                logger.error("Page load timeout for company_id: %s", company_id)
                return False
            
            # 依次處理每個欄位 Process each section
            for section in sections:
                logger.info("Processing section: %s for company_id: %s", section["name"], company_id)
                
                try:
                    # 點擊對應的欄位按鈕 Click the section button
                    section_button = self._find_section_button(wait, section["class"])
                    if not section_button:
                        logger.error("Section button not found: %s", section["name"])
                        continue
                    
                    # 點擊欄位按鈕 Click section button
                    logger.info("Clicking section button: %s", section["name"])
                    self.driver.execute_script("arguments[0].click();", section_button)
                    
                    # 等待內容載入 Wait for content to load
                    time.sleep(2)
                    
                    # 尋找打印按鈕 Find print button
                    print_button = self._find_print_button(wait)
                    if not print_button:
                        logger.error("Print button not found for section: %s", section["name"])
                        continue
                    
                    # 生成PDF Generate PDF
                    success = self._generate_section_pdf(company_id, section, print_button)
                    if success:
                        success_count += 1
                        logger.info("Successfully generated PDF for section: %s", section["name"])
                    else:
                        logger.error("Failed to generate PDF for section: %s", section["name"])
                    
                    # 短暫延遲避免請求過於頻繁 Brief delay to avoid too frequent requests
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error("Error processing section %s: %s", section["name"], str(e))
                    continue
            
            # 檢查是否至少成功一個 Check if at least one succeeded
            if success_count > 0:
                logger.info("Successfully generated %d out of %d PDFs for company_id: %s", 
                          success_count, len(sections), company_id)
                return True
            else:
                logger.error("Failed to generate any PDFs for company_id: %s", company_id)
                return False
            
        except Exception as e:
            logger.error("Error occurred while crawling company_id %s: %s", company_id, str(e))
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser driver closed")
    
    def _find_section_button(self, wait, section_class):
        """
        尋找欄位按鈕 Find section button
        
        Args:
            wait: WebDriverWait實例
            section_class: 欄位按鈕的class名稱
            
        Returns:
            WebElement or None: 找到的按鈕元素
        """
        selectors = [
            f"button.{section_class}",
            f"button[class*='{section_class}']",
            f"*[class*='{section_class}']"
        ]
        
        for selector in selectors:
            try:
                element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info("Section button found with selector: %s", selector)
                return element
            except TimeoutException:
                continue
            except Exception as e:
                logger.warning("Error with selector %s: %s", selector, str(e))
                continue
        
        return None
    
    def _generate_section_pdf(self, company_id, section, print_button):
        """
        為特定欄位生成PDF Generate PDF for specific section
        
        Args:
            company_id: 股票代碼
            section: 欄位資訊字典
            print_button: 打印按鈕元素
            
        Returns:
            bool: 成功返回True，失敗返回False
        """
        try:
            # 生成PDF檔名 Generate PDF filename
            timestamp = int(time.time())
            pdf_filename = f"stock_{company_id}_{section['filename_suffix']}_{timestamp}.pdf"
            pdf_path = os.path.join(self.download_path, pdf_filename)
            
            logger.info("Generating PDF for section: %s", section["name"])
            
            # 使用Chrome DevTools Protocol生成PDF Use Chrome DevTools Protocol to generate PDF
            result = self.driver.execute_cdp_cmd('Page.printToPDF', {
                'landscape': False,
                'displayHeaderFooter': False,
                'printBackground': True,
                'preferCSSPageSize': True,
                'paperWidth': 8.27,  # A4 width in inches
                'paperHeight': 11.69,  # A4 height in inches
                'marginTop': 0.4,
                'marginBottom': 0.4,
                'marginLeft': 0.4,
                'marginRight': 0.4,
            })
            
            # 保存PDF Save PDF
            with open(pdf_path, 'wb') as file:
                import base64
                file.write(base64.b64decode(result['data']))
            
            logger.info("PDF saved successfully: %s", pdf_path)
            return True
            
        except Exception as e:
            logger.error("Failed to generate PDF for section %s: %s", section["name"], str(e))
            return False
    
    def _find_print_button(self, wait):
        """
        尋找打印按鈕 Find print button
        根據提供的HTML結構尋找包含打印圖標的元素
        
        Args:
            wait: WebDriverWait實例
            
        Returns:
            WebElement or None: 找到的打印按鈕元素
        """
        # 多種選擇器策略 Multiple selector strategies
        selectors = [
            # 根據data-name屬性 By data-name attribute
            "span[data-name='列印網頁']",
            # 根據SVG路徑 By SVG path
            "span svg path[fill='#156FF5']",
            # 根據父級span By parent span
            "span[data-v-5dfef1eb] svg",
            # 更通用的打印按鈕選擇器 Generic print button selectors
            "button[title*='列印'], button[title*='print'], a[title*='列印'], a[title*='print']",
            # 包含打印字樣的元素 Elements containing print text
            "//*[contains(text(), '列印') or contains(text(), 'print') or contains(text(), 'Print')]"
        ]
        
        for selector in selectors:
            try:
                if selector.startswith('/'):
                    # XPath選擇器 XPath selector
                    element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    # CSS選擇器 CSS selector
                    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                logger.info("Print button found with selector: %s", selector)
                return element
                
            except TimeoutException:
                continue
            except Exception as e:
                logger.warning("Error with selector %s: %s", selector, str(e))
                continue
        
        return None


def main():
    """
    主函數 Main function
    示範如何使用StockPDFCrawler
    """
    # 初始化爬蟲 Initialize crawler
    crawler = StockPDFCrawler(download_path="./stock_pdfs")
    
    # 測試股票代碼列表 Test stock company IDs
    test_company_ids = ["2049", "2330", "2454"]  # 可自定義股票代碼 Customizable stock IDs
    
    for company_id in test_company_ids:
        logger.info("Starting crawl for company_id: %s", company_id)
        success = crawler.crawl_stock_pdf(company_id)
        
        if success:
            logger.info("Successfully crawled company_id: %s", company_id)
        else:
            logger.error("Failed to crawl company_id: %s", company_id)
        
        # 避免過於頻繁請求 Avoid too frequent requests
        time.sleep(5)


if __name__ == "__main__":
    main() 