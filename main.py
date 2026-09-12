import os
import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# ================= Configuration Area =================
# 从环境变量读取，或者在本地测试时直接替换为字符串
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")

# 发送频率设置：每2分钟发送10次
TOTAL_SENDS = 10
INTERVAL_SECONDS = 120 / TOTAL_SENDS  # 12秒一次

# ====================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def send_channel_report():
    """向频道发送报告的逻辑"""
    bot = Bot(token=TOKEN)
    
    # 构造你的报告内容，这里以时间戳为例
    message_text = f"📢 **自动化频道报告**\n🕒 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    for i in range(TOTAL_SENDS):
        try:
            # 发送消息
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=message_text,
                parse_mode="Markdown" # 支持 Markdown 格式化 [citation:8]
            )
            logger.info(f"发送成功: {i+1}/{TOTAL_SENDS}")
            
            # 如果不是最后一次发送，则等待间隔时间
            if i < TOTAL_SENDS - 1:
                await asyncio.sleep(INTERVAL_SECONDS)
                
        except TelegramError as e:
            logger.error(f"发送失败: {e}")
            # 遇到错误时稍作延迟，避免死循环
            await asyncio.sleep(5)

    logger.info("本轮发送任务完成。")

async def main():
    """主循环"""
    logger.info("机器人启动...")
    
    while True:
        try:
            await send_channel_report()
            # 等待下一轮周期（2分钟周期已包含在发送逻辑中，这里只需等待剩余的极短时间或直接重置周期）
            # 为了严格符合“每2分钟发送10次”，上一轮结束后稍微暂停一下再开始下一轮
            logger.info("等待 2 分钟进入下一轮...")
            await asyncio.sleep(120)
        except Exception as e:
            logger.error(f"主循环异常: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    if not TOKEN or not CHANNEL_ID:
        logger.error("缺少环境变量 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHANNEL_ID")
    else:
        asyncio.run(main())
