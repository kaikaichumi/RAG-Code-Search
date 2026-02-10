#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 CSV 資料庫說明轉換成 Markdown 格式
這樣 RAG 系統能更好地理解和搜尋
"""

import csv
import os
from pathlib import Path

def convert_db_csv_to_markdown():
    """將資料庫 CSV 轉換成結構化的 Markdown"""

    csv_path = Path("../HM-DB資料庫說明(欄位說明).csv")
    output_path = Path("../DB_SCHEMA.md")

    if not csv_path.exists():
        print(f"❌ 找不到檔案：{csv_path}")
        return

    print(f"📖 讀取 CSV：{csv_path}")

    # 讀取 CSV（自動偵測編碼）
    encodings = ['utf-8-sig', 'utf-8', 'cp950', 'big5']
    content = None

    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                content = list(csv.reader(f))
            print(f"✓ 成功讀取（編碼：{encoding}）")
            break
        except:
            continue

    if not content:
        print("❌ 無法讀取 CSV 檔案")
        return

    # 開始轉換
    print(f"✏️  轉換成 Markdown...")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# HMRV 資料庫結構說明\n\n")
        f.write("## 綱目：HMRV\n\n")
        f.write("> 本文件由 CSV 自動轉換，包含所有資料表和欄位說明\n\n")
        f.write("---\n\n")

        current_table = None
        in_table_header = False

        for i, row in enumerate(content):
            # 跳過空行
            if not any(row):
                continue

            # 偵測表格名稱（第二欄有值）
            if len(row) > 1 and row[1] and not row[1].startswith('表格'):
                current_table = row[1].strip()
                if current_table:
                    f.write(f"## 表格：{current_table}\n\n")
                    in_table_header = True
                    continue

            # 偵測欄位說明標題行
            if len(row) > 3 and '欄位名稱' in str(row):
                if current_table:
                    f.write("| KEY | 欄位名稱 | 資料型態 | NULL | 說明 | 備註 |\n")
                    f.write("|-----|---------|---------|------|------|------|\n")
                in_table_header = False
                continue

            # 寫入欄位資料
            if current_table and len(row) > 6:
                key = row[2].strip() if len(row) > 2 else ''
                field = row[3].strip() if len(row) > 3 else ''
                dtype = row[4].strip() if len(row) > 4 else ''
                null = row[5].strip() if len(row) > 5 else ''
                desc = row[6].strip() if len(row) > 6 else ''
                note = row[7].strip() if len(row) > 7 else ''

                # 只寫入有欄位名稱的行
                if field:
                    # 清理多行內容
                    desc = desc.replace('\n', ' ').replace('\r', '')
                    note = note.replace('\n', ' ').replace('\r', '')

                    f.write(f"| {key} | `{field}` | {dtype} | {null} | {desc} | {note} |\n")

        f.write("\n---\n\n")
        f.write("*本文件由 convert_csv_to_md.py 自動產生*\n")

    print(f"✅ 轉換完成！")
    print(f"📄 輸出檔案：{output_path.absolute()}")
    print(f"📊 檔案大小：{output_path.stat().st_size / 1024:.1f} KB")
    print()
    print("下一步：")
    print("  1. 檢查 DB_SCHEMA.md 內容是否正確")
    print("  2. 重新執行 3_build_db.bat 建立知識庫")
    print("  3. 這次就能正確搜尋資料庫欄位說明了！")

if __name__ == "__main__":
    convert_db_csv_to_markdown()
