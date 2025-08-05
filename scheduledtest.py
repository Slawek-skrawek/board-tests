import schedule
import time
import sendmail
import watchdogtest


def run_weekly_test():
    print("Running weekly test.")
    result_file = watchdogtest.run(h_serial='2')
    print("Newest file by name: ", result_file)
    sendmail.send_email(result_file)


# Schedule the job: every Friday at 18:00
schedule.every().tuesday.at("18:00").do(run_weekly_test)

print("Scheduler started. Waiting for jobs...")

while True:
    schedule.run_pending()
    time.sleep(1)  # check every second
