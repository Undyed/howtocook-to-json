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
from typing import Dict, List, Optional, Any


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
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        
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
        match = re.search(r'## 计算(.*?)(?=##|\Z)', content, re.DOTALL)
        
        # If no "计算" section, try "必备原料和工具"
        if not match:
            match = re.search(r'## 必备原料和工具(.*?)(?=##|\Z)', content, re.DOTALL)
        
        if not match:
            return ingredients
        
        ingredient_text = match.group(1)
        
        # Parse each ingredient line
        for line in ingredient_text.split('\n'):
            line = line.strip()
            if not line or not line.startswith('-') and not line.startswith('*'):
                continue
            
            # Remove leading dash/asterisk
            line = re.sub(r'^[-*]\s*', '', line)
            
            # Skip lines that are notes or warnings
            if line.startswith('注：') or line.startswith('注意') or line.startswith('WARNING'):
                continue
            
            # Handle lines with multiple items separated by 、 or ，
            if ('、' in line or '，' in line) and not re.search(r'\d+\s*[-~]\s*\d+', line):
                # Split by 、 or ，
                items = re.split(r'[、，]', line)
                for item in items:
                    item = item.strip()
                    if not item:
                        continue
                    
                    # Try to parse quantity for each item
                    item_ingredient = {
                        'name': None,
                        'quantity': None,
                        'unit': None,
                        'text_quantity': f"- {item}",
                        'notes': '量未指定'
                    }
                    
                    quantity_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kg|ml|l|斤|个|只|片|根|瓣|颗|块|勺|匙|小勺|大勺|克|毫升|升|两|钱)', item)
                    if quantity_match:
                        quantity_str = quantity_match.group(1)
                        unit = quantity_match.group(2)
                        name_match = re.match(r'([^0-9]+)', item)
                        if name_match:
                            item_ingredient['name'] = name_match.group(1).strip()
                            item_ingredient['quantity'] = float(quantity_str)
                            item_ingredient['unit'] = unit
                            item_ingredient['text_quantity'] = f"{quantity_str} {unit}"
                            item_ingredient['notes'] = None
                    else:
                        item_ingredient['name'] = item
                    
                    if item_ingredient['name']:
                        ingredients.append(item_ingredient)
                continue
            
            ingredient = {
                'name': None,
                'quantity': None,
                'unit': None,
                'text_quantity': f"- {line}",
                'notes': '量未指定'
            }
            
            # Try to parse quantity and unit
            # Pattern: name quantity unit
            quantity_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kg|ml|l|斤|个|只|片|根|瓣|颗|块|勺|匙|小勺|大勺|克|毫升|升|两|钱)', line)
            
            if quantity_match:
                quantity_str = quantity_match.group(1)
                unit = quantity_match.group(2)
                
                # Extract name (text before quantity)
                name_match = re.match(r'([^0-9]+)', line)
                if name_match:
                    ingredient['name'] = name_match.group(1).strip()
                    ingredient['quantity'] = float(quantity_str)
                    ingredient['unit'] = unit
                    ingredient['text_quantity'] = f"{quantity_str} {unit}"
                    ingredient['notes'] = None
            else:
                # No quantity found, just extract name
                name_match = re.match(r'([^\d]+)', line)
                if name_match:
                    ingredient['name'] = name_match.group(1).strip()
            
            if ingredient['name']:
                ingredients.append(ingredient)
        
        return ingredients
    
    def parse_steps(self, content: str) -> List[Dict[str, Any]]:
        """Parse cooking steps"""
        steps = []
        
        # Find steps section
        match = re.search(r'## 计算和操作(.*?)(?=##|\Z)', content, re.DOTALL)
        if not match:
            return steps
        
        steps_text = match.group(1)
        
        # Parse each step
        step_num = 1
        for line in steps_text.split('\n'):
            line = line.strip()
            if not line or not line.startswith('-') and not line.startswith('*'):
                continue
            
            # Remove leading dash/asterisk
            description = re.sub(r'^[-*]\s*', '', line)
            
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
        match = re.search(r'##\s*附加内容(.*?)(?=##|\Z)', content, re.DOTALL)
        if not match:
            # Try to find any content after steps
            match = re.search(r'## 计算和操作.*?(?=##|\Z)(.*)', content, re.DOTALL)
        
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
            recipe_id = 'dishes-' + str(relative_path).replace('/', '-').replace('.md', '').replace('\\', '-')
            
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
                
            # Also check for other common image names in the directory
            if not image_path:
                for img_file in image_dir.glob('*'):
                    if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                        relative_img_path = str(relative_path.parent / img_file.name).replace('\\', '/')
                        from urllib.parse import quote
                        encoded_path = quote(relative_img_path, safe='/')
                        image_path = f"https://media.githubusercontent.com/media/Anduin2017/HowToCook/refs/heads/master/dishes/{encoded_path}"
                        break
            
            recipe = {
                'id': recipe_id,
                'name': title,
                'description': self.extract_description(content),
                'source_path': str(relative_path).replace('\\', '/'),
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
