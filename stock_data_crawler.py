import requests
from bs4 import BeautifulSoup
import ast
import pandas as pd
import time
# import pyodbc

stock_code_list = ["2409","2330","0001","2454","2317","2308","2382","3034","2379","2303"]
for stock_code in stock_code_list:
    url = 'https://mops.twse.com.tw/mops/api/t146sb05' ###
    payload = {
        "companyId": stock_code
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0',
        'Origin': 'https://mops.twse.com.tw',
        'Referer': 'https://mops.twse.com.tw/mops/web/t146sb05',
    }
    response = requests.post(url, json=payload, headers=headers)
    if "公司代號格式錯誤" not in response.text:
        output = ast.literal_eval(response.text)
        
        ####基本資料####
        tmp = output['result']['basic_info'] ##基本資料
        df_basic_info = pd.DataFrame(columns = tmp.keys())
        df_basic_info = pd.concat([df_basic_info, pd.DataFrame([tmp])], axis=0, ignore_index=True)
        # df_basic_info    
        ##插入資料
        # cn = pyodbc.connect("DRIVER={MySQL ODBC 5.1 Driver}; SERVER=主機名稱;DATABASE=資料庫名稱; UID=帳號; PASSWORD=密碼;OPTION=4;")
        insert_table = "insert into table_name1 values " + ",".join("('" + "','".join(row.astype("str")) + "')"  for row in df_basic_info.values)
        # print("基本資料:\n",insert_table)
        # cn.execute(insert_table)
        # cn.close
        ###############
        
        ####營收資訊####
        revenue_col_name = ['年份','月份','當月營收','去年當月營收','去年同月增減(%)','當月累計營收','去年累計營收','前期比較增減(%)','股票代碼']
        df_revenue_info = pd.DataFrame(columns = revenue_col_name)
        api_name = output['result']['revenue_information']['moreInfoUrl']['apiName'] ##財報資訊
        url2 = f"https://mops.twse.com.tw/mops/api/{api_name}"
        payload = {
            "company_id": stock_code
        }
        res_revenue = requests.post(url2, json=payload, headers=headers)
        output_revenue = ast.literal_eval(res_revenue.text)
        INFOs = output_revenue['result']['data']
        for info in INFOs:
            new_row_df = pd.DataFrame([info + [stock_code]],columns = revenue_col_name)
            df_revenue_info = pd.concat([df_revenue_info , new_row_df],ignore_index=True)
        ##插入資料
        # cn = pyodbc.connect("DRIVER={MySQL ODBC 5.1 Driver}; SERVER=主機名稱;DATABASE=資料庫名稱; UID=帳號; PASSWORD=密碼;OPTION=4;")
        insert_table = "insert into table_name2 values " + ",".join("('" + "','".join(row.astype("str")) + "')"  for row in df_revenue_info.values)
        # print("營收資訊:\n",insert_table)
        # cn.execute(insert_table)
        # cn.close
        ###############
        
        ####財報資訊####
        report_col_name = []
        filt_data = output['result']['financial_report_information']['titles']
        for data in filt_data:
            report_col_name.append(data['main'])
        report_col_name[0] = "項目"
        report_col_name.insert(0,"股票代碼")
        df_report_info = pd.DataFrame(columns = report_col_name)
    
        ITEMs = ['CAL','CCSI','CCFS']
        for item in ITEMs:
            contents = output['result']['financial_report_information'][item]
            for content in contents:
                content2 = [stock_code] + content
                new_row_df = pd.DataFrame([content2],columns = report_col_name)
                df_report_info = pd.concat([df_report_info,new_row_df], ignore_index=True)
    
        ##插入資料
        # cn = pyodbc.connect("DRIVER={MySQL ODBC 5.1 Driver}; SERVER=主機名稱;DATABASE=資料庫名稱; UID=帳號; PASSWORD=密碼;OPTION=4;")
        insert_table = "insert into table_name3 values " + ",".join("('" + "','".join(row.astype("str")) + "')"  for row in df_report_info.values)
        # print("財報資訊:\n",insert_table)
        # cn.execute(insert_table)
        # cn.close
        # print("="*70)
        print(f"======股票代碼 {stock_code} 執行完成。======")
    else:
        print(f"======股票代碼 {stock_code} 發生異常。======")
        time.sleep(0.2)