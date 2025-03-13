# Crawler

这是一个通用的爬虫工具，目前支持爬取微博帖子，未来可扩展至其他平台。

## 功能

- 搜索指定关键词的微博帖子。
- 提取包含“全文”链接的帖子完整内容。
- 输出结果到 CSV 文件。

## 依赖安装

1. 确保安装 Python 3.8 或以上版本。
2. 克隆仓库：

```bash
git clone https://github.com/yilin0518/crawler.git
cd crawler
```

3. 安装需要的python包

```bash
pip install requests beautifulsoup4 pandas selenium webdriver-manager
```

## 配置信息

根据 **config\_template.py** 创建 **config.py**

```bash
copy config_template.py config.py
```

编辑 **config.py**，填入平台的配置信息，例如:

```python
CONFIG = {
    "weibo": {
        "COOKIE": "你的微博 COOKIE",
        "XSRF_TOKEN": "你的微博 XSRF_TOKEN"  # 可选
    },
    "zhihu": {
        "COOKIE": "你的知乎 COOKIE",
        "OTHER_PARAM": "你的知乎参数"
    }
}
```

## 运行

可以选择使用命令行参数，不输入使用默认参数

```bash

python main.py --platform "weibo" --keyword "高考加分" --pages 5 --output "weibo_posts.csv"
```


* **--platform**：目标平台（当前支持 "weibo"）。
* **--keyword**：搜索关键词。
* **--pages**：爬取页数。
* **--output**：输出文件名。
