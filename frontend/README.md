# tech-2-ai frontend

六个主页面对应后端六个功能模块，路由按需加载。共享组件仅包含运行信息、证据和任务进度。

```powershell
npm ci
npm run dev
npm test
npm run format:check
npm run build
```

默认使用 Vite `/api` 代理访问 `http://127.0.0.1:8000`。如已有 `.env.development`，其 `VITE_API_BASE_URL` 优先，可设为空使用代理。生产环境为同源部署或明确配置跨域地址。

普通请求统一在 `src/api/http.js`；SSE 协议解析独立测试。页面离开时中止前台请求和轮询；后台任务可以从工程页面继续查看或取消。所有模型文本使用 Vue 文本绑定，不直接渲染不可信 HTML。
