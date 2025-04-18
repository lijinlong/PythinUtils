import asyncio
import json
import os
import argparse
from googletrans import Translator

### 需要安装 googletrans 库 ·pip install googletrans·

# 设置置信度阈值
ACCEPT_CONFIDENCE = 0.9  

async def translate_text(text, src_lang='auto', target_langs=None, translations=None):
    if target_langs is None:
        target_langs = ['en']  # 默认目标语言为英语

    async with Translator() as translator:
        print(f"Translating '{text}' ...")
        for target_lang in target_langs:
            result = await translator.translate(text, src=src_lang, dest=target_lang)
            print(f"{result.src}->{result.dest}:\t{result.text}")
            print(f"Pronunciation: {result.pronunciation}")
            confidence = result.extra_data.get('confidence', 0)
            print(f"Confidence: {confidence}")

            # 如果 confidence 大于 0.9，记录翻译结果
            if confidence < ACCEPT_CONFIDENCE:
                result.text = f"?{confidence:.2f}?" + result.text
                confidence = ACCEPT_CONFIDENCE
                # trust = input(f"Warning: Low confidence ({confidence}). Trust this translation or give your translate? (y/n): ").strip().lower()
                # if trust == 'y':
                #     confidence = ACCEPT_CONFIDENCE
                # elif len(trust) > 1:
                #     result.text = trust
                #     confidence = ACCEPT_CONFIDENCE

            if confidence >= ACCEPT_CONFIDENCE:
                if text not in translations:
                    translations[text] = []
                translations[text].append((target_lang, result.text))
            

# 用户交互部分
async def main():
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser(description="Google Translate CLI Tool")
    parser.add_argument("-src", help="源语言代码 (默认 'sl')", default=None)
    parser.add_argument("-dst", help="目标语言代码列表 (用逗号分隔，默认 'en,zh-CN')", default=None)
    parser.add_argument("file", nargs="?", help="要翻译的文本文件路径", default=None)
    args = parser.parse_args()

    # 如果命令行参数提供了源语言和目标语言，则使用它们
    src_lang = args.src or input("请输入源语言代码(默认 'sl' 斯洛文尼亚语):") or 'sl'
    target_langs = args.dst or input("请输入目标语言代码列表(用逗号分隔，默认 'en,zh-CN'):") or 'en,zh-CN'
    target_langs = target_langs.split(',')

    translations = {}  # 用于记录高置信度的翻译结果
    num = 0

    # 如果提供了文件路径，则读取文件内容逐行翻译
    if args.file:
        if not os.path.exists(args.file):
            print(f"文件 {args.file} 不存在。")
            return
        with open(args.file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            text = line.strip()
            if text:
                await translate_text(text, src_lang=src_lang, target_langs=target_langs, translations=translations)
                num += 1
    else:
        # 否则按交互模式运行
        while True:
            text = input(f"{num}:请输入要翻译的文字(输入 'q' 退出):")
            if text.lower() == 'q':
                print("退出翻译程序。")
                break
            await translate_text(text, src_lang=src_lang, target_langs=target_langs, translations=translations)
            num += 1

    # 打印记录的翻译结果
    if translations:
        print("\n记录的高置信度翻译结果:")
        for original, results in translations.items():
            print(f"原文: {original}")
            for target_lang, translated in results:
                print(f"  {target_lang}: {translated}")

        # 提示用户是否保存为 JSON 文件
        save_to_file = input("\n是否将高置信度的翻译结果保存为 JSON 文件？(y/n):").lower()
        if save_to_file == 'y':
            file_name = input("请输入保存的文件名(默认 'translations.json'):") or 'translations.json'
            
            # 自动添加 .json 扩展名（如果没有）
            if not file_name.endswith('.json'):
                file_name += '.json'

            # 如果文件已存在，读取内容并合并
            if os.path.exists(file_name):
                with open(file_name, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                #print(f"已找到现有文件：{file_name}:\n{existing_data}")

                # 合并现有数据与新数据
                for key, value in translations.items():
                    if key in existing_data:
                        # 合并并去重
                        combined = set(tuple(item) for item in existing_data[key]) | set(tuple(item) for item in value)
                        existing_data[key] = [list(item) for item in combined]
                        #print(f"Merge: {key}")
                    else:
                        existing_data[key] = value
                        #print(f"Add: {key}")
            else:
                existing_data = translations

            #print(f"After Merge: {existing_data}")
            # 按原文的字母序排列
            sorted_translations = dict(sorted(existing_data.items()))
            # 保存到文件
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(sorted_translations, f, ensure_ascii=False, indent=4)
            print(f"翻译结果已保存到文件：{file_name}")

        # 提示用户是否保存为 Markdown 文件
        save_to_md = input("\n是否将高置信度的翻译结果保存为 Markdown 文件？(y/n):").lower()
        if save_to_md == 'y':
            md_file_name = file_name.replace('.json', '.md')
            with open(md_file_name, 'w', encoding='utf-8') as f:
                for original, results in sorted(sorted_translations.items()):
                    f.write(f"{original}\n")
                    for target_lang, translated in results:
                        f.write(f"* {target_lang}: {translated}\n")
                    f.write("\n")
            print(f"翻译结果已保存到文件：{md_file_name}")
    else:
        print("\n没有记录到高置信度的翻译结果。")

# 运行程序
asyncio.run(main())

