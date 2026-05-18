#!/usr/bin/env python3
"""
news_sync.py - RSSフィードから日次ニュースを取得（日本語要約付き）
カテゴリ: AI, スタートアップ, 土木業界, 米国建設, BIM×AI

依存: pip install feedparser google-genai python-dotenv
"""

import os
import sys
import re
import html
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from xml.etree import ElementTree as ET

from dotenv import load_dotenv

load_dotenv()

try:
    import feedparser
except ImportError:
    print("feedparser未インストール: pip install feedparser")
    sys.exit(1)

# Gemini APIによる日本語要約
_genai_client = None

def _get_genai_client():
    global _genai_client
    if _genai_client is not None:
        return _genai_client
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        _genai_client = genai.Client(api_key=api_key)
        return _genai_client
    except Exception as e:
        print(f"  ⚠ Gemini初期化失敗: {e}")
        return None


def translate_to_japanese(articles_by_category: dict) -> dict:
    """全記事をまとめてGeminiで日本語タイトル・要約に変換する"""
    client = _get_genai_client()
    if not client:
        return {}

    entries = []
    index_map = []
    for category, feeds_data in articles_by_category.items():
        for feed_name, articles in feeds_data:
            for article in articles:
                idx = len(entries)
                entries.append(f"[{idx}] {article['title']}\n{article['summary']}")
                index_map.append((category, feed_name, article))

    if not entries:
        return {}

    BATCH_SIZE = 30
    result_map = {}

    for batch_start in range(0, len(entries), BATCH_SIZE):
        batch = entries[batch_start:batch_start + BATCH_SIZE]
        batch_text = "\n---\n".join(batch)

        prompt = (
            "以下のニュース記事を日本語に翻訳・要約してください。\n"
            "各記事は [番号] で始まります。出力は以下の形式で、番号ごとに1行で返してください:\n"
            "[番号] 日本語タイトル | 日本語要約（1〜2文）\n\n"
            "元から日本語の記事はそのまま出力してください。\n"
            "番号は入力と同じ番号をそのまま使ってください。\n\n"
            f"{batch_text}"
        )

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            for line in response.text.strip().split("\n"):
                line = line.strip()
                m = re.match(r"\[(\d+)\]\s*(.+?)\s*\|\s*(.+)", line)
                if m:
                    abs_idx = int(m.group(1))
                    if 0 <= abs_idx < len(index_map):
                        cat, fn, art = index_map[abs_idx]
                        result_map[id(art)] = {
                            "title_ja": m.group(2).strip(),
                            "summary_ja": m.group(3).strip(),
                        }
        except Exception as e:
            print(f"  ⚠ Gemini翻訳エラー: {e}")

    return result_map

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "context", "news")

# --- RSSフィード定義 ---
FEEDS = {
    "AI": [
        {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
        {"name": "The Batch (deeplearning.ai)", "url": "https://www.deeplearning.ai/the-batch/feed/"},
        {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
        {"name": "AI News (Google)", "url": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"},
        {"name": "ITmedia AI+", "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"},
        {"name": "AI News (Google JP)", "url": "https://news.google.com/rss/search?q=%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD+OR+%E7%94%9F%E6%88%90AI&hl=ja&gl=JP&ceid=JP:ja"},
    ],
    "スタートアップ": [
        {"name": "TechCrunch Startups", "url": "https://techcrunch.com/category/startups/feed/"},
        {"name": "BRIDGE (日本)", "url": "https://thebridge.jp/feed"},
        {"name": "Y Combinator Blog", "url": "https://www.ycombinator.com/blog/rss/"},
        {"name": "スタートアップ (Google JP)", "url": "https://news.google.com/rss/search?q=%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%88%E3%82%A2%E3%83%83%E3%83%97+%E8%B3%87%E9%87%91%E8%AA%BF%E9%81%94&hl=ja&gl=JP&ceid=JP:ja"},
    ],
    "土木・建設": [
        {"name": "建設通信新聞", "url": "https://www.kensetsunews.com/rss/archives.xml"},
        {"name": "日経クロステック 建設", "url": "https://xtech.nikkei.com/rss/xtech-kensetsu.rdf"},
        {"name": "Construction Dive", "url": "https://www.constructiondive.com/feeds/news/"},
        {"name": "ENR (Engineering News-Record)", "url": "https://www.enr.com/rss"},
        {"name": "建設業界 (Google JP)", "url": "https://news.google.com/rss/search?q=%E5%BB%BA%E8%A8%AD+OR+%E5%9C%9F%E6%9C%A8+OR+%E3%82%BC%E3%83%8D%E3%82%B3%E3%83%B3&hl=ja&gl=JP&ceid=JP:ja"},
    ],
    "建設スタートアップ": [
        {"name": "ConTech (Google News)", "url": "https://news.google.com/rss/search?q=construction+technology+startup&hl=en-US&gl=US&ceid=US:en"},
        {"name": "BuiltWorlds", "url": "https://builtworlds.com/feed/"},
        {"name": "建設テック (Google JP)", "url": "https://news.google.com/rss/search?q=%E5%BB%BA%E8%A8%AD%E3%83%86%E3%83%83%E3%82%AF+OR+%E5%9C%9F%E6%9C%A8%E3%83%86%E3%83%83%E3%82%AF+OR+%E3%82%B3%E3%83%B3%E3%83%86%E3%83%83%E3%82%AF&hl=ja&gl=JP&ceid=JP:ja"},
    ],
    "BIM×AI": [
        {"name": "BIM×AI (Google News)", "url": "https://news.google.com/rss/search?q=BIM+AI+construction&hl=en-US&gl=US&ceid=US:en"},
        {"name": "BIM×AI 日本語", "url": "https://news.google.com/rss/search?q=BIM+AI+%E5%BB%BA%E8%A8%AD&hl=ja&gl=JP&ceid=JP:ja"},
        {"name": "Autodesk Blog", "url": "https://adsknews.autodesk.com/feed"},
    ],
    "行政・研究機関 (BIM/CIM/AI)": [
        {"name": "国交省 BIM/CIM/AI (Google JP)", "url": "https://news.google.com/rss/search?q=site%3Amlit.go.jp+(BIM+OR+CIM+OR+AI+OR+%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD+OR+i-Construction)&hl=ja&gl=JP&ceid=JP:ja"},
        {"name": "国総研 BIM/CIM/AI (Google JP)", "url": "https://news.google.com/rss/search?q=site%3Anilim.go.jp+(BIM+OR+CIM+OR+AI+OR+%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD)&hl=ja&gl=JP&ceid=JP:ja"},
        {"name": "国交省動向 (Google JP)", "url": "https://news.google.com/rss/search?q=%E5%9B%BD%E5%9C%9F%E4%BA%A4%E9%80%9A%E7%9C%81+(BIM+OR+CIM+OR+AI+OR+i-Construction+OR+PLATEAU)&hl=ja&gl=JP&ceid=JP:ja"},
        {"name": "i-Construction (Google JP)", "url": "https://news.google.com/rss/search?q=i-Construction+OR+%E3%82%A4%E3%83%B3%E3%83%95%E3%83%A9DX&hl=ja&gl=JP&ceid=JP:ja"},
    ],
}

# 取得する日数（これ以前の記事は無視）
DAYS_BACK = int(os.environ.get("NEWS_DAYS", "1"))


def fetch_feed(feed_info):
    """1つのフィードを取得し、記事リストを返す"""
    articles = []
    cutoff = datetime.now() - timedelta(days=DAYS_BACK)

    try:
        d = feedparser.parse(feed_info["url"])
        for entry in d.entries[:10]:  # 各フィード最大10件
            # 日付パース
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])

            # 日付フィルター（日付不明の場合は含める）
            if published and published < cutoff:
                continue

            title = entry.get("title", "(タイトルなし)")
            title = html.unescape(title).strip()
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            # HTMLタグ除去
            summary = re.sub(r"<[^>]+>", "", html.unescape(summary)).strip()
            if len(summary) > 200:
                summary = summary[:200] + "..."

            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "date": published.strftime("%Y-%m-%d %H:%M") if published else "不明",
            })
    except Exception as e:
        print(f"  ⚠ {feed_info['name']}: {e}")

    return articles


