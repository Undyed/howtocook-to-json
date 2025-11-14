# 🍳 HowToCook 菜谱 JSON 转换器


[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

自动将 [HowToCook](https://github.com/Anduin2017/HowToCook) 项目的 Markdown 菜谱转换为结构化的 JSON 格式。

## ✨ 功能特性

- 🤖 每天自动拉取最新菜谱并生成 JSON
- 📊 包含菜谱名称、食材、步骤、难度等信息

## 🚀 快速开始

### 本地使用

```bash
# 1. 克隆本仓库
git clone https://github.com/YOUR_USERNAME/howtocook-to-json.git
cd howtocook-to-json

# 2. 克隆 HowToCook 仓库
git clone https://github.com/Anduin2017/HowToCook.git

# 3. 运行转换脚本
python convert_recipes.py

# 4. 查看生成的 JSON
cat target/all_recipes.json
```

### 直接使用数据

```bash
# 下载最新的 JSON 文件
curl -O https://raw.githubusercontent.com/Undyed/howtocook-to-json/main/target/all_recipes.json
```

## 📋 数据格式示例

```json
{
  "id": "dishes-aquatic-咖喱炒蟹",
  "name": "咖喱炒蟹的做法",
  "description": "第一次吃咖喱炒蟹是在泰国...",
  "category": "水产",
  "difficulty": 4,
  "ingredients": [
    {
      "name": "肉蟹",
      "quantity": 300,
      "unit": "g"
    }
  ],
  "steps": [
    {
      "step": 1,
      "description": "肉蟹掀盖后对半砍开..."
    }
  ],
  "image_path": "https://media.githubusercontent.com/..."
}
```

## 🤖 自动化

本项目使用 GitHub Actions 每天自动更新数据（北京时间 08:00）。


## 🙏 致谢

感谢 [HowToCook](https://github.com/Anduin2017/HowToCook) 项目提供的优质菜谱内容！
