import pandas as pd

# 读取你的 Excel 文件（请根据实际文件名修改）
df = pd.read_excel('villages.xlsx', sheet_name='Sheet1')  

# 重命名列
df = df.rename(columns={
    '序号': 'id',
    '行政区': 'province',
    '市': 'city',
    '村': 'name',
    '一级分类': 'industry_type',
    '二级分类': 'sub_category',
    '产品名称': 'product_name'
})

# 添加 baike_urls 列（空）
df['baike_urls'] = ''

# 确保 id 是整数
df['id'] = df['id'].astype(int)

# 保存为 villages.csv（半自动脚本默认读取这个文件）
df.to_csv('villages.csv', index=False, encoding='utf-8-sig')

print(f"转换完成！共 {len(df)} 条数据，已保存为 villages.csv")