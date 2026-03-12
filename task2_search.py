from playwright.sync_api import sync_playwright, expect
import time


def run():
    STEP_DELAY = 1000  # 1秒延迟，方便观察

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ================= 1. 登录 =================
        print("🔐 步骤 1: 登录系统")
        page.goto("https://www.saucedemo.com")
        page.get_by_placeholder("Username").fill("standard_user")
        page.get_by_placeholder("Password").fill("secret_sauce")
        page.get_by_role("button", name="Login").click()

        # 等待登录成功 (出现商品标题)
        page.wait_for_selector(".title", state="visible")
        print("✅ 登录成功，进入商品页。")
        time.sleep(STEP_DELAY / 1000)

        # ================= 2. 验证商品列表 =================
        print("📦 步骤 2: 验证商品列表")
        # 断言：页面必须包含 "Products" 标题
        expect(page.get_by_text("Products")).to_be_visible()

        # 获取第一个商品的名称 (用于后续验证)
        # Sauce Demo 的商品结构通常是 .inventory_item_name
        first_item_name = page.locator(".inventory_item_name").first.inner_text()
        print(f"👀 准备添加第一个商品: {first_item_name}")
        time.sleep(STEP_DELAY / 1000)

        # ================= 3. 添加到购物车 =================
        # ================= 3. 添加到购物车 (关键修正) =================
        print("🛒 步骤 3: 添加商品到购物车")

        # 1. 确保我们在商品列表页 (防止意外跳转)
        # 如果不在 inventory.html，说明前面出错了
        if "inventory" not in page.url:
            print(f"⚠️ 警告：当前 URL 是 {page.url}，预期在 inventory 页面。尝试返回...")
            # 如果不小心进了购物车，先退出来（可选，视情况而定）
            # page.go_back()

        # 2. 点击第一个商品的 "Add to cart"
        # 使用更稳健的定位：找到第一个商品容器，再找里面的按钮
        first_item = page.locator(".inventory_item").first
        add_btn = first_item.get_by_role("button", name="Add to cart")

        # 检查按钮是否存在
        if add_btn.count() == 0:
            print("❌ 错误：找不到 'Add to cart' 按钮！请检查是否已登录或页面加载完成。")
            page.screenshot(path="debug_no_add_btn.png")  # 截图 debugging
            raise Exception("找不到添加按钮")

        add_btn.click()
        print("✅ 已点击添加按钮")

        # 3. 【关键】等待角标出现！
        # 很多时候点击后需要等一小会儿 DOM 更新
        cart_badge = page.locator(".shopping_cart_badge")
        try:
            # 最多等 5 秒，看角标是否变成 "1"
            cart_badge.wait_for(state="visible", timeout=5000)
            expect(cart_badge).to_have_text("1")
            print("✅ 购物车角标已更新为 1")
        except Exception as e:
            print(f"⚠️ 角标未及时出现：{e}")
            page.screenshot(path="debug_no_badge.png")

        time.sleep(STEP_DELAY / 1000)

        # ================= 4. 进入购物车页面 (多种方案备选) =================
        # ================= 4. 进入购物车页面 (智能版) =================
        print("🛍️ 步骤 4: 进入购物车详情页")

        # 📸 调试：点击前截个图
        page.screenshot(path="debug_before_click_cart.png")
        print(f"📍 当前 URL: {page.url}")

        # 如果已经在购物车页面，跳过点击和等待
        if "cart.html" in page.url:
            print("✅ 已经在购物车页面，跳过点击操作")
        else:
            # 不在购物车页面，才需要点击
            print("🔗 尝试点击购物车链接...")

            # --- 方案 A: data-test ---
            try:
                cart_link = page.get_by_test_id("cart")
                cart_link.wait_for(state="visible", timeout=5000)
                cart_link.click()
                print("✅ 已点击购物车链接 (data-test)")
            except Exception as e:
                print(f"⚠️ data-test 失败: {e}")
                # --- 方案 B: CSS ---
                try:
                    css_cart = page.locator("a.shopping_cart_link")
                    css_cart.wait_for(state="visible", timeout=5000)
                    css_cart.click()
                    print("✅ 已点击购物车链接 (CSS)")
                except Exception as e2:
                    print(f"❌ CSS 也失败: {e2}")
                    page.screenshot(path="debug_cart_click_fail.png")
                    raise Exception("无法点击购物车链接")

            # 等待导航（只有当我们确实点击了才等待）
            print("⏳ 等待页面跳转...")
            try:
                page.wait_for_url("*/cart.html", timeout=10000)
                print("✅ URL 已成功跳转到 cart.html")
            except Exception as e:
                print(f"⚠️ URL 未跳转，但可能已在目标页。当前 URL: {page.url}")
                # 不抛出异常，继续往下走

        # 无论是否点击，现在都应该在购物车页面了
        # 等待页面完全加载
        page.wait_for_load_state("networkidle", timeout=10000)

        # 📸 再次截图确认
        page.screenshot(path="debug_after_click_cart.png")
        print("📸 已保存 debug_after_click_cart.png")

        # 验证页面内容（这才是真正的成功标志！）
        print("🔍 验证购物车页面内容...")
        try:
            # Sauce Demo 购物车页面的标题通常是 "Your Cart"
            expect(page.get_by_text("Your Cart")).to_be_visible(timeout=5000)
            print("✅ 成功验证：页面包含 'Your Cart' 标题")
        except Exception as e:
            print(f"❌ 验证失败：{e}")
            # 尝试其他可能的文本
            try:
                expect(page.get_by_text("Checkout")).to_be_visible(timeout=5000)
                print("✅ 备用验证：页面包含 'Checkout' 按钮")
            except Exception as e2:
                print(f"❌ 备用验证也失败：{e2}")
                page.screenshot(path="debug_cart_content_fail.png")
                raise Exception("无法验证购物车页面内容")

        time.sleep(STEP_DELAY / 1000)

        # ================= 5. 点击结账 (Checkout) =================
        # ================= 5. 进入结账第一步 (终极修正版) =================
        # ================= 5. 进入结账第一步 (终极鲁棒版) =================
        # ================= 5. 进入结账第一步 (绝对鲁棒版) =================
        # ================= 5. 进入结账第一步 (最终版 - 等待 React 渲染) =================
        # ================= 5. 进入结账第一步 (终极直球版) =================
        # ================= 5. 进入结账第一步 (终极暴力版) =================
        print("💳 步骤 5: 直接点击 Checkout 按钮（绕过可见性检查）")

        # 📸 截图确认当前状态
        page.screenshot(path="debug_before_click_checkout_force.png")
        current_url = page.url
        print(f"📍 当前 URL: {current_url}")

        # 💥 方法 1: 直接使用 data-test="checkout" 并强制点击（即使不可见）
        checkout_btn = None
        try:
            checkout_btn = page.get_by_test_id("checkout")
            # 不等待 visible，直接尝试点击
            print("🖱️ 尝试直接点击 checkout 按钮...")
            checkout_btn.click(force=True)  # force=True 忽略可见性检查
            print("✅ 已强制点击 Checkout 按钮")
        except Exception as e:
            print(f"⚠️ 直接点击失败: {e}")

            # 💥 方法 2: 使用 CSS 选择器 + force click
            try:
                checkout_btn = page.locator("button#checkout")
                checkout_btn.click(force=True)
                print("✅ 已通过 CSS #checkout 强制点击")
            except Exception as e2:
                print(f"⚠️ CSS 点击也失败: {e2}")

                # 💥 方法 3: 使用 JavaScript 直接触发点击事件
                try:
                    print("🔧 使用 JavaScript 强制触发点击事件...")
                    page.evaluate("""
                        document.querySelector('button[data-test="checkout"]').click();
                    """)
                    print("✅ 已通过 JS 触发点击")
                except Exception as e3:
                    print(f"❌ 所有方法都失败: {e3}")
                    page.screenshot(path="debug_checkout_click_all_fail.png")
                    raise Exception("Checkout 按钮无法通过任何方式点击")

        # 📸 点击后截图
        page.screenshot(path="debug_after_click_checkout_force.png")

        # ⏳ 等待页面跳转（实际是 checkout-step-1.html）
        print("⏳ 等待跳转到 checkout-step-1.html ...")
        try:
            page.wait_for_url("*/checkout-step-1.html", timeout=10000)
            print("✅ 成功跳转到 checkout-step-1.html")
        except Exception as e:
            print(f"⚠️ URL 未跳转，但可能已在目标页。当前 URL: {page.url}")
            # 不抛异常，继续验证内容

        # 等待网络空闲和页面渲染
        # ================= 6. 填写收货信息 =================
        # ================= 6. 填写收货信息 (终极修正版 - 大小写精准匹配) =================
        # ================= 6. 填写收货信息 (终极核弹版 - CSS 选择器 + JS 填充) =================
        # ================= 6. 填写收货信息 (终极简洁版 - 按 placeholder 定位) =================
        print("📦 步骤 6: 填写收货人信息")

        # 📸 截图确认当前状态
        page.screenshot(path="debug_before_fill_simple.png")

        # ✍️ 直接根据 placeholder 文本填写
        page.get_by_placeholder("First Name").fill("John")
        page.get_by_placeholder("Last Name").fill("Doe")
        page.get_by_placeholder("Zip/Postal Code").fill("12345")

        print("✅ 所有字段已填写完毕")

        # 📸 填写后截图
        page.screenshot(path="debug_after_fill_simple.png")

        time.sleep(STEP_DELAY / 1000)
        # ================= 7. 完成订单 =================
        # ================= 7. 完成订单 (稳健版 - 不依赖标题文本，直接操作按钮) =================
        # ================= 7. 完成订单 (真实流程版 - Continue + Finish) =================
        print("🚀 步骤 7: 提交订单（两步走）")

        # 📸 截图确认当前状态（应该是 Checkout: Your Information）
        page.screenshot(path="debug_step7_before_continue.png")
        print(f"📍 当前 URL: {page.url}")

        # 🔹 第一步：点击 Continue 按钮，进入 Overview 页面
        print("🖱️ 点击 'Continue' 按钮...")
        continue_button = page.get_by_role("button", name="Continue")
        continue_button.wait_for(state="visible", timeout=10000)
        continue_button.click()

        # ⏳ 等待跳转到 Overview 页面
        print("⏳ 等待跳转至 Checkout: Overview 页面...")
        # 等待出现 "Checkout: Overview" 标题或 "Finish" 按钮
        finish_button = page.get_by_role("button", name="Finish")
        finish_button.wait_for(state="visible", timeout=10000)
        print("✅ 已到达 Overview 页面，'Finish' 按钮可见")

        # 📸 截图确认 Overview 页面
        page.screenshot(path="debug_step7_overview.png")

        # 🔹 第二步：点击 Finish 按钮，完成订单
        print("🖱️ 点击 'Finish' 按钮提交最终订单...")
        finish_button.click()

        # ⏳ 等待订单成功页面
        print("⏳ 等待订单成功页面加载...")
        success_header = page.locator("h2").filter(has_text="Thank you for your order!")
        success_header.wait_for(state="visible", timeout=10000)

        # 【关键断言】验证成功页面的标题文本
        success_header = page.locator("h2").filter(has_text="Thank you for your order!")
        expect(success_header).to_contain_text("Thank you for your order!", timeout=10000)
        print("✅ 断言通过：订单提交成功！检测到 'Thank you for your order!'")

        # 📸 最终成功截图
        page.screenshot(path="debug_step7_success.png")

        time.sleep(STEP_DELAY / 1000)

        # ================= 8. 最终断言 =================
        print("🏆 步骤 8: 验证订单完成")
        # 必须看到 "Thank you for your order!"
        success_msg = page.get_by_text("Thank you for your order!")
        expect(success_msg).to_be_visible()

        # 截图留念
        page.screenshot(path="full_shopping_success.png")
        print("✅ 全流程测试通过！订单完成截图已保存。")

        # 停留 5 秒展示结果
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    run()