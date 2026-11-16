import csv
import time
from pathlib import Path
from urllib.parse import urljoin

from scrapling.fetchers import Fetcher


def main():
    rows = []
    url = "https://quotes.toscrape.com/"
    seen = set()

    while url and url not in seen:
        page = Fetcher.get(url)

        if page.status != 200:
            raise RuntimeError(f"请求失败：{page.status}，网址：{url}")

        seen.add(url)

        for quote in page.css(".quote"):
            rows.append({
                "名言": quote.css(".text::text").get(),
                "作者": quote.css(".author::text").get(),
            })

        print(f"已采集 {len(seen)} 页，共 {len(rows)} 条")

        next_url = page.css(".next a::attr(href)").get()
        url = urljoin(url, next_url) if next_url else None

        if url:
            time.sleep(1)

    output = Path(__file__).parent / "all_quotes.csv"

    with output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["名言", "作者"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"保存完成：{output}")


if __name__ == "__main__":
    main()