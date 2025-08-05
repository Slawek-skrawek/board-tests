import json
import smtplib
from email.message import EmailMessage
import mimetypes
import os
import sys
import config

password = os.environ["EMAIL_APP_PASSWORD"]


def send_email(sent_file=None):
    # Load JSON data
    with open(f"{config.PYTHON_PATH}jsons/email_cfg.json", "r") as file:
        cfg = json.load(file)

    with open(sent_file, "r") as file:
        results = json.load(file)

    rows = ""
    hub_serial = results["Hub serial"]
    for test in results["Watchdog tests"]:
        port = test["Port"]
        board = test["Board name"]
        board_serial = test["Board serial"]
        status = test["Test passed"]
        icon = "✅" if status is True else "❌"
        color = "green" if status is True else "red"
        rows += (f"<tr>"
                 f"<td>{port}</td>"
                 f"<td>{board}</td>"
                 f"<td>{board_serial}</td>"
                 f"<td style='color:{color};'>{icon} {status}</td>"
                 f"</tr>")

    html_body = f"""
    <html>
      <body>
        <h2 style="color: steelblue;">Test Report</h2>
        <h3>Watchdog Tests</h3>
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse;">
          <caption>Watchdog tests for hub {hub_serial}</caption>
          <tr>
            <th>Port number</th>
            <th>Board name</th>
            <th>Board serial</th>
            <th>Test passed</th>
          </tr>
          {rows}
        </table>
        <p>{os.path.basename(sent_file)}</p>
      </body>
    </html>
    """

    # Compose the email
    msg = EmailMessage()
    msg["From"] = cfg["sender"]

    recipients = cfg["recipients"]
    if isinstance(recipients, list):
        msg["To"] = ", ".join(recipients)
    else:
        msg["To"] = recipients
        recipients = [recipients]  # Ensure it's a list for sending
    msg["Subject"] = cfg["subject"]
    msg.set_content("This is a fallback plain-text version.")
    msg.add_alternative(html_body, subtype='html')

    with open(f"{config.PYTHON_PATH}jsons/preview_email.html", "w", encoding="utf-8") as f:
        f.write(html_body)

    print("Preview written to preview_email.html — open it in your browser.")

    # Add attachment if provided
    attachment_path = sent_file
    if attachment_path and os.path.isfile(attachment_path):
        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(attachment_path)
        mime_type = mime_type or "application/octet-stream"
        maintype, subtype = mime_type.split("/")

        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
            msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)

    # Send the email
    try:
        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["username"], password)
            server.send_message(msg, to_addrs=recipients)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")


def main():
    send_email()


if __name__ == "__main__":
    main()
