# Copyright 2023 Grant Brady
# Use of this source code is governed by an MIT-style license that can be found in the LICENSE file
import os
import time
import shutil
import sqlite3
import ffmpeg
from win10toast import ToastNotifier

# Set the directory to watch for new gifs
directory = "C:\\Users\\bragr\\Downloads"

# Connect to the sqlite database
conn = sqlite3.connect('known_files.db')
c = conn.cursor()

# Create the table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS files
             (name text, size real)''')
conn.commit()

# Define the minimum file size for transcoding (1MB)
MIN_FILE_SIZE = 1000000

# Create a notifier object for Windows desktop notifications
toaster = ToastNotifier()

while True:
    # Get a list of all files in the directory
    files = os.listdir(directory)

    # Loop through the files
    for file in files:
        # Check if the file is a gif and larger than the minimum size
        if file.endswith('.gif') and os.path.getsize(os.path.join(directory, file)) > MIN_FILE_SIZE:
            # Check if the file has already been processed
            c.execute("SELECT * FROM files WHERE name=?", (file,))
            result = c.fetchone()
            if result:
                continue  # File already processed, skip to next file

            # Transcode the gif to mp4 using ffmpeg
            input_path = os.path.join(directory, file)
            output_path = os.path.splitext(input_path)[0] + '.mp4'
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(stream, output_path)
            ffmpeg.run(stream)

            # Add the file to the database
            size = os.path.getsize(output_path)
            c.execute("INSERT INTO files VALUES (?, ?)", (file, size))
            conn.commit()

            # Display a Windows desktop notification for the transcoded file
            toaster.show_toast("File transcoded", f"{file} has been transcoded to MP4", duration=5)

    # Sleep for 2 seconds before checking again
    time.sleep(2)
