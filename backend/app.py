"""
一村一品 API 服务
从 CSV 文件读取数据
"""
import os
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 获取 CSV 文件路径
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, 'villages.csv')

# 全局变量
villages_data = []
provinces_data = []
categories_data = []

def load_data():
    """从 CSV 文件加载数据"""
    global villages_data, provinces_data, categories_data
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"✅ 成功加载 {len(df)} 条村庄数据")
        print(f"📋 列名: {list(df.columns)}")
        
        # 转换为字典列表
        villages_data = df.to_dict(orient='records')
        
        # 统计省份数据（用于首页省份卡片）
        province_stats = {}
        for v in villages_data:
            province = v.get('province', '未知')
            if province not in province_stats:
                province_stats[province] = {
                    'name': province,
                    'count': 0
                }
            province_stats[province]['count'] += 1
        provinces_data = list(province_stats.values())
        
        # 统计分类数据（用于筛选按钮）
        category_stats = {}
        for v in villages_data:
            cat = v.get('industry_type', '其他')
            if cat not in category_stats:
                category_stats[cat] = {
                    'name': cat,
                    'count': 0
                }
            category_stats[cat]['count'] += 1
        categories_data = list(category_stats.values())
        
        print(f"✅ 统计完成: {len(provinces_data)} 个省份, {len(categories_data)} 个分类")
        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {csv_path}")
        villages_data = []
        provinces_data = []
        categories_data = []
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        villages_data = []
        provinces_data = []
        categories_data = []

# ========== API 接口 ==========

@app.route('/')
def hello():
    return '一村一品 API 服务运行中'

@app.route('/api/villages', methods=['GET'])
def get_villages():
    """获取村庄列表，支持按省份、分类筛选"""
    province = request.args.get('province')
    category = request.args.get('category')
    keyword = request.args.get('keyword')
    
    result = villages_data.copy()
    
    if province:
        result = [v for v in result if v.get('province') == province]
    if category:
        result = [v for v in result if v.get('industry_type') == category]
    if keyword:
        result = [v for v in result if keyword in str(v.get('name', '')) or keyword in str(v.get('product_name', ''))]
    
    return jsonify(result)

@app.route('/api/villages/<int:id>', methods=['GET'])
def get_village(id):
    """获取单个村庄详情（复数路径）"""
    for v in villages_data:
        if v.get('id') == id:
            return jsonify(v)
    return jsonify({'error': '未找到'}), 404

# 兼容单数路径 /api/village/<id>
@app.route('/api/village/<int:id>', methods=['GET'])
def get_village_alt(id):
    """获取单个村庄详情（单数路径，兼容前端旧代码）"""
    return get_village(id)

@app.route('/api/provinces', methods=['GET'])
def get_provinces():
    """获取省份列表（用于首页卡片）"""
    return jsonify(provinces_data)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取分类列表（用于筛选按钮）"""
    return jsonify(categories_data)

# 启动时加载数据
if __name__ == '__main__':
    load_data()
    app.run(debug=True, port=5000)