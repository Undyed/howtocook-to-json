# 🍳 HowToCook 菜谱 JSON 转换器

[![Build Recipe JSON](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build-recipes.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build-recipes.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

自动将 [HowToCook](https://github.com/Anduin2017/HowToCook) 项目的 Markdown 菜谱转换为结构化的 JSON 格式，方便开发者在各种应用中使用。

## ✨ 功能特性

- 🤖 **自动化构建**: 每天自动拉取最新菜谱并生成 JSON（北京时间 08:00）
- 📊 **结构化数据**: 包含菜谱名称、食材、步骤、难度、分类等完整信息
- 🖼️ **图片链接**: 自动生成 GitHub Media URL 格式的图片链接，可直接访问
- 🏷️ **智能分类**: 按水产、荤菜、素菜、主食、早餐、汤、饮品、甜点等 10 大分类
- 📈 **统计报告**: 自动生成构建报告和详细的分类统计信息
- 🔍 **智能解析**: 自动识别食材数量、单位，支持多种格式
- 🌐 **多语言支持**: 完整的中文支持，适合国内开发者使用

## 📋 数据格式

生成的 JSON 文件包含以下字段：

```json
{
  "id": "dishes-aquatic-咖喱炒蟹",
  "name": "咖喱炒蟹的做法",
  "description": "第一次吃咖喱炒蟹是在泰国的建兴酒家...\n\n预估烹饪难度：★★★★",
  "source_path": "aquatic/咖喱炒蟹.md",
  "image_path": "https://media.githubusercontent.com/media/Anduin2017/HowToCook/refs/heads/master/dishes/aquatic/%E5%92%96%E5%96%B1%E7%82%92%E8%9F%B9.jpg",
  "category": "水产",
  "difficulty": 4,
  "tags": ["水产"],
  "servings": 1,
  "ingredients": [
    {
      "name": "肉蟹",
      "quantity": 300,
      "unit": "g",
      "text_quantity": "300 g",
      "notes": null
    },
    {
      "name": "咖喱块",
      "quantity": 15,
      "unit": "g",
      "text_quantity": "15 g",
      "notes": null
    }
  ],
  "steps": [
    {
      "step": 1,
      "description": "肉蟹掀盖后对半砍开，蟹钳用刀背轻轻拍裂..."
    },
    {
      "step": 2,
      "description": "洋葱切成洋葱碎，备用"
    }
  ],
  "prep_time_minutes": null,
  "cook_time_minutes": null,
  "total_time_minutes": null,
  "additional_notes": [
    "做法参考：[十几年澳门厨房佬教学挂汁的咖喱蟹怎么做](https://www.bilibili.com/video/BV1Nq4y1W7K9)",
    "如果您遵循本指南的制作流程而发现有问题或可以改进的流程，请提出 Issue 或 Pull request 。"
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识符，格式：`dishes-{分类}-{菜名}` |
| `name` | string | 菜谱名称 |
| `description` | string | 菜谱描述和难度说明 |
| `source_path` | string | 源 Markdown 文件路径 |
| `image_path` | string \| null | 菜谱图片 URL（GitHub Media 格式） |
| `category` | string | 菜谱分类（水产、荤菜、素菜等） |
| `difficulty` | number | 烹饪难度（1-5 星） |
| `tags` | array | 标签列表 |
| `servings` | number | 份数 |
| `ingredients` | array | 食材列表 |
| `steps` | array | 烹饪步骤 |
| `prep_time_minutes` | number \| null | 准备时间（分钟） |
| `cook_time_minutes` | number \| null | 烹饪时间（分钟） |
| `total_time_minutes` | number \| null | 总时间（分钟） |
| `additional_notes` | array | 附加说明和参考链接 |

## 🚀 快速开始

### 前置要求

- Python 3.11 或更高版本
- Git

### 本地使用

1. **克隆本仓库**：
```bash
git clone https://github.com/YOUR_USERNAME/howtocook-to-json.git
cd howtocook-to-json
```

2. **克隆 HowToCook 仓库**：
```bash
git clone https://github.com/Anduin2017/HowToCook.git
```

3. **运行转换脚本**：
```bash
python convert_recipes.py
```

脚本会自动：
- 🔍 检测 HowToCook 目录位置
- 📖 解析所有菜谱 Markdown 文件
- 🏗️ 生成结构化 JSON 数据
- 💾 保存到 `target/all_recipes.json`

4. **查看生成的 JSON 文件**：
```bash
# 查看文件大小和基本信息
ls -lh target/all_recipes.json

# 查看前几行
head -n 50 target/all_recipes.json

# 使用 jq 格式化查看（如果已安装）
cat target/all_recipes.json | jq '.[0]'
```

### 直接使用生成的数据

如果你只想使用数据而不想自己构建，可以直接从本仓库下载：

```bash
# 下载最新的 JSON 文件
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/howtocook-to-json/main/target/all_recipes.json
```

## 🤖 GitHub Actions 自动化

本项目配置了完整的 CI/CD 流程，无需手动维护：

### 自动化功能

- ⏰ **定时运行**: 每天 UTC 00:00（北京时间 08:00）自动执行
- �  **自动拉取**: 从 HowToCook 仓库获取最新菜谱数据
- 🏗️ **自动构建**: 解析并生成最新的 JSON 文件
- 📤 **自动提交**: 检测到变化时自动提交到仓库
- 📊 **构建报告**: 生成详细的统计报告和分类信息
- 🔔 **失败通知**: 构建失败时自动通知

### 工作流触发条件

1. **定时触发**: 每天自动运行
2. **代码推送**: 当 `convert_recipes.py` 或工作流文件被修改时
3. **手动触发**: 随时可以手动运行

### 手动触发步骤

1. 访问你的 GitHub 仓库
2. 点击顶部的 **"Actions"** 标签
3. 在左侧选择 **"Build Recipe JSON"** 工作流
4. 点击右上角的 **"Run workflow"** 按钮
5. 选择分支（通常是 `main`）
6. 点击绿色的 **"Run workflow"** 确认

### 查看构建结果

每次构建完成后，你可以：
- 📊 查看详细的构建报告（包含菜谱数量、分类统计等）
- 📝 查看构建日志
- ✅ 确认数据是否更新成功

### 工作流配置

工作流文件位于 `.github/workflows/build-recipes.yml`，你可以根据需要自定义：

```yaml
# 修改运行时间（cron 表达式）
schedule:
  - cron: '0 0 * * *'  # 每天 00:00 UTC

# 修改 Python 版本
python-version: '3.11'
```

## 📁 项目结构

```
howtocook-to-json/
├── .github/
│   └── workflows/
│       └── build-recipes.yml    # GitHub Actions 自动化工作流
├── docs/
│   ├── pics.md                  # 图片格式说明文档
│   └── usage-example.md         # 详细使用示例和代码
├── target/
│   └── all_recipes.json         # 生成的 JSON 数据文件（332 个菜谱）
├── HowToCook/                   # HowToCook 仓库（需要克隆）
│   └── dishes/                  # 菜谱源文件目录
├── convert_recipes.py           # 核心转换脚本
├── .gitignore                   # Git 忽略配置
└── README.md                    # 项目说明文档（本文件）
```

### 核心文件说明

- **`convert_recipes.py`**: 主转换脚本，负责解析 Markdown 并生成 JSON
- **`target/all_recipes.json`**: 最终生成的数据文件，可直接使用
- **`.github/workflows/build-recipes.yml`**: CI/CD 配置，实现自动化构建

## 💡 使用场景

这个 JSON 数据可以用于：

- 📱 **移动应用**: 作为菜谱 App 的数据源
- 🌐 **网站开发**: 构建在线菜谱网站
- 🤖 **聊天机器人**: 实现菜谱推荐和查询功能
- 📊 **数据分析**: 分析菜谱趋势、食材使用频率等
- 🔍 **搜索引擎**: 构建菜谱搜索和推荐系统
- 📖 **电子书**: 生成电子菜谱书
- 🎓 **学习项目**: 作为数据源练习前后端开发

查看 [`docs/usage-example.md`](docs/usage-example.md) 获取详细的代码示例。

## 🔧 技术栈

- **Python 3.11+**: 核心开发语言
- **正则表达式**: Markdown 解析
- **JSON**: 数据格式
- **GitHub Actions**: CI/CD 自动化
- **Git**: 版本控制

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 报告问题

如果发现菜谱解析有问题，请提交 Issue 并包含：

1. 📝 具体的菜谱名称或 ID
2. ❌ 当前的错误结果
3. ✅ 期望的正确结果
4. 💡 如果可能，提供修复建议

### 提交代码

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发建议

- 遵循 PEP 8 Python 代码规范
- 添加必要的注释和文档
- 测试你的更改
- 更新相关文档

## 📝 更新日志

### v1.0.0 (2024-01-XX)

- ✨ 初始版本发布
- 🤖 实现 GitHub Actions 自动化构建
- 📊 支持 332 个菜谱的完整解析
- 🖼️ 自动生成图片链接
- 📈 生成详细的统计报告

## ⚠️ 注意事项

1. **数据来源**: 所有菜谱数据来自 [HowToCook](https://github.com/Anduin2017/HowToCook) 项目
2. **更新频率**: 数据每天自动更新一次
3. **图片链接**: 图片链接指向 GitHub，需要网络访问
4. **数据准确性**: 解析结果可能存在误差，使用时请注意验证
5. **版权说明**: 菜谱内容版权归原作者所有

## 📄 许可证

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 开源协议。

菜谱内容版权归 [HowToCook](https://github.com/Anduin2017/HowToCook) 项目所有。

## 🙏 致谢

- 感谢 [HowToCook](https://github.com/Anduin2017/HowToCook) 项目提供的优质菜谱内容
- 感谢所有贡献者的支持和帮助
- 感谢开源社区的无私分享

## 📮 联系方式

- 💬 提交 Issue: [GitHub Issues](https://github.com/YOUR_USERNAME/howtocook-to-json/issues)
- 📧 邮件联系: your.email@example.com
- 🌟 如果这个项目对你有帮助，请给个 Star！

---

<div align="center">
  <sub>Built with ❤️ by developers, for developers</sub>
</div>
