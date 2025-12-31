import os, time, shutil

BASE_DIR = "jobs"
MAX_AGE_HOURS = 6

def cleanup_jobs():
    now = time.time()
    for job in os.listdir(BASE_DIR):
        path = os.path.join(BASE_DIR, job)
        if not os.path.isdir(path):
            continue
        if now - os.path.getmtime(path) > MAX_AGE_HOURS * 3600:
            shutil.rmtree(path)
