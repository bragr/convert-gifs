# Copyright 2023 Grant Brady
# Use of this source code is governed by an MIT-style license that can be found in the LICENSE file
import os
import time
import sqlite3
import pathlib
import ffmpeg
from win10toast import ToastNotifier

# Set the directory to watch for new gifs
DIRECTORY = f"{pathlib.Path.home()}{os.path.sep}Downloads"
# Define the minimum file size for transcoding (1MB)
MIN_FILE_SIZE = 1000000


def setup_sqlite():
    # Connect to the sqlite database
    conn = sqlite3.connect('known_files.db')
    c = conn.cursor()

    # Create the table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (name text, size real)''')
    conn.commit()

    mem_conn = sqlite3.connect(':memory:')
    conn.backup(mem_conn)
    mem_c = mem_conn.cursor()
    print("Database loaded into memory")

    return mem_conn, mem_c, conn


def main():
    conn, c, file_conn = setup_sqlite()
    # Create a notifier object for Windows desktop notifications
    toaster = ToastNotifier()

    try:
        files = os.listdir(DIRECTORY)
        c.execute('SELECT name FROM files')
        for row in c.fetchall():
            if row[0] not in files:
                c.execute('DELETE FROM files WHERE name=?', (row[0],))

        conn.commit()

        while True:
            # Get a list of all files in the directory
            files = os.listdir(DIRECTORY)

            # Loop through the files
            for file in files:
                # Check if the file is a gif and larger than the minimum size
                if file.endswith('.gif') and \
                   c.execute("SELECT * FROM files WHERE name=?", (file,)).fetchone() is None and \
                   os.path.getsize(os.path.join(DIRECTORY, file)) > MIN_FILE_SIZE:
                    # Transcode the gif to mp4 using ffmpeg
                    input_path = os.path.join(DIRECTORY, file)
                    output_path = os.path.splitext(input_path)[0] + '.mp4'
                    stream = ffmpeg.input(input_path)
                    stream = ffmpeg.output(stream, output_path)
                    ffmpeg.run(stream)

                    # Add the file to the database
                    size = os.path.getsize(output_path)
                    c.execute("INSERT INTO files VALUES (?, ?)", (file, size))
                    conn.commit()

                    # Display a Windows desktop notification for the transcoded file
                    toaster.show_toast("File transcoded", f"{file} has been transcoded to MP4", duration=3, threaded=True)

            # Sleep for 1 second before checking again
            time.sleep(1)
    finally:
        conn.backup(file_conn)
        conn.close()
        file_conn.close()
        print("Database backed up and closed")


if __name__ == '__main__':
    main()
