import schedule
import time
import sendmail
import watchdogtest


def run_daily_test():
    print("Running daily test.")
    result_file = watchdogtest.run(h_serial='2')
    print("Newest file by name: ", result_file)
    sendmail.send_email(result_file)


def main():
    # Schedule the job: every day at 18:00
    schedule.every().day.at("18:00").do(run_daily_test)

    print("Scheduler started. Waiting for jobs...")

    while True:
        schedule.run_pending()
        time.sleep(1)  # check every second


if __name__ == "__main__":
    main()
