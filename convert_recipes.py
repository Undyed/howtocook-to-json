#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recipe Markdown to JSON Converter
Converts HowToCook recipe markdown files to structured JSON format
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class RecipeParser:
    """Parser for recipe markdown files"""
    
    # Category mapping based on directory structure
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
    
    QUANTITY_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*('
        r'g|kg|mg|ml|l|L|斤|两|钱|克|千克|毫克|毫升|升|'
        r'个|只|片|根|瓣|颗|块|勺|匙|小勺|大勺|汤勺|茶勺|撮|粒|朵|条|段|杯|碗|锅|人|份|份数|cm|厘米|mm|毫米|米|寸|滴|包|袋|盒|瓶|罐|棵|头|尾'
        r')',
        re.IGNORECASE
    )
    
    QUALITATIVE_KEYWORDS = (
        '适量', '少许', '若干', '适当', '随意', '按口味', '酌情', '适量即可',
        '足量', '少量', '充足', '适量/按口味', '适量（按口味）'
    )
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
    
    def _strip_parenthetical(self, text: str) -> Tuple[str, List[str]]:
        """Remove parenthetical notes while collecting their text"""
        if not text:
            return '', []
        
        notes: List[str] = []
        
        def replacer(match):
            inner = match.group(1).strip()
            if inner:
                notes.append(inner)
            return ''
        
        cleaned = re.sub(r'[（(]([^（）()]+)[）)]', replacer, text)
        return cleaned.strip(), notes
    
    def _split_name_quantity(self, text: str) -> Tuple[str, str]:
        """Split an ingredient line into name and quantity parts"""
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
        """Create an ingredient dictionary from a single line of text"""
        text = raw_text.strip()
        if not text or re.fullmatch(r'[-*_]{2,}', text):
            return None
        
        name_part, quantity_part = self._split_name_quantity(text)
        quantity_display = quantity_part
        quantity_search = quantity_part or text
        
        if '=' in quantity_part:
            left, right = quantity_part.split('=', 1)
            if left.strip():
                quantity_display = left.strip()
            quantity_search = right.strip() or left.strip() or quantity_part
        
        name_clean, name_notes = self._strip_parenthetical(name_part)
        quantity_display, quantity_notes = self._strip_parenthetical(quantity_display)
        
        quantity_match = self.QUANTITY_PATTERN.search(quantity_search) or self.QUANTITY_PATTERN.search(text)
        quantity_value = float(quantity_match.group(1)) if quantity_match else None
        unit = quantity_match.group(2) if quantity_match else None
        
        notes = [note for note in name_notes + quantity_notes if note]
        notes_text = '；'.join(notes) if notes else None
        
        ingredient = {
            'name': name_clean.strip('：:=') if name_clean else None,
            'quantity': quantity_value,
            'unit': unit,
            'text_quantity': quantity_display if quantity_display else None,
            'notes': notes_text
        }
        
        if ingredient['name']:
            if ingredient['text_quantity'] is None and ingredient['quantity'] is None and not ingredient['notes']:
                ingredient['notes'] = '量未指定'
            return ingredient
        
        return None
        
    def parse_difficulty(self, content: str) -> int:
        """Extract difficulty level from content"""
        match = re.search(r'预估烹饪难度：(★+)', content)
        if match:
            return len(match.group(1))
        return 1
    
    def parse_servings(self, content: str) -> int:
        """Extract servings from content"""
        # Default to 1 serving
        return 1
    
    def parse_ingredients(self, content: str) -> List[Dict[str, Any]]:
        """Parse ingredients section"""
        ingredients = []
        
        # Try to find "计算" section first (more specific ingredient list)
        match = re.search(r'##\s*计算(.*?)(?=^##(?!#)|\Z)', content, re.DOTALL | re.MULTILINE)
        
        # If no "计算" section, try "必备原料和工具"
        if not match:
            match = re.search(r'##\s*必备原料和工具(.*?)(?=^##(?!#)|\Z)', content, re.DOTALL | re.MULTILINE)
        
        if not match:
            return ingredients
        
        ingredient_text = match.group(1)
        
        # Parse each ingredient line
        for line in ingredient_text.split('\n'):
            line = line.strip()
            if not line or (line[0] not in '-*+'):
                continue
            
            # Remove leading dash/asterisk
            line = re.sub(r'^[-*+]\s*', '', line)
            
            # Skip lines that are notes or warnings
            if line.startswith('注：') or line.startswith('注意') or line.startswith('WARNING'):
                continue
            
            # Handle lines with multiple items separated by 、 or ，
            multi_sep = ('、' in line or '，' in line)
            has_numeric = bool(re.search(r'\d', line))
            has_special_sep = any(sep in line for sep in ('=', ':', '：', '*'))
            
            if multi_sep and not has_numeric and not has_special_sep:
                items = [item.strip() for item in re.split(r'[、，]', line) if item.strip()]
                for item in items:
                    ingredient = self._create_ingredient_entry(item)
                    if ingredient:
                        ingredients.append(ingredient)
                continue
            
            ingredient = self._create_ingredient_entry(line)
            if ingredient:
                ingredients.append(ingredient)
        
        return ingredients
    
    def parse_steps(self, content: str) -> List[Dict[str, Any]]:
        """Parse cooking steps"""
        steps = []
        
        # Find steps section
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
        
        # Parse each step
        step_num = 1
        for line in steps_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            description = ''
            if line and line[0] in '-*+':
                description = re.sub(r'^[-*+]\s*', '', line).strip()
            else:
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
        """Parse additional notes"""
        notes = []
        
        # Find notes section (usually at the end)
        match = re.search(r'##\s*附加内容(.*?)(?=^##(?!#)|\Z)', content, re.DOTALL | re.MULTILINE)
        if not match:
            # Try to find any content after steps
            match = re.search(r'##\s*(?:计算和操作|操作)(.*?)(?=^##(?!#)|\Z)', content, re.DOTALL | re.MULTILINE)
        
        if match:
            notes_text = match.group(1)
            for line in notes_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or line.startswith('如果您遵循')):
                    notes.append(line)
        
        return notes
    
    def extract_description(self, content: str) -> str:
        """Extract description from content"""
        # Get content before first ## heading
        match = re.match(r'#[^#].*?\n\n(.*?)(?=##)', content, re.DOTALL)
        if match:
            desc = match.group(1).strip()
            # Include difficulty if present
            difficulty_match = re.search(r'预估烹饪难度：(★+)', content)
            if difficulty_match:
                if not desc.endswith(difficulty_match.group(0)):
                    desc += f"\n\n{difficulty_match.group(0)}"
            return desc
        return ""
    
    def parse_recipe_file(self, file_path: Path, relative_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single recipe markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title (use search instead of match to handle leading whitespace)
            title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
            if not title_match:
                return None
            
            title = title_match.group(1).strip()
            
            # Generate ID from path with "dishes" prefix
            relative_str = relative_path.as_posix()
            recipe_id = 'dishes-' + relative_str.replace('/', '-').replace('.md', '')
            
            # Determine category from path
            parts = relative_path.parts
            category = self.CATEGORY_MAP.get(parts[0], parts[0]) if len(parts) > 0 else '未分类'
            
            # Check for image and generate GitHub media URL
            image_path = None
            image_dir = file_path.parent
            for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                # Check for same name as markdown file
                img_file = image_dir / (file_path.stem + ext)
                if img_file.exists():
                    # Generate GitHub media URL with URL encoding
                    relative_img_path = str(relative_path.parent / img_file.name).replace('\\', '/')
                    # URL encode the path
                    from urllib.parse import quote
                    encoded_path = quote(relative_img_path, safe='/')
                    image_path = f"https://media.githubusercontent.com/media/Anduin2017/HowToCook/refs/heads/master/dishes/{encoded_path}"
                    break
                # Check for common names
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
                
            # Also check for other common image names in the directory (sorted for consistency)
            if not image_path:
                image_files = sorted([f for f in image_dir.glob('*') 
                                     if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']])
                if image_files:
                    img_file = image_files[0]  # Take the first one alphabetically
                    relative_img_path = str(relative_path.parent / img_file.name).replace('\\', '/')
                    from urllib.parse import quote
                    encoded_path = quote(relative_img_path, safe='/')
                    image_path = f"https://media.githubusercontent.com/media/Anduin2017/HowToCook/refs/heads/master/dishes/{encoded_path}"
            
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
        """Convert all recipe files to JSON"""
        recipes = []
        dishes_path = self.base_path / 'dishes'
        
        if not dishes_path.exists():
            print(f"Error: {dishes_path} does not exist")
            return
        
        # Walk through all markdown files
        for md_file in dishes_path.rglob('*.md'):
            relative_path = md_file.relative_to(dishes_path)
            
            # Skip template files
            if 'template' in str(relative_path).lower():
                continue
            
            print(f"Processing: {relative_path}")
            recipe = self.parse_recipe_file(md_file, relative_path)
            
            if recipe:
                recipes.append(recipe)
        
        # Sort recipes by ID to ensure consistent output
        recipes.sort(key=lambda x: x['id'])
        
        # Write to JSON file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2, sort_keys=True)
        
        print(f"\nConversion complete!")
        print(f"Total recipes: {len(recipes)}")
        print(f"Output file: {output_path}")


def main():
    """Main entry point"""
    import sys
    
    # Auto-detect HowToCook directory
    # Try multiple possible locations
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
    
    # Create parser and convert
    parser = RecipeParser(base_path)
    parser.convert_all_recipes(output_file)


if __name__ == '__main__':
    main()
