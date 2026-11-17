"""公众号内容自动生成流水线入口 + 本地日报网站。

用法：
    python main.py               # 跑一轮：抓取 → 筛选 → 润色 → 生成文章 → 重建网站
    python main.py --dry-run     # 只抓取来源并打印候选，不调用大模型
    python main.py --site-only   # 只重建本地日报网站（不抓取、不花 API 费用）
"""
import argparse
from datetime import datetime

from src import config as config_mod
from src import site, storage
from src.llm import article as article_gen
from src.publish import fallback, wechat
from src.publish.html import to_wechat_html
from src.sources import aggregate


def print_banner() -> None:
    print("=" * 60)
    print(f"  公众号内容自动生成  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def build_site_only(cfg: dict) -> None:
    site_dir, n = site.build_site(cfg)
    print(f"本地日报网站已生成: {site_dir}")
    print(f"共 {n} 篇 · 双击 docs\\index.html 即可查看")


def run_once(cfg: dict, dry_run: bool = False) -> dict:
    print_banner()

    print("[1/5] 抓取来源...")
    items = aggregate.collect(cfg)
    print(f"      候选素材 {len(items)} 条")
    if not items:
        print("      没有找到新素材，仅重建网站。")
        build_site_only(cfg)
        return {"picked": [], "published": []}
    for it in items:
        print(f"      - [{it.source}] {it.title[:50]}")

    if dry_run:
        return {"picked": items, "published": []}

    results = []
    print(f"[2/5] 生成文章（共 {len(items)} 篇，调用大模型...）")
    for idx, it in enumerate(items, 1):
        try:
            article = article_gen.generate(it, cfg)
            paths = fallback.save_article(article, cfg["run"]["output_dir"])
            storage.record_article(
                cfg["run"]["data_dir"], datetime.now().strftime("%Y-%m-%d"),
                article["title"], paths["html"], it.url, "generated",
            )
            storage.mark_seen(cfg["run"]["data_dir"], it)
            results.append({"article": article, "item": it})
            print(f"      [{idx}/{len(items)}] {article['title']}")
        except Exception as e:
            print(f"      [{idx}/{len(items)}] 生成失败: {e}")

    print("[3/5] 发布...")
    published = []
    if cfg["wechat"].get("enabled") and cfg["run"].get("mode") == "publish":
        client = wechat.WeChatClient(cfg)
        for r in results:
            try:
                res = client.publish_article(
                    r["article"]["title"],
                    to_wechat_html(r["article"]["markdown"]),
                )
                published.append(res)
                print(f"      已提交发布: {r['article']['title']} -> {res}")
            except wechat.WeChatError as e:
                print(f"      发布失败（{r['article']['title']}）: {e}")
    else:
        print("      发布模式未开启，文章已生成到 output/。")

    print("[4/5] 重建本地日报网站...")
    try:
        site_dir, n = site.build_site(cfg)
        print(f"      网站已更新: {site_dir}（{n} 篇）")
    except Exception as e:
        print(f"      网站生成失败: {e}")

    print("[5/5] 完成")
    print(f"      生成 {len(results)} 篇，提交发布 {len(published)} 篇")
    return {"picked": items, "published": published}


def main() -> None:
    parser = argparse.ArgumentParser(description="公众号内容自动生成 + 本地日报网站")
    parser.add_argument("--dry-run", action="store_true", help="只抓取来源，不生成文章")
    parser.add_argument("--site-only", action="store_true", help="只重建本地日报网站")
    args = parser.parse_args()
    cfg = config_mod.load_config()
    if args.site_only:
        build_site_only(cfg)
        return
    run_once(cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