def generate_markdown(all_results, date_str, translations=None):
    """全カテゴリの結果をMarkdownにまとめる（日本語翻訳付き）"""
    if translations is None:
        translations = {}

    lines = [
        f"# デイリーニュース - {date_str}",
        f"_自動取得: {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
    ]

    total = 0
    for category, feeds_data in all_results.items():
        category_articles = []
        for feed_name, articles in feeds_data:
            category_articles.extend([(feed_name, a) for a in articles])

        if not category_articles:
            continue

        lines.append(f"## {category}")
        lines.append("")

        for feed_name, article in category_articles:
            total += 1
            tr = translations.get(id(article))
            title = tr["title_ja"] if tr else article["title"]
            summary = tr["summary_ja"] if tr else article["summary"]

            lines.append(f"### {title}")
            lines.append(f"- **ソース**: {feed_name} | **日時**: {article['date']}")
            if article["link"]:
                lines.append(f"- **URL**: {article['link']}")
            if summary:
                lines.append(f"- {summary}")
            lines.append("")

    lines.append(f"---\n_合計 {total} 件取得_")
    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"📰 ニュース取得開始 ({date_str})")
    print(f"   対象期間: 過去{DAYS_BACK}日")
    print()

    all_results = {}
    for category, feeds in FEEDS.items():
        print(f"📂 {category}")
        feeds_data = []
        for feed_info in feeds:
            articles = fetch_feed(feed_info)
            feeds_data.append((feed_info["name"], articles))
            count = len(articles)
            status = f"  ✅ {feed_info['name']}: {count}件" if count else f"  - {feed_info['name']}: 0件"
            print(status)
        all_results[category] = feeds_data
        print()

    # 日本語翻訳
    print("🌐 日本語翻訳中...")
    translations = translate_to_japanese(all_results)
    if translations:
        print(f"  ✅ {len(translations)}件を翻訳")
    else:
        print("  ⚠ 翻訳スキップ（GOOGLE_API_KEY未設定 or エラー）")
    print()

    # Markdown生成・保存
    md = generate_markdown(all_results, date_str, translations)
    output_path = os.path.join(OUTPUT_DIR, f"{date_str}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"💾 保存: {output_path}")

    # 古いニュースの自動クリーンアップ（30日以上前）
    cleanup_cutoff = datetime.now() - timedelta(days=30)
    for fname in os.listdir(OUTPUT_DIR):
        if fname.endswith(".md"):
            try:
                fdate = datetime.strptime(fname.replace(".md", ""), "%Y-%m-%d")
                if fdate < cleanup_cutoff:
                    os.remove(os.path.join(OUTPUT_DIR, fname))
                    print(f"🗑  古いニュース削除: {fname}")
            except ValueError:
                pass


if __name__ == "__main__":
    main()
