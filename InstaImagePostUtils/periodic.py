from queue import PriorityQueue
from shutil import rmtree
import os
import time
import InstaImagePostUtils
import threading


def initialize_pq(pq: PriorityQueue, uploads_dir: str):
    for d in os.listdir(uploads_dir):
        d_path = os.path.join(uploads_dir, d)
        if os.path.isfile(d_path):
            # Remove files because they shouldn't be there.
            os.remove(d_path)
            break
        mtime = os.stat(d_path).st_mtime
        entry = (mtime, d)
        pq.put(entry)


def delete_old_image_dirs():
    pq = InstaImagePostUtils.pq
    threshold_s = InstaImagePostUtils.IMAGE_KEEP_TIME_S
    while not pq.empty() and (time.time() - pq.queue[0][0] > threshold_s):
        dname = pq.get()[1]
        InstaImagePostUtils.app.logger.info(f"Deleting {dname}")
        try:
            rmtree(os.path.join(InstaImagePostUtils.app.config["FULL_UPLOAD_FOLDER"], dname))
        except FileNotFoundError:
            InstaImagePostUtils.app.logger.info(f"Error deleting {dname}")


def exec_every_n_seconds(n):
    counter = 1
    while True:
        counter += 1
        pre = time.time()
        delete_old_image_dirs()
        drift = time.time() - pre
        time.sleep(n - drift/ 1e6)
