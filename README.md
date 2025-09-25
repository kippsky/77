## 电商多平台比价工具（淘宝/京东/小红书/抖音）

功能：
- 输入产品名称与关键信息，一键搜索淘宝、京东、小红书、抖音的店铺与价格
- 展示平台、标题、店铺名、价格、评论数、评分、销量等信息
- 支持按价格、评论数进行单一或多重对比排序
- 点击对比结果可查看店铺与产品详细信息

### 运行步骤
1. 安装依赖
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
2. 配置环境变量（可选，但推荐）：
```bash
export SERPAPI_KEY="your_serpapi_key"
```
3. 启动图形界面
```bash
python run.py
```

说明：
- 默认通过 SerpAPI 进行搜索聚合，未配置 `SERPAPI_KEY` 时会使用内置的安全降级逻辑（可能只返回部分/示例数据）。
- 本工具仅做公开网页信息聚合与展示，请遵守各平台服务条款与法律法规。

c3NyOi8vTVRjeUxqRXdOQzR4TWpjdU1qQTRPamd3T1RrNmIzSnBaMmx1T21GbGN5MHlOVFl0WTJaaU9uQnNZV2x1T2xwVmJGaE5SVkoxWVhwWk5VNUVWVEJhVkZwMVZUTmtNV016UWpKUFZWSjBWWHBKZDAxWVVsSk5SVkV2UDI5aVpuTndZWEpoYlQwCnNzcjovL01UY3lMakV3TkM0MU1DNHhNREk2T0RBNU9UcHZjbWxuYVc0NllXVnpMVEkxTmkxalptSTZjR3hoYVc0NldsVnNXRTFGVW5WaGVsazFUa1JWTUZwVVduVlZNMlF4WXpOQ01rOVZVblJWZWtsM1RWaFNVazFGVVM4X2IySm1jM0JoY21GdFBRCg==
