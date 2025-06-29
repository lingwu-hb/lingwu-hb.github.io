import os
import re
import yaml
import shutil
from datetime import datetime

# 配置
posts_dir = 'source/_posts'
links_base_dir = 'source/_posts_organized'  # 存放链接的基础目录
organize_by = 'categories'  # 'date' 或 'categories' 或 'both'

def normalize_category(category):
    """处理类别名称，移除中括号"""
    if isinstance(category, str):
        # 移除 [xxx] 格式中的括号
        return re.sub(r'^\[(.*)\]$', r'\1', category.strip())
    return category

def create_symlinks():
    print("开始更新文章符号链接...")
    
    # 确保目录存在
    if not os.path.exists(posts_dir):
        print(f"错误: {posts_dir} 目录不存在")
        return False
    
    # 如果链接目录已存在，先清空它
    if os.path.exists(links_base_dir):
        print(f"清空目录: {links_base_dir}")
        shutil.rmtree(links_base_dir)
    
    # 创建基础链接目录
    os.makedirs(links_base_dir, exist_ok=True)
    
    # 创建分类目录
    if organize_by in ['categories', 'both']:
        categories_dir = os.path.join(links_base_dir, 'categories')
        os.makedirs(categories_dir, exist_ok=True)
    
    # 创建日期目录
    if organize_by in ['date', 'both']:
        date_dir = os.path.join(links_base_dir, 'date')
        os.makedirs(date_dir, exist_ok=True)
    
    # 获取所有文章文件
    files = [f for f in os.listdir(posts_dir) if f.endswith('.md') and os.path.isfile(os.path.join(posts_dir, f))]
    print(f"找到 {len(files)} 个文章文件")
    
    for file in files:
        file_path = os.path.join(posts_dir, file)
        print(f"处理文件: {file}")
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"警告: 无法读取 {file}: {e}")
            continue
        
        # 提取front-matter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            print(f"警告: {file} 没有有效的front-matter，跳过")
            continue
            
        try:
            front_matter = yaml.safe_load(match.group(1))
        except Exception as e:
            print(f"警告: {file} front-matter解析错误: {e}")
            continue
        
        # 按类别组织
        if organize_by in ['categories', 'both']:
            categories = front_matter.get('categories', [])
            
            # 处理不同格式的类别
            if not isinstance(categories, list):
                categories = [categories] if categories else []
            
            # 处理嵌套列表的情况，如 [['AI'], ['data storage']]
            processed_categories = []
            for cat in categories:
                if isinstance(cat, list):
                    # 如果是嵌套列表，提取每个子元素
                    for subcat in cat:
                        if subcat:
                            processed_categories.append(normalize_category(subcat))
                else:
                    if cat:
                        processed_categories.append(normalize_category(cat))
            
            print(f"文件 {file} 的分类: {processed_categories}")
            
            for category in processed_categories:
                if not category:
                    continue
                    
                target_dir = os.path.join(categories_dir, str(category))
                os.makedirs(target_dir, exist_ok=True)
                
                # 创建符号链接
                link_path = os.path.join(target_dir, file)
                if os.path.exists(link_path):
                    print(f"删除已存在的文件: {link_path}")
                    os.remove(link_path)
                
                # 计算相对路径
                rel_path = os.path.relpath(file_path, target_dir)
                
                # Windows上使用mklink命令或直接复制
                if os.name == 'nt':
                    try:
                        # 在Windows上，使用复制而不是符号链接
                        print(f"复制文件: {file_path} -> {link_path}")
                        shutil.copy2(file_path, link_path)
                        print(f"复制成功: {file} -> {category}/{file}")
                    except Exception as e:
                        print(f"警告: 无法创建链接 {file} -> {category}/{file}: {e}")
                else:
                    try:
                        os.symlink(rel_path, link_path)
                        print(f"创建符号链接: {file} -> {category}/{file}")
                    except Exception as e:
                        print(f"警告: 无法创建链接 {file} -> {category}/{file}: {e}")
        
        # 按日期组织
        if organize_by in ['date', 'both']:
            date_str = front_matter.get('date')
            if not date_str:
                print(f"警告: {file} 没有日期信息，跳过日期组织")
                continue
                
            try:
                if isinstance(date_str, datetime):
                    year = date_str.strftime('%Y')
                    month = date_str.strftime('%m')
                else:
                    date_parts = str(date_str).split('-')
                    year, month = date_parts[0], date_parts[1] if len(date_parts) > 1 else '01'
            except Exception as e:
                print(f"警告: {file} 日期格式不正确: {e}")
                continue
                
            year_dir = os.path.join(date_dir, year)
            os.makedirs(year_dir, exist_ok=True)
            
            month_dir = os.path.join(year_dir, month)
            os.makedirs(month_dir, exist_ok=True)
            
            # 创建符号链接
            link_path = os.path.join(month_dir, file)
            if os.path.exists(link_path):
                print(f"删除已存在的文件: {link_path}")
                os.remove(link_path)
            
            # 计算相对路径
            rel_path = os.path.relpath(file_path, month_dir)
            
            # Windows上使用mklink命令或直接复制
            if os.name == 'nt':
                try:
                    # 在Windows上，使用复制而不是符号链接
                    print(f"复制文件: {file_path} -> {link_path}")
                    shutil.copy2(file_path, link_path)
                    print(f"复制成功: {file} -> {year}/{month}/{file}")
                except Exception as e:
                    print(f"警告: 无法创建链接 {file} -> {year}/{month}/{file}: {e}")
            else:
                try:
                    os.symlink(rel_path, link_path)
                    print(f"创建符号链接: {file} -> {year}/{month}/{file}")
                except Exception as e:
                    print(f"警告: 无法创建链接 {file} -> {year}/{month}/{file}: {e}")
    
    print("符号链接更新完成!")
    return True

if __name__ == "__main__":
    create_symlinks()