from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from downloader.base import BaseSource


class ChromeDriverNotInstalled(Exception):
    def __init__(self):
        super().__init__("ChromeDriver is not installed")


class MediafireLinkNotFound(Exception):
    def __init__(self):
        super().__init__("Mediafire download link not found")


class MediafireSource(BaseSource):
    def download(self, url: str, path: str) -> None:
        download_link = self.get_download_link(url)

        self.manager.direct_download(download_link, path)

    def is_valid(self, url: str) -> bool:
        return "mediafire.com/file/" in url

    def setup_driver():
        chrome_options = Options()
        # Add arguments to make headless mode more similar to regular browser
        chrome_options.add_argument("--headless=new")  # New headless implementation
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Add window size to ensure elements are visible
        chrome_options.add_argument("--window-size=1920,1080")

        # Add user agent to appear more like a regular browser
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Additional headers to bypass basic detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # Create driver with options
        driver = webdriver.Chrome(options=chrome_options)

        # Mask webdriver presence
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return driver

    def get_download_link(url):
        try:
            driver = MediafireSource.setup_driver()

            # Open the page
            driver.get(url)

            # Use explicit wait instead of implicit wait
            wait = WebDriverWait(driver, 20)

            # Wait for the download button to be present and clickable
            download_element = wait.until(
                EC.presence_of_element_located((By.ID, "downloadButton"))
            )

            # Get the href attribute
            download_link = download_element.get_attribute("href")
            return download_link

        except WebDriverException:
            raise ChromeDriverNotInstalled()

        except TimeoutException:
            raise MediafireLinkNotFound()

        finally:
            driver.quit()
