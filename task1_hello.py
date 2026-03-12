from playwright.sync_api import sync_playwright


def run():
    # 启动 Playwright
    with sync_playwright() as p:
        # 启动浏览器 (headless=False 表示显示浏览器界面，方便你看过程)
        browser = p.chromium.launch(headless=False)

        # 创建一个新页面
        page = browser.new_page()

        # 访问百度
        print("正在打开百度...")
        page.goto("https://www.baidu.com")

        # 等待页面加载完成 (可选，但推荐)
        page.wait_for_load_state("networkidle")

        # 截图保存
        print("正在截图...")
        page.screenshot(path="baidu_home.png")
        print("截图已保存为 baidu_home.png！")

        # 关闭浏览器
        browser.close()


if __name__ == "__main__":
    run()