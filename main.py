import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from ping3 import ping
import requests

from zzupy.exception import NetworkError, ParsingError
from zzupy.web import EPortalClient, discover_portal_info

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

CHECK_URL = "http://www.baidu.com"
# CHECK_URL = "http://www.ys.mihoyo.com"
CHECK_INTERVAL_SECONDS = 10
REQUEST_TIMEOUT_SECONDS = 2

ENV_FILE = Path(__file__).resolve().with_name(".env")
load_dotenv(ENV_FILE, interpolate=False)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(
            f"缺少环境变量 {name}。请复制 .env.example 为 .env 并填写真实配置。"
        )
    return value


ZZU_USERNAME = require_env("ZZU_USERNAME")
ZZU_PASSWORD = require_env("ZZU_PASSWORD")

# 邮箱配置
SMTP_SERVER = "mail.v.zzu.edu.cn"  # 发信服务器
SMTP_PORT = 465                    # SSL 端口 (注意：465通常对应SSL加密)

SENDER_EMAIL = require_env("SENDER_EMAIL")
SENDER_PASSWORD = require_env("SENDER_PASSWORD")

RECEIVER_EMAIL = require_env("RECEIVER_EMAIL")  # 接收邮件的邮箱

EMAIL_SUBJECT = "电台室校园网状态警报"
EMAIL_SENDER_NAME = "电台室电脑"     # 发件人显示名称
EMAIL_BODY_TEMPLATE = """

"""


def send_email(
    receiver_email: str = RECEIVER_EMAIL,
    email_subject: str = EMAIL_SUBJECT,
    email_body_template: Optional[str] = None,
):
    try:
        send_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_template = email_body_template or EMAIL_BODY_TEMPLATE
        email_body = final_template.format(
            send_time=send_time,
            sender_email=SENDER_EMAIL,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
        )

        # --- 步骤 1: 构建邮件内容 ---
        msg = MIMEMultipart()
        msg['From'] = formataddr([EMAIL_SENDER_NAME, SENDER_EMAIL])
        msg['To'] = formataddr(["收件人", receiver_email])
        msg['Subject'] = email_subject

        # 添加邮件正文
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))

        # --- 步骤 2: 连接服务器 (使用 SSL) ---
        print(f"正在通过 SSL 连接服务器 {SMTP_SERVER}:{SMTP_PORT} ...")
        
        # 关键修改：端口 465 必须使用 SMTP_SSL，不需要调用 starttls()
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        
        # --- 步骤 3: 登录 ---
        print("正在登录告警邮箱...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # --- 步骤 4: 发送 ---
        print("正在发送邮件...")
        server.sendmail(SENDER_EMAIL, [receiver_email], msg.as_string())
        
        # --- 步骤 5: 退出 ---
        server.quit()
        print("✅ 邮件发送成功！")
        print("已发送至告警收件箱。")
        print(f"主题: {email_subject}")
        print(f"内容: {email_body}")

    except smtplib.SMTPAuthenticationError:
        print("❌ 登录失败：用户名或密码错误。")
        print("提示：如果密码无误，请检查网页版邮箱设置，确认是否开启了'SMTP/IMAP服务'。")
    except Exception as e:
        print(f"❌ 发送失败，错误信息: {e}")

def is_online_ping(host,timeout: int = REQUEST_TIMEOUT_SECONDS):
    # 同样需要清理 url
    host = host.replace("http://", "").replace("https://", "").split("/")[0]
    
    try:
        # timeout 设置超时时间（秒）
        response = ping(host, timeout)
        
        # 如果 ping 成功，返回的是延迟时间（float）；如果失败，返回 None 或 False
        if response is None or response is False:
            print(f"Ping {CHECK_URL} 网站失败！")
            return False
        else:
            print(f"Ping {host} 成功，延迟时间: {response * 1000} ms")
            return response * 1000  # 转换为毫秒
    except Exception as e:
        print(f"Ping {CHECK_URL} 网站时发生异常！错误信息: {e}")
        return False


def is_online() -> bool:
    """Return True when outbound http traffic is not hijacked by the portal."""
    try:
        response = requests.get(
            CHECK_URL,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=False,
            headers = {'Connection': 'close'},
        )
        print(f"访问 {CHECK_URL} 成功，状态码: {response.status_code}，内容长度: {len(response.content)}")
    except requests.RequestException as exc: 
        print(f"访问 {CHECK_URL} 失败。错误信息: {exc}")
        return False
    
	# 如果内容过少，说明被劫持了
    # 测试得到校园网登录界面的内容长度为373，直接和400比方便
    if len(response.content) < 400:
        print(f"访问 {CHECK_URL} 内容过少，可能已掉线，长度: {len(response.content)}")
        return False
        
    if response.status_code == 204:
        return True

    if response.status_code in {200, 301, 307, 308}:
        redirect_target = response.headers.get("Location") or response.url
        if redirect_target and "baidu.com" in redirect_target:
            return True

        if response.status_code == 200 and "baidu.com" in response.text:
            return True
    print("访问未通过验证，可能已掉线。")
    return False


def attempt_login(username: str, password: str):
    try:
        portal_info = discover_portal_info()
        with EPortalClient(
            portal_info.portal_server_url,
            bind_address=portal_info.user_ip,
            force_bind=True,
        ) as client:
            result = client.auth(username, password)
            print(result.message)
            return bool(getattr(result, "success", False))
    except ParsingError as exc:
        print(f"登录失败: {exc}")
        return 10
    except NetworkError as exc:
        print(f"登录失败: {exc}")
        return 20


def monitor_login_state_once(username: str, password: str) -> None:
    try:
        offline_detected = False
        while True:
            is_network_online = (pingTime := is_online_ping(CHECK_URL,REQUEST_TIMEOUT_SECONDS)) and is_online()
            if not is_network_online:
                if not offline_detected:
                    offline_detected = True
                    print("检测到掉线，尝试重新登录…")
                success = attempt_login(username, password)
                print(f"登录尝试结果代码: {success}")
                if success == 10:
                    print(f"将在 {CHECK_INTERVAL_SECONDS} 秒后重试。")
                elif success == 20:
                    print("请检查是否连接校园网")
                    break
            else:
                print("当前网络在线。")
                if offline_detected:
                    print("检测到网络恢复，正在发送通知邮件…")
                    email_body_template = f"""
警告：
于{{send_time}}，实验室电脑检测到校园网掉线！
如果看到这行，说明网络已恢复正常！目前可以正常访问外网。
为了避免网络波动,请检查组网情况。
服务器网络状态：   百度: {pingTime} ms       
                哔哩哔哩: {is_online_ping("bilibili.com",REQUEST_TIMEOUT_SECONDS)} ms
                原神: {is_online_ping("ys.mihoyo.com",REQUEST_TIMEOUT_SECONDS)} ms
"""
                    send_email(
                        email_subject="NAS校园网出现掉线警报",
                        email_body_template=email_body_template,
                    )
                    offline_detected = False
                break
            time.sleep(CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("已停止登录监控。")
        print("（主动停止：KeyboardInterrupt）")
    except Exception as e:
        print(f"发生意外错误: {e}")




if __name__ == "__main__":
    print("正在检测校园网登录状态……")
    monitor_login_state_once(ZZU_USERNAME, ZZU_PASSWORD)






