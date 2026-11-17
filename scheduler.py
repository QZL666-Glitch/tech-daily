"""本地定时任务：每天按 config.yaml 里的时间自动跑一轮。

运行方式：python scheduler.py（保持窗口常开，或配合 Windows 计划任务自启）
"""
from apscheduler.schedulers.blocking import BlockingScheduler

from main import run_once
from src import config as config_mod


def main() -> None:
    cfg = config_mod.load_config()
    hour = cfg["schedule"].get("hour", 8)
    minute = cfg["schedule"].get("minute", 0)
    print(f"定时任务已启动：每天 {hour:02d}:{minute:02d} 运行一轮")

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(run_once, "cron", hour=hour, minute=minute,
                      args=[cfg], id="daily_publish")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("已停止。")


if __name__ == "__main__":
    main()
