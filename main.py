import argparse
from crawl_weibo import crawl_weibo_data, extract_content_details  # 导入微博爬虫模块

try:
    from config import CONFIG
except ImportError:
    raise ImportError("请根据 config_template.py 创建 config.py 文件，并填入配置信息")

def main():
    parser = argparse.ArgumentParser(description="A crawler for multiple platforms.")
    parser.add_argument("--platform", type=str, default="weibo", help="目标平台 (默认: weibo)")
    parser.add_argument("--keyword", type=str, default="高考加分", help="搜索关键词")
    parser.add_argument("--pages", type=int, default=5, help="爬取页数")
    parser.add_argument("--output", type=str, default="posts.csv", help="输出文件名")
    args = parser.parse_args()

    if args.platform == "weibo":
        # 调用微博爬虫
        results = crawl_weibo_data(args.keyword, args.pages, CONFIG["weibo"])
        if not results:
            print("未爬取到数据，请检查关键词或网络连接")
            return
        df = extract_content_details(results, CONFIG["weibo"])  # 修复：传入 config
        df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"已保存数据到 {args.output}")
    else:
        print(f"暂不支持平台：{args.platform}")
        # 未来扩展其他平台时在此添加逻辑

if __name__ == "__main__":
    main()