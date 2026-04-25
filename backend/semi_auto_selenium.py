"""
半自动百度百科链接采集（Selenium版）- 增强版（修复保存问题）
"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from urllib.parse import quote

def setup_driver():
    edge_options = Options()
    edge_options.add_argument('--log-level=3')
    edge_options.add_argument('--silent')
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Edge(options=edge_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def open_search_tabs(driver, keywords):
    handles = []
    driver.get(f"https://www.baidu.com/s?wd={quote(keywords[0])}")
    handles.append(driver.current_window_handle)
    time.sleep(1)
    for kw in keywords[1:]:
        driver.execute_script(f"window.open('https://www.baidu.com/s?wd={quote(kw)}');")
        time.sleep(0.5)
        handles.append(driver.current_window_handle)
    return handles

def close_tabs_except_main(driver, main_handle):
    for handle in driver.window_handles:
        if handle != main_handle:
            driver.switch_to.window(handle)
            driver.close()
    driver.switch_to.window(main_handle)

def get_user_choice(village_name, product_name, current_index, total):
    print("\n" + "="*60)
    print(f"当前进度: [{current_index+1}/{total}]")
    print(f"村庄: {village_name}")
    print(f"产品: {product_name}")
    print("="*60)
    print("👉 请在浏览器中查看搜索结果，复制合适的百度百科链接。")
    print("操作选项：")
    print("  1. 输入一个或多个链接（用英文逗号分隔）")
    print("  2. 输入 'skip' 跳过")
    print("  3. 输入 'pause' 暂停（按回车继续）")
    print("  4. 输入 'done' 完成并保存已处理的数据")
    print("  5. 输入 'goto' 跳转到其他村庄（按id或搜索）")
    user_input = input("\n请输入: ").strip()
    return user_input

def find_index_by_id_or_search(df, user_input):
    if user_input.isdigit():
        target_id = int(user_input)
        mask = df['id'] == target_id
        if mask.any():
            return mask.idxmax()
        else:
            print(f"❌ 未找到 id={target_id} 的村庄")
            return None
    else:
        keyword = user_input.strip()
        matches = df[df['name'].str.contains(keyword, na=False) | 
                     df['product_name'].str.contains(keyword, na=False)]
        if len(matches) == 0:
            print(f"❌ 未找到包含 '{keyword}' 的村庄")
            return None
        print(f"找到 {len(matches)} 个匹配项：")
        for i, (idx, row) in enumerate(matches.iterrows()):
            print(f"   {i+1}. id={row['id']}: {row['name']} - {row['product_name']}")
        if len(matches) == 1:
            return matches.index[0]
        else:
            sub_choice = input("请输入序号（1-{}）选择具体村庄: ".format(len(matches))).strip()
            if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(matches):
                return matches.index[int(sub_choice)-1]
            else:
                print("输入无效")
                return None

def main():
    df = pd.read_csv('villages.csv', encoding='utf-8-sig')
    if 'baike_urls' not in df.columns:
        df['baike_urls'] = ''
    df['baike_urls'] = df['baike_urls'].fillna('')
    
    total = len(df)
    completed = (df['baike_urls'] != '')
    completed_count = completed.sum()
    print(f"📊 总村庄数: {total}, 已完成: {completed_count}")
    
    # 选择起始索引
    start_idx = None
    choice = input("直接回车从第一个未处理村庄开始，或输入行号/id，或输入 'search' 搜索: ").strip()
    if choice == '':
        pending = df[df['baike_urls'] == '']
        if len(pending) == 0:
            print("✅ 所有村庄都已处理完成！")
            return
        start_idx = pending.index[0]
    elif choice.isdigit():
        start_idx = int(choice) - 1
        if start_idx < 0 or start_idx >= total:
            print("行号超出范围，从头开始")
            start_idx = None
    elif choice.lower() == 'search':
        keyword = input("请输入村庄名或产品名关键词: ").strip()
        idx = find_index_by_id_or_search(df, keyword)
        if idx is not None:
            start_idx = idx
        else:
            pending = df[df['baike_urls'] == '']
            if len(pending) > 0:
                start_idx = pending.index[0]
                print(f"未找到，从第一个未处理村庄开始: {df.loc[start_idx, 'name']}")
            else:
                print("✅ 所有村庄都已处理完成！")
                return
    else:
        pending = df[df['baike_urls'] == '']
        if len(pending) > 0:
            start_idx = pending.index[0]
            print(f"输入无效，从第一个未处理村庄开始: {df.loc[start_idx, 'name']}")
        else:
            print("✅ 所有村庄都已处理完成！")
            return
    
    if start_idx is None:
        return
    
    driver = setup_driver()
    main_handle = driver.current_window_handle
    idx = start_idx
    
    # 用于统计本次会话成功保存的数量
    saved_in_session = 0
    
    try:
        while idx < total:
            row = df.iloc[idx]
            village = row['name']
            product = row['product_name']
            current_urls = row['baike_urls']
            
            # 已有链接的处理
            if current_urls != '':
                print(f"\n{'='*50}")
                print(f"当前村庄 [{idx+1}/{total}]: {village} - {product}")
                print(f"已有链接: {current_urls[:80]}...")
                action = input("按回车跳过，输入 'e' 编辑/覆盖，输入 's' 停止: ").strip().lower()
                if action == 'e':
                    print("   ✏️ 请输入新的链接（多个用英文逗号分隔）")
                    new_links = input("请输入: ").strip()
                    if new_links:
                        urls = [url.strip() for url in new_links.split(',') if url.strip()]
                        if urls:
                            df.at[idx, 'baike_urls'] = '|'.join(urls)
                            df.to_csv('villages.csv', index=False, encoding='utf-8-sig')
                            print(f"   ✅ 已更新链接: {'|'.join(urls)}")
                            print("   💾 已保存")
                            saved_in_session += 1
                    else:
                        print("   ⚠️ 未输入链接，保持不变")
                elif action == 's':
                    print("   🛑 用户终止")
                    break
                # 无论跳过还是编辑，都移动到下一个
                idx += 1
                continue
            
            # 正常处理没有链接的村庄
            print(f"\n{'='*50}")
            print(f"🔍 正在处理 [{idx+1}/{total}] {village} - {product}")
            
            keywords = [
                f"{village} {product} 百科",
                f"{product} 百度百科",
                f"{village} 百度百科"
            ]
            print("   🌐 正在打开搜索页面...")
            open_search_tabs(driver, keywords)
            print("   ✅ 已打开 3 个搜索标签页")
            
            user_input = get_user_choice(village, product, idx, total)
            
            close_tabs_except_main(driver, main_handle)
            print("   🧹 已关闭搜索标签页")
            
            if user_input.lower() == 'skip':
                print("   ⏭️ 已跳过")
                idx += 1
                continue
            elif user_input.lower() == 'pause':
                input("   ⏸️ 已暂停，按回车继续...")
                continue
            elif user_input.lower() == 'done':
                print("   🛑 用户终止，正在保存已处理数据...")
                break
            elif user_input.lower() == 'goto':
                target = input("请输入目标 id 或搜索关键词: ").strip()
                new_idx = find_index_by_id_or_search(df, target)
                if new_idx is not None:
                    idx = new_idx
                    print(f"   🔄 跳转到: {df.loc[idx, 'name']} (行号 {idx+1})")
                else:
                    print("   ⚠️ 未找到目标，继续当前")
                continue
            else:
                # 处理用户输入的链接
                raw_input = user_input.strip()
                # 去除可能的外层引号
                if raw_input.startswith('"') and raw_input.endswith('"'):
                    raw_input = raw_input[1:-1]
                if raw_input.startswith("'") and raw_input.endswith("'"):
                    raw_input = raw_input[1:-1]
                
                urls = [url.strip() for url in raw_input.split(',') if url.strip()]
                if urls:
                    df.at[idx, 'baike_urls'] = '|'.join(urls)
                    print(f"   ✅ 已保存 {len(urls)} 个链接")
                    # 立即保存到文件
                    df.to_csv('villages.csv', index=False, encoding='utf-8-sig')
                    print("   💾 数据已实时保存")
                    # 验证是否真的写入
                    df_verify = pd.read_csv('villages.csv', encoding='utf-8-sig')
                    saved_val = df_verify.at[idx, 'baike_urls']
                    if saved_val == '|'.join(urls):
                        print(f"   🔍 验证通过，已写入CSV")
                    else:
                        print(f"   ❌ 验证失败！请检查文件权限")
                    saved_in_session += 1
                else:
                    print("   ⚠️ 未输入有效链接，跳过")
            
            idx += 1
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断，正在保存...")
    finally:
        df.to_csv('villages.csv', index=False, encoding='utf-8-sig')
        driver.quit()
        print(f"\n✅ 程序结束，浏览器已关闭。本次会话共保存 {saved_in_session} 条链接。")

if __name__ == '__main__':
    main()