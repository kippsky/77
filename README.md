## 多平台商品价格/评论对比助手（Python/Tkinter）

功能：输入产品名称与补充信息，聚合淘宝、京东、小红书、抖音等平台（演示数据），展示价格、评分、评论数；支持设置价格/评分/评论权重进行多重对比，点击行可查看详情并打开链接。

提示：当前适配器为可复用架构，默认使用可复现的“演示数据”（不依赖登录/反爬）。你可以替换各平台适配器中的 `search` 实现为真实抓取或 API 查询。

### 运行

1. 安装 Python 3.9+
2. 确保已安装 Tk 支持（Ubuntu/Debian: `sudo apt-get install -y python3-tk`）
3. 运行：

```bash
python -m app.main
```

### 目录结构

```
app/
  adapters/
    base.py
    taobao.py
    jd.py
    xiaohongshu.py
    douyin.py
  aggregator.py
  models.py
  main.py
```

### 扩展为真实数据

- 在 `app/adapters/*.py` 中实现真实的 `search(product_name, product_info)`，返回 `List[Offer]`
- 可选思路：
  - 调用平台开放 API（若有）
  - 站内检索页抓取（建议 Playwright/无头浏览器 + 登录 Cookie）
  - 第三方搜索引擎 site: 定位并抓取详情页

注意：电商平台通常有严格的反爬策略，请遵守平台条款与当地法律法规。

### 对比算法

对每条 Offer 计算综合得分：

```
score = w_price * (便宜程度) + w_rating * (评分归一化) + w_reviews * (评论数对数归一化)
```

权重可在界面上通过滑块设置，总和自动归一化。

c3NyOi8vTVRjeUxqRXdOQzR4TWpjdU1qQTRPamd3T1RrNmIzSnBaMmx1T21GbGN5MHlOVFl0WTJaaU9uQnNZV2x1T2xwVmJGaE5SVkoxWVhwWk5VNUVWVEJhVkZwMVZUTmtNV016UWpKUFZWSjBWWHBKZDAxWVVsSk5SVkV2UDI5aVpuTndZWEpoYlQwCnNzcjovL01UY3lMakV3TkM0MU1DNHhNREk2T0RBNU9UcHZjbWxuYVc0NllXVnpMVEkxTmkxalptSTZjR3hoYVc0NldsVnNXRTFGVW5WaGVsazFUa1JWTUZwVVduVlZNMlF4WXpOQ01rOVZVblJWZWtsM1RWaFNVazFGVVM4X2IySm1jM0JoY21GdFBRCg==
