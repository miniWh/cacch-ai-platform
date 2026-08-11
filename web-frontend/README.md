# CACCH AI Frontend

平台工作台前端（Vue 3 + Vite + TypeScript + Element Plus）。

统一工作台入口：顶栏 Logo（泰禾集团 / CAC GROUP）+ 动态左侧菜单；含 **对话台**、**站点清单**（Mock，未接后端）。

## 开发

```bash
cd web-frontend
npm install
npm run dev
```

浏览器打开控制台提示的本地地址（默认 `http://localhost:5173`）。

## 页面

| 路由 | 页面 |
| :--- | :--- |
| `/chat` | AI 对话台 |
| `/sites` | 站点清单（已对接后端 `/api/v1/rag/kb/{kb_id}/sources`） |
| `/documents` | 文档与任务（占位） |
| `/settings` | 应用配置（占位） |
| `/menus` | 菜单管理（显示/隐藏、排序、重命名） |

## 目录

```text
src/
  components/     # 顶栏、侧栏
  layouts/        # 工作台布局
  mock/           # 测试数据
  views/          # 页面
  router/
  styles/
```

对接后端时，将 `src/mock/data.ts` 替换为 API 调用即可。
