#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recipe Markdown to JSON Converter
将 HowToCook 菜谱的 Markdown 文件转换为结构化的 JSON 格式
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class RecipeParser:
    """
    菜谱解析器类
    用于解析 Markdown 格式的菜谱文件并转换为结构化数据
    """
    
    # 目录结构到中文分类的映射
    CATEGORY_MAP = {
        'aquatic': '水产',
        'breakfast': '早餐',
        'condiment': '调味料',
        'dessert': '甜点',
        'drink': '饮品',
        'meat_dish': '荤菜',
        'semi-finished': '半成品',
        'soup': '汤',
        'staple': '主食',
        'vegetable_dish': '素菜',
        'template': '模板'
    }
    
    # 数量匹配正则表达式：匹配数字+单位的组合
    # 例如：100g, 2个, 3勺, 500ml 等
    QUANTITY_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*('  # 匹配数字（整数或小数）
        r'g|kg|mg|ml|l|L|斤|两|钱|克|千克|毫克|毫升|升|'  # 重量和容量单位
        r'个|只|片|根|瓣|颗|块|勺|匙|小勺|大勺|汤勺|茶勺|撮|粒|朵|条|段|杯|碗|锅|人|份|份数|cm|厘米|mm|毫米|米|寸|滴|包|袋|盒|瓶|罐|棵|头|尾'  # 计数单位
        r')',
        re.IGNORECASE
    )
    
    # 定性描述关键词：用于识别非精确数量的描述
    # 例如："适量"、"少许" 等
    QUALITATIVE_KEYWORDS = (
        '适量', '少许', '若干', '适当', '随意', '按口味', '酌情', '适量即可',
        '足量', '少量', '充足', '适量/按口味', '适量（按口味）'
    )
    
    def __init__(self, base_path: str):
        """
        初始化解析器
        
        Args:
            base_path: HowToCook 仓库的根目录路径
        """
        self.base_path = Path(base_path)
    
    def _strip_parenthetical(self, text: str) -> Tuple[str, List[str]]:
        """
        移除文本中的括号内容，同时收集括号中的注释
        
        Args:
            text: 待处理的文本
            
        Returns:
            (清理后的文本, 括号中的注释列表)
            
        Example:
            "鸡蛋（2个）" -> ("鸡蛋", ["2个"])
        """
        if not text:
            return '', []
        
        notes: List[str] = []
        
        def replacer(match):
            """替换函数：收集括号内容并返回空字符串"""
            inner = match.group(1).strip()
            if inner:
                notes.append(inner)
            return ''
        
        # 匹配中英文括号及其内容
        cleaned = re.sub(r'[（(]([^（）()]+)[）)]', replacer, text)
        return cleaned.strip(), notes
    
    def _split_name_quantity(self, text: str) -> Tuple[str, str]:
        """
        将食材行拆分为名称和数量两部分
        
        Args:
            text: 食材文本，例如 "鸡蛋：2个" 或 "盐 适量"
            
        Returns:
            (食材名称, 数量描述)
            
        处理多种格式：
        1. 冒号分隔：鸡蛋：2个
        2. 等号分隔：鸡蛋=2个
        3. 数字前分割：鸡蛋2个
        4. 定性关键词：盐适量
        """
        if not text:
            return '', ''
        
        # Prefer colon style separators (常见格式：原料: 数量)
        for sep in ('：', ':'):
            if sep in text:
                parts = text.split(sep, 1)
                return parts[0].strip(), parts[1].strip()
        
        # Fallback to equals sign
        if '=' in text:
            parts = text.split('=', 1)
            return parts[0].strip(), parts[1].strip()
        
        # Split before the first digit so we can keep textual quantity
        digit_match = re.search(r'(?<![A-Za-z])(\d+(?:\.\d+)?)', text)
        if digit_match:
            idx = digit_match.start()
            return text[:idx].strip(), text[idx:].strip()
        
        # Handle qualitative keywords such as “适量”
        keyword_pattern = r'(.+?)\s*(' + '|'.join(map(re.escape, self.QUALITATIVE_KEYWORDS)) + r')\)?$'
        keyword_match = re.search(keyword_pattern, text)
        if keyword_match:
            return keyword_match.group(1).strip(), keyword_match.group(2).strip()
        
        return text.strip(), ''
    
    def _create_ingredient_entry(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        从单行文本创建食材字典
        
        Args:
            raw_text: 原始食材文本行
            
        Returns:
            食材字典，包含名称、数量、单位、文本数量、备注等字段
            如果无法解析则返回 None
            
        Example:
            "鸡蛋（土鸡蛋）：2个" -> {
                'name': '鸡蛋',
                'quantity': 2.0,
                'unit': '个',
                'text_quantity': '2个',
                'notes': '土鸡蛋'
            }
        """
        text = raw_text.strip()
        # 跳过空行或分隔线
        if not text or re.fullmatch(r'[-*_]{2,}', text):
            return None
        
        # 分割名称和数量
        name_part, quantity_part = self._split_name_quantity(text)
        quantity_display = quantity_part
        quantity_search = quantity_part or text
        
        # 处理数量部分中的等号（如：2个=200g）
        if '=' in quantity_part:
            left, right = quantity_part.split('=', 1)
            if left.strip():
                quantity_display = left.strip()
            quantity_search = right.strip() or left.strip() or quantity_part
        
        # 提取括号中的注释
        name_clean, name_notes = self._strip_parenthetical(name_part)
        quantity_display, quantity_notes = self._strip_parenthetical(quantity_display)
        
        # 使用正则表达式提取数值和单位
        quantity_match = self.QUANTITY_PATTERN.search(quantity_search) or self.QUANTITY_PATTERN.search(text)
        quantity_value = float(quantity_match.group(1)) if quantity_match else None
        unit = quantity_match.group(2) if quantity_match else None
        
        # 合并所有注释
        notes = [note for note in name_notes + quantity_notes if note]
        notes_text = '；'.join(notes) if notes else None
        
        # 构建食材字典
        ingredient = {
            'name': name_clean.strip('：:=') if name_clean else None,
            'quantity': quantity_value,
            'unit': unit,
            'text_quantity': quantity_display if quantity_display else None,
            'notes': notes_text
        }
        
        # 验证食材名称存在
        if ingredient['name']:
            # 如果没有任何数量信息，添加提示
            if ingredient['text_quantity'] is None and ingredient['quantity'] is None and not ingredient['notes']:
                ingredient['notes'] = '量未指定'
            return ingredient
        
        return None
        
    def parse_difficulty(self, content: str) -> int:
        """
        从内容中提取烹饪难度等级
        
        Args:
            content: Markdown 文件内容
            
        Returns:
            难度等级（星级数量），默认为 1
            
        Example:
            "预估烹饪难度：★★★" -> 3
        """
        match = re.search(r'预估烹饪难度：(★+)', content)
        if match:
            return len(match.group(1))
        return 1
    
    def parse_servings(self, content: str) -> int:
        """
        从内容中提取份数
        
        Args:
            content: Markdown 文件内容
            
        Returns:
            份数，默认为 1
        """
        # 默认为 1 份
        return 1
    
    def parse_ingredients(self, content: str) -> List[Dict[str, Any]]:
        """
        解析食材清单部分
        
        Args:
            content: Markdown 文件内容
            
        Returns:
            食材字典列表
            
        处理逻辑：
        1. 优先查找 "## 计算" 部分（更具体的食材列表）
        2. 如果没有，则查找 "## 必备原料和工具" 部分
        3. 解析每一行食材，支持多种格式
        """
        ingredients = []
        
        # 优先查找 "计算" 部分（更精确的食材列表）
        match = re.search(r'##\s*计算(.*?)(?=^##(?!#)|\Z)', content, re.DOTALL | re.MULTILINE)
        
        # 如果没有 "计算" 部分，尝试 "必备原料和工具"
        if not match:
            match = re.search(r'##\s*必备原料和工具(.*?)(?=^##(?!#)|\Z)', content, re.DOTALL | re.MULTILINE)
        
        if not match:
            return ingredients
        
        ingredient_text = match.group(1)
        
        # 逐行解析食材
        for line in ingredient_text.split('\n'):
            line = line.strip()
            # 只处理列表项（以 -、* 或 + 开头）
            if not line or (line[0] not in '-*+'):
                continue
            
            # 移除列表标记
            line = re.sub(r'^[-*+]\s*', '', line)
            
            # 跳过注释和警告行
            if line.startswith('注：') or line.startswith('注意') or line.startswith('WARNING'):
                continue
            
            # 处理用顿号或逗号分隔的多个食材（如：盐、糖、味精）
            multi_sep = ('、' in line or '，' in line)
            has_numeric = bool(re.search(r'\d', line))
            has_special_sep = any(sep in line for sep in ('=', ':', '：', '*'))
            
            # 只有在没有数字和特殊分隔符时，才按顿号/逗号分割
            if multi_sep and not has_numeric and not has_special_sep:
                items = [item.strip() for item in re.split(r'[、，]', line) if item.strip()]
                for item in items:
                    ingredient = self._create_ingredient_entry(item)
                    if ingredient:
                        ingredients.append(ingredient)
                continue
            
            # 正常解析单个食材
            ingredient = self._create_ingredient_entry(line)
            if ingredient:
                ingredients.append(ingredient)
        
        return ingredients
    
    def parse_steps(self, content: str) -> List[Dict[str, Any]]:
        """
        解析烹饪步骤部分
        
        Args:
            content: Markdown 文件内容
            
        Returns:
            步骤字典列表，每个步骤包含序号和描述
            
        支持的标题格式：
        - ## 计算和操作
        - ## 操作
        - ## 操作步骤
        - ## 操作流程
        - ## 做法
        - ## 步骤
        """
        steps = []
        
        # 查找步骤部分（尝试多种可能的标题）
        step_sections = ['计算和操作', '操作', '操作步骤', '操作流程', '做法', '步骤']
        match = None
        for heading in step_sections:
            pattern = rf'##\s*{heading}(.*?)(?=^##(?!#)|\Z)'
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                break
        
        if not match:
            return steps
        
        steps_text = match.group(1)
        
        # 逐行解析步骤
        step_num = 1
        for line in steps_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            description = ''
            # 处理列表格式（- 或 * 或 + 开头）
            if line and line[0] in '-*+':
                description = re.sub(r'^[-*+]\s*', '', line).strip()
            else:
                # 处理数字编号格式（1. 或 1) 或 1、）
                number_match = re.match(r'^\d+[.)、]?\s*(.*)', line)
                if number_match:
                    description = number_match.group(1).strip()
            
            if not description:
                continue
            
            if description:
                steps.append({
                    'step': step_num,
                    'description': description
                })
                step_num += 1
        
        return steps
    
    def parse_notes(self, content: str) -> List[str]:
        """
        解析附加说明和注意事项
        
        Args:
            content: Markdown 文件内容
            
        Returns:
            注意事项列表
            
        查找逻辑：
        1. 优先查找 "## 附加内容" 部分
        2. 如果没有，尝试从步骤部分后提取
        """
        notes = []
        
        # 查找附加内容部分（通常在文件末尾）
        match = re.search(r'##\s*附加内容(.*?)(?=^##(?!#)|\Z)', content, re.DOTALL | re.MULTILINE)
        if not match:
            # 尝试从步骤部分后查找内容
            match = re.search(r'##\s*(?:计算和操作|操作)(.*?)(?=^##(?!#)|\Z)', content, re.DOTALL | re.MULTILINE)
        
        if match:
            notes_text = match.group(1)
            for line in notes_text.split('\n'):
                line = line.strip()
                # 提取列表项或特定格式的注释
                if line and (line.startswith('-') or line.startswith('*') or line.startswith('如果您遵循')):
                    notes.append(line)
        
        return notes
    
    def extract_description(self, content: str) -> str:
        """
        从内容中提取菜谱描述
        
        Args:
            content: Markdown 文件内容
            
        Returns:
            菜谱描述文本
            
        提取逻辑：
        1. 获取标题（# 标题）和第一个二级标题（## 标题）之间的内容
        2. 如果描述中没有包含难度信息，则追加难度信息
        """
        # 获取第一个 ## 标题之前的内容
        match = re.match(r'#[^#].*?\n\n(.*?)(?=##)', content, re.DOTALL)
        if match:
            desc = match.group(1).strip()
            # 如果存在难度信息，确保包含在描述中
            difficulty_match = re.search(r'预估烹饪难度：(★+)', content)
            if difficulty_match:
                if not desc.endswith(difficulty_match.group(0)):
                    desc += f"\n\n{difficulty_match.group(0)}"
            return desc
        return ""
    
    def parse_recipe_file(self, file_path: Path, relative_path: Path) -> Optional[Dict[str, Any]]:
        """
        解析单个菜谱 Markdown 文件
        
        Args:
            file_path: 文件的绝对路径
            relative_path: 相对于 dishes 目录的路径
            
        Returns:
            菜谱字典，包含所有解析的信息；解析失败返回 None
            
        处理流程：
        1. 读取文件内容
        2. 提取标题
        3. 生成唯一 ID
        4. 确定分类
        5. 查找配图
        6. 解析各个部分（食材、步骤、注意事项等）
        7. 组装成完整的菜谱字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题（使用 search 而不是 match 以处理前导空白）
            title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
            if not title_match:
                return None
            
            title = title_match.group(1).strip()
            
            # 从路径生成唯一 ID（添加 "dishes" 前缀）
            relative_str = relative_path.as_posix()
            recipe_id = 'dishes-' + relative_str.replace('/', '-').replace('.md', '')
            
            # 从路径确定分类
            parts = relative_path.parts
            category = self.CATEGORY_MAP.get(parts[0], parts[0]) if len(parts) > 0 else '未分类'
            
            # 查找配图并生成 GitHub media URL
            image_path = None
            image_dir = file_path.parent
            for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                # 检查与 Markdown 文件同名的图片
                img_file = image_dir / (file_path.stem + ext)
                if img_file.exists():
                    # 生成 GitHub media URL 并进行 URL 编码
                    relative_img_path = str(relative_path.parent / img_file.name).replace('\\', '/')
                    # URL 编码路径
                    from urllib.parse import quote
                    encoded_path = quote(relative_img_path, safe='/')
                    image_path = f"https://media.githubusercontent.com/media/Anduin2017/HowToCook/refs/heads/master/dishes/{encoded_path}"
                    break
                # 检查常见的图片名称
                for common_name in ['成品', '完成', title.replace('的做法', '')]:
                    img_file = image_dir / (common_name + ext)
                    if img_file.exists():
                        relative_img_path = str(relative_path.parent / img_file.name).replace('\\', '/')
                        from urllib.parse import quote
                        encoded_path = quote(relative_img_path, safe='/')
                        image_path = f"https://media.githubusercontent.com/media/Anduin2017/HowToCook/refs/heads/master/dishes/{encoded_path}"
                        break
                if image_path:
                    break
                
            # 如果还没找到图片，检查目录中的其他图片文件（按字母顺序排序以保证一致性）
            if not image_path:
                image_files = sorted([f for f in image_dir.glob('*') 
                                     if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']])
                if image_files:
                    img_file = image_files[0]  # 取第一个（按字母顺序）
                    relative_img_path = str(relative_path.parent / img_file.name).replace('\\', '/')
                    from urllib.parse import quote
                    encoded_path = quote(relative_img_path, safe='/')
                    image_path = f"https://media.githubusercontent.com/media/Anduin2017/HowToCook/refs/heads/master/dishes/{encoded_path}"
            
            # 组装完整的菜谱字典
            recipe = {
                'id': recipe_id,
                'name': title,
                'description': self.extract_description(content),
                'source_path': f"dishes/{relative_str}",
                'image_path': image_path,
                'category': category,
                'difficulty': self.parse_difficulty(content),
                'tags': [category],
                'servings': self.parse_servings(content),
                'ingredients': self.parse_ingredients(content),
                'steps': self.parse_steps(content),
                'prep_time_minutes': None,
                'cook_time_minutes': None,
                'total_time_minutes': None,
                'additional_notes': self.parse_notes(content)
            }
            
            return recipe
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def convert_all_recipes(self, output_file: str):
        """
        转换所有菜谱文件为 JSON 格式
        
        Args:
            output_file: 输出 JSON 文件的路径
            
        处理流程：
        1. 遍历 dishes 目录下的所有 Markdown 文件
        2. 跳过模板文件
        3. 解析每个菜谱文件
        4. 按 ID 排序以确保输出一致性
        5. 写入 JSON 文件
        """
        recipes = []
        dishes_path = self.base_path / 'dishes'
        
        if not dishes_path.exists():
            print(f"Error: {dishes_path} does not exist")
            return
        
        # 遍历所有 Markdown 文件
        for md_file in dishes_path.rglob('*.md'):
            relative_path = md_file.relative_to(dishes_path)
            
            # 跳过模板文件
            if 'template' in str(relative_path).lower():
                continue
            
            print(f"Processing: {relative_path}")
            recipe = self.parse_recipe_file(md_file, relative_path)
            
            if recipe:
                recipes.append(recipe)
        
        # 按 ID 排序以确保输出一致性
        recipes.sort(key=lambda x: x['id'])
        
        # 写入 JSON 文件
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2, sort_keys=True)
        
        print(f"\nConversion complete!")
        print(f"Total recipes: {len(recipes)}")
        print(f"Output file: {output_path}")


def main():
    """
    主入口函数
    
    功能：
    1. 自动检测 HowToCook 目录位置
    2. 创建解析器实例
    3. 执行转换并输出 JSON 文件
    
    支持的目录位置：
    - HowToCook（当前目录下）
    - /Users/e/workplace/python/howtocook-to-json/HowToCook（本地开发路径）
    - ../HowToCook（上级目录）
    """
    import sys
    
    # 自动检测 HowToCook 目录
    # 尝试多个可能的位置
    possible_paths = [
        'HowToCook',  # GitHub Actions 克隆的位置
        '/Users/e/workplace/python/howtocook-to-json/HowToCook',  # 本地开发路径
        '../HowToCook',  # 相对路径
    ]
    
    base_path = None
    for path in possible_paths:
        if Path(path).exists():
            base_path = path
            print(f"找到 HowToCook 目录: {path}")
            break
    
    if not base_path:
        print("错误: 找不到 HowToCook 目录")
        print("请确保已克隆 HowToCook 仓库到以下位置之一:")
        for path in possible_paths:
            print(f"  - {path}")
        sys.exit(1)
    
    output_file = 'target/all_recipes.json'
    
    # 创建解析器并执行转换
    parser = RecipeParser(base_path)
    parser.convert_all_recipes(output_file)


if __name__ == '__main__':
    main()
