import subprocess
import os
import logging
from datetime import datetime
import pytz
import sys
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_and_push.log"),
        logging.StreamHandler()
    ]
)

# Set Indian timezone
IST = pytz.timezone('Asia/Kolkata')

def run_command(command, description):
    """Run a system command and log the output"""
    logging.info(f"Starting: {description}")
    try:
        # Use shell=True for node commands if needed, but list format is safer
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logging.info(f"Success: {description}")
            if result.stdout:
                logging.info(f"Output: {result.stdout.strip()}")
            return True
        else:
            logging.error(f"Error in {description}: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Exception during {description}: {e}")
        return False

def commit_and_push():
    """Commit and push changes to GitHub"""
    logging.info("Checking for changes to commit...")
    
    # Check if there are any changes
    status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if not status.stdout.strip():
        logging.info("No changes to commit (result likely not available yet).")
        return False
        
    # Git identity check (ensures it doesn't fail on new environments)
    subprocess.run(['git', 'config', '--global', 'user.name', 'Lottery Bot'], check=False)
    subprocess.run(['git', 'config', '--global', 'user.email', 'bot@lottery.com'], check=False)

    # Add, Commit, Push
    if run_command(['git', 'add', '.'], "Git Add"):
        commit_msg = f"Auto-update: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST"
        if run_command(['git', 'commit', '-m', commit_msg], "Git Commit"):
            # Push specifically to the main branch from current HEAD
            # This triggers the GitHub Pages deployment.
            return run_command(['git', 'push', 'origin', 'HEAD:main'], "Git Push to Main")
    return False

def main():
    logging.info("=== Starting Kerala Lottery Update Task ===")
    
    # 0. Sync with GitHub first
    # This cleans up the repo and ensures we have the latest code from main
    run_command(['git', 'fetch', 'origin'], "Git Fetch")
    run_command(['git', 'reset', '--mix', 'origin/main'], "Git Sync (Reset to Remote Main)")
    
    # 1. Run the scraper
    # You can use 'main.py' or 'lottery_scraper.py'
    if not run_command([sys.executable, 'main.py'], "Lottery Scraper"):
        logging.warning("Scraper failed or had warnings, proceeding anyway...")

    # 2. Generate Manifest (Important for the web app to see new results)
    run_command(['node', 'generate-manifest.js'], "Manifest Generation")

    # 3. Generate History
    run_command(['node', 'generate-history.js'], "History Generation")

    # 4. Generate PDF Links
    run_command(['node', 'generate-pdf-links.js'], "PDF Link Generation")

    # 4. Push to GitHub
    if commit_and_push():
        logging.info("Update and push completed successfully!")
        return True
    else:
        logging.error("Failed to update GitHub.")
        return False

if __name__ == "__main__":
    # To run this up to 7 times automatically on PythonAnywhere:
    # It will stop as soon as it successfully pushes a new result.
    runs = 7
    delay_minutes = 15
    
    for i in range(runs):
        logging.info(f"--- Starting Run {i+1} of {runs} ---")
        success = main()
        
        if success:
            logging.info("Result found and pushed. Stopping further runs for today.")
            break
            
        if i < runs - 1:
            logging.info(f"Waiting {delay_minutes} minutes before next check...")
            time.sleep(delay_minutes * 60)
    
    logging.info("=== Daily update task finished. ===")
