#!/usr/bin/python

import os
import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from smtpd import COMMASPACE
from ssl import SSLError
from config.settings import EMAIL_USER, EMAIL_HOST, EMAIL_PORT, EMAIL_PASSWORD


STATUS_MAIL_SEND_SUCCEED = 0  # 成功的
STATUS_MAIL_SEND_FAILED = 1  # 失败的
STATUS_MAIL_SERVER_ERROR = 2  # 邮件服务器配置错误
STATUS_MAIL_SERVER_HOST_ERROR = 3  # 邮件服务器host为空
STATUS_MAIL_SERVER_USERNAME_ERROR = 4  # 邮件服务器用户名为空
STATUS_MAIL_SERVER_PASSWORD_ERROR = 5  # 邮件服务器密码为空
STATUS_MAIL_SUBJECT_NONE_ERROR = 6  # 邮件主题为空
STATUS_MAIL_SUBJECT_PARAMS_ERROR = 7  # 邮件主题参数格式错误
STATUS_MAIL_FROM_ADDRESS_NONE_ERROR = 8  # 邮件发送地址为空
STATUS_MAIL_FROM_ADDRESS_PARAMS_ERROR = 9  # 邮件发送地址参数格式错误
STATUS_MAIL_TO_ADDRESS_NONE_ERROR = 10  # 邮件目标地址为空
STATUS_MAIL_TO_ADDRESS_PARAMS_ERROR = 11  # 邮件目标地址参数格式错误
STATUS_MAIL_CONTENT_NONE_ERROR = 12  # 邮件内容为空
STATUS_MAIL_CONTENT_PARAMS_ERROR = 13  # 邮件内容参数错误
STATUS_MAIL_HELO_ERROR = 14  # 无法连接到邮件服务器
STATUS_MAIL_REJECTED_ALL_ERROR = 15  # 服务器拒绝所有接收方
STATUS_MAIL_SENDER_REFUSED_ERROR = 16  # 服务器拒绝发送地址请求
STATUS_MAIL_UNEXPECTED_CODE_ERROR = 17  # 服务器返回其他错代码


MAIL_STATUS_LIST = [
    (STATUS_MAIL_SEND_SUCCEED, '成功的'),
    (STATUS_MAIL_SEND_FAILED, '失败的'),
    (STATUS_MAIL_SERVER_ERROR, '邮件服务器配置错误'),
    (STATUS_MAIL_SERVER_HOST_ERROR, '邮件服务器host为空'),
    (STATUS_MAIL_SERVER_USERNAME_ERROR, '邮件服务器用户名为空'),
    (STATUS_MAIL_SERVER_PASSWORD_ERROR, '邮件服务器密码为空'),
    (STATUS_MAIL_SUBJECT_NONE_ERROR, '邮件主题为空'),
    (STATUS_MAIL_SUBJECT_PARAMS_ERROR, '邮件主题参数格式错误'),
    (STATUS_MAIL_FROM_ADDRESS_NONE_ERROR, '邮件发送地址为空'),
    (STATUS_MAIL_FROM_ADDRESS_PARAMS_ERROR, '邮件发送地址参数格式错误'),
    (STATUS_MAIL_TO_ADDRESS_NONE_ERROR, '邮件目标地址为空'),
    (STATUS_MAIL_TO_ADDRESS_PARAMS_ERROR, '邮件目标地址参数格式错误'),
    (STATUS_MAIL_CONTENT_NONE_ERROR, '邮件内容为空'),
    (STATUS_MAIL_CONTENT_PARAMS_ERROR, '邮件内容参数错误'),
    (STATUS_MAIL_HELO_ERROR, '无法连接到邮件服务器'),
    (STATUS_MAIL_REJECTED_ALL_ERROR, '服务器拒绝所有接收方'),
    (STATUS_MAIL_SENDER_REFUSED_ERROR, '服务器拒绝发送地址请求'),
    (STATUS_MAIL_UNEXPECTED_CODE_ERROR, '服务器返回其他错代码'),
]


# 邮件默认配置
DEFAULT_SERVER = {
    'HOST': EMAIL_HOST,
    'PORT': EMAIL_PORT,
    'MAIL_FROM': EMAIL_USER,
    'USERNAME': EMAIL_USER,
    'PASSWORD': EMAIL_PASSWORD,
    'MAIL_USER': EMAIL_USER,
}

"""
不再使用xml格式
为减小数据量，内部采用zip格式压缩邮件列表
批量发送邮件，支持邮件模板，动态替换模板参数，同时支持获取邮件发送是否成功状态
用法，比如：
    subject='感谢查看邮件'
    content="您好"
    lists=[{'email':'huangqing@idiaoyan.com','sex':'女','name':'lili'},{'email':'1035227236@qq.com','sex':'男','name':'lucy'}]
    result = sendEmails(subject, content, lists)
    if result:
        status = result['status']
        if int(status) != 0:
            print '邮件发送成功'
sendEmails返回json，如{"status":"1","id":"859"}，status为1，表示邮件服务器成功接受邮件发送请求
"""



def send_mail(
        mail_server: dict = DEFAULT_SERVER,
        mail_from: str = DEFAULT_SERVER['USERNAME'],
        mail_to: list = None,
        cc_to: list = None,
        subject: str = '提醒邮件',
        content: str = '',
        content_images: dict = None,
        attachments: list = None,
        ) -> int:
    """立即发送邮件

    :param mail_server: 邮件服务器
    :param mail_from: 发送邮箱
    :param mail_to: 接收邮箱
    :param cc_to: 抄送邮箱
    :param subject: 邮件主题
    :param content: 内容
    :param content_images: 附件图片资源
    :param attachments: 邮件附件
    :param smtp_id: 邮件服务器设置id
    :param mail_server: dict:  (Default value = DEFAULT_SERVER)
    :param mail_from: str:  (Default value = DEFAULT_SERVER['USERNAME'])
    :param mail_to: list:  (Default value = None)
    :param cc_to: list:  (Default value = None)
    :param subject: str:  (Default value = '提醒邮件')
    :param content: str:  (Default value = '')
    :param content_images: dict:  (Default value = None)
    :param attachments: list:  (Default value = None)

    """
    mail_mime = MIMEMultipart()
    # 邮件信息
    mail_to = list(set(mail_to))
    mail_mime['From'] = mail_from
    mail_mime['To'] = COMMASPACE.join(mail_to)
    mail_mime['CC'] = COMMASPACE.join(cc_to) if cc_to else ''
    mail_mime['Subject'] = Header(subject, 'utf-8')
    mail_mime['Date'] = formatdate(localtime=True)
    # 邮件内容
    html_content = MIMEText(content, 'html', 'utf-8')
    mail_mime.attach(html_content)
    # 邮件内容图片
    if isinstance(content_images, dict):
        for content_id, image_path in content_images.items():
            if image_path:
                image = open(image_path, 'rb')
                image_mime = MIMEImage(image.read())
                image_mime.add_header('Content-ID', content_id)
                image.close()
                mail_mime.attach(image_mime)
    # 邮件附件
    if isinstance(attachments, list):
        for attachment in attachments:
            a_mime = MIMEBase('application', 'octet-stream')
            a_file = open(attachment, 'rb')
            a_mime.set_payload(a_file.read())
            # Base64加密成字符串
            encoders.encode_base64(a_mime)
            a_mime.add_header(
                'Content-Disposition', 'attachment', filename=os.path.basename(attachment))
            mail_mime.attach(a_mime)
    try:
        if cc_to:
            mail_to.extend(cc_to)
        if mail_to:
            mail_to = list(set(mail_to))
        try:
            smtp = smtplib.SMTP_SSL(mail_server['HOST'],mail_server['PORT'])
        except SSLError:
            smtp = smtplib.SMTP(mail_server['HOST'],mail_server['PORT'])
        smtp.ehlo()

        smtp.login(mail_server['MAIL_USER'], mail_server['PASSWORD'])
        smtp.sendmail(mail_from, mail_to, mail_mime.as_string())
    except smtplib.SMTPHeloError as she:
        raise Exception("email send error:"+str(STATUS_MAIL_HELO_ERROR))
    except smtplib.SMTPRecipientsRefused as srr:
        raise Exception("email send error:"+str(STATUS_MAIL_REJECTED_ALL_ERROR))
    except smtplib.SMTPSenderRefused as ssr:
        raise Exception("email send error:"+str(STATUS_MAIL_SENDER_REFUSED_ERROR))
    except smtplib.SMTPDataError as sde:
        raise Exception("email send error:"+ str(STATUS_MAIL_UNEXPECTED_CODE_ERROR))
    finally:
        smtp.close()


if __name__ == '__main__':
    send_mail(mail_to=['1286345540@qq.com'],
                      subject='test',
                      content='test'
                      )