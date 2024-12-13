import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from typing import Dict, List
import hashlib
import base64
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import platform
import os

class GetuiSpider:
    def __init__(self):
        print("开始初始化 GetuiSpider...")
        self.base_url = "https://dev.getui.com"
        self.session = requests.Session()
        self.token = None
        
        print("配置 Chrome 选项...")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 根据操作系统设置不同的配置
        system = platform.system().lower()
        print(f"当前操作系统: {system}")
        
        if system == 'darwin':  # MacOS
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
        elif system == 'linux':  # Linux (包括 CentOS)
            chrome_options.add_argument('--headless')  # Linux 服务器使用无头模式
            chrome_options.add_argument('--disable-gpu')
            chrome_path = '/usr/bin/google-chrome'
            if os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
        
        print("初始化 Chrome 驱动...")
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            # 设置 webdriver-manager 的日志级别
            os.environ['WDM_LOG_LEVEL'] = '0'
            os.environ['WDM_PRINT_FIRST_LINE'] = 'True'
            
            print("开始下载 ChromeDriver...")
            driver_path = ChromeDriverManager().install()
            print(f"ChromeDriver 下载完成，路径: {driver_path}")
            
            service = Service(driver_path)
            print("开始初始化浏览器...")
            
            start_time = time.time()
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            elapsed_time = time.time() - start_time
            print(f"Chrome 驱动初始化成功，耗时 {elapsed_time:.2f} 秒")
        except Exception as e:
            print(f"Chrome 驱动初始化失败: {str(e)}")
            print("详细错误信息:")
            import traceback
            print(traceback.format_exc())
            raise
        
        self.wait = WebDriverWait(self.driver, 10)
        print("GetuiSpider 初始化完成")
    
    def login(self, username: str, password: str) -> bool:
        """使用 Selenium 登录获取 token"""
        try:
            print(f"\n开始登录过程，访问 {self.base_url}/dev/")
            self.driver.get(f"{self.base_url}/dev/")
            print("页面加载完成")
            
            print("等待用户名输入框出现...")
            username_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            print("找到用户名输入框，输入用户名")
            username_input.send_keys(username)
            
            print("查找密码输入框...")
            password_input = self.driver.find_element(By.NAME, "password")
            print("找到密码输入框，输入密码")
            password_input.send_keys(password)
            
            print("查找登录按钮...")
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '登录')]")
            print("找到登录按钮，点击登录")
            login_button.click()
            
            print("等待登录成功...")
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            print("检测到 dashboard 元素，登录成功")
            
            print("获取 token...")
            self.token = self.driver.execute_script(
                "return localStorage.getItem('token')"
            )
            print(f"获取到 token: {self.token is not None}")
            
            print("同步 cookies...")
            for cookie in self.driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
            print("cookies 同步完成")
            
            return bool(self.token)
            
        except Exception as e:
            print(f"\n登录过程出现错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"当前 URL: {self.driver.current_url}")
            return False
        
    def __del__(self):
        """清理 Selenium driver"""
        if hasattr(self, 'driver'):
            print("关闭 Chrome 驱动...")
            try:
                self.driver.quit()
                print("Chrome 驱动已关闭")
            except Exception as e:
                print(f"关闭 Chrome 驱动时出错: {str(e)}")

    def get_app_list(self) -> List[Dict]:
        """获取应用列表"""
        url = f"{self.base_url}/dos-hz/appService/app/queryApplist"
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "token": self.token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"
        }
        data = {
            "pageSize": 100,
            "pageNum": 1,
            "orderBy": "createTime",
            "order": "desc"
        }
        
        try:
            response = self.session.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                return result.get("data", {}).get("list", [])
            return []
        except Exception as e:
            print(f"获取应用列表失败: {str(e)}")
            return []

def main():
    print("\n=== 开始运行爬虫程序 ===")
    try:
        spider = GetuiSpider()
        print("\n尝试登录...")
        if spider.login("hismartcar", "HS_Jdo@223"):
            print("\n登录成功，开始获取应用列表")
            app_list = spider.get_app_list()
            print(f"\n获取到 {len(app_list)} 个应用")
            for app in app_list:
                print(json.dumps(app, ensure_ascii=False, indent=2))
        else:
            print("\n登录失败")
    except Exception as e:
        print(f"\n程序运行出现错误:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")

if __name__ == "__main__":
    main()