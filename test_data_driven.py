import pytest
import json
from playwright.sync_api import sync_playwright, expect


# 1. 读取 JSON 数据
def load_users():
    with open("test_users.json", "r", encoding="utf-8") as f:
        return json.load(f)


# 2. 定义参数化装饰器
# 这行代码会让 pytest 自动为 JSON 里的每一条数据运行一次 test_shopping_flow
@pytest.mark.parametrize("user", load_users())
def test_shopping_flow(user, page):
    """
    数据驱动的购物流程测试
    :param user: 从 JSON 注入的用户字典
    :param page: pytest-playwright 自动注入的 page 对象
    """
    print(f"\n🚀 开始测试用户: {user['id']} ({user['username']})")

    # --- 步骤 1: 登录 ---
    page.goto("https://www.saucedemo.com")
    page.get_by_placeholder("Username").fill(user["username"])
    page.get_by_placeholder("Password").fill(user["password"])
    page.get_by_role("button", name="Login").click()

    # 处理登录失败的情况 (比如 locked_out_user)
    error_msg = page.locator("[data-test='error']")
    if error_msg.is_visible():
        msg_text = error_msg.inner_text()
        print(f"❌ 用户 {user['id']} 登录失败: {msg_text}")
        # 断言：如果是预期会失败的账号，这里可以写特定逻辑
        # 如果这不是预期失败，则抛出异常让测试标记为 FAILED
        assert "locked out" in msg_text.lower(), f"意外错误: {msg_text}"
        return  # 登录失败，直接结束当前用例，不往下跑

    print("✅ 登录成功")
    expect(page.get_by_text("Products")).to_be_visible()

    # --- 步骤 2: 加购 ---
    first_item = page.locator(".inventory_item").first
    first_item.get_by_role("button", name="Add to cart").click()

    # 等待角标
    expect(page.locator(".shopping_cart_badge")).to_have_text("1")

    # --- 步骤 3: 进入购物车 ---
    page.get_by_test_id("cart").click()
    page.get_by_test_id("checkout").click()

    # --- 步骤 4: 填写信息 (使用动态数据) ---
    page.get_by_placeholder("First Name").fill(user["first_name"])
    page.get_by_placeholder("Last Name").fill(user["last_name"])
    page.get_by_placeholder("Zip/Postal Code").fill(user["zip"])

    page.get_by_role("button", name="Continue").click()
    page.get_by_role("button", name="Finish").click()

    # --- 步骤 5: 验证结果 ---
    expect(page.get_by_text("Thank you for your order!")).to_be_visible()

    # 截图：用用户ID命名，方便区分
    page.screenshot(path=f"result_{user['id']}.png")
    print(f"📸 用户 {user['id']} 测试完成，截图已保存。")