import schedule
import time
import subprocess
import pytz
from datetime import datetime, time as dt_time
import threading
import os

# Set Indian timezone
IST = pytz.timezone('Asia/Kolkata')

def run_lottery_scraper():
    """Run the lottery scraper"""
    try:
        print(f"Running lottery scraper at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST")
        result = subprocess.run(['python', 'main.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Lottery scraper completed successfully")
            print(result.stdout)
        else:
            print(f"Error running lottery scraper: {result.stderr}")
    except Exception as e:
        print(f"Exception occurred: {e}")

def is_within_optimal_time_range():
    """Check if current time is between 2:45 PM and 5:30 PM IST"""
    now = datetime.now(IST)
    start_time = dt_time(14, 45)  # 2:45 PM
    end_time = dt_time(17, 30)   # 5:30 PM
    current_time = now.time()
    
    return start_time <= current_time <= end_time

def scheduled_task():
    """Task that runs every 15 minutes but only executes during specified hours"""
    if is_within_optimal_time_range():
        print("Within optimal time range - running lottery scraper")
        run_lottery_scraper()
    else:
        current_time = datetime.now(IST).strftime('%H:%M:%S')
        print(f"Current time {current_time} IST is outside optimal range (14:45-17:30)")

def run_scheduler():
    """Run the scheduler in a separate thread"""
    # Schedule the task to run every 15 minutes during the optimal window
    schedule.every(15).minutes.do(scheduled_task)
    
    print("Scheduler started - will check every 15 minutes")
    print("Active time: 2:45 PM to 5:30 PM IST daily")
    print("Press Ctrl+C to stop the scheduler")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Check if GitHub token is set
    if not os.environ.get('GITHUB_TOKEN'):
        print("WARNING: GITHUB_TOKEN not set. Auto-push to GitHub will not work.")
        print("Please set GITHUB_TOKEN in Replit Secrets for automatic GitHub pushes.")
    
    # Run one initial check
    print("Starting lottery result scheduler...")
    print(f"Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST")
    
    # Start the scheduler
    run_scheduler()