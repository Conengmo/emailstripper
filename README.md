# emailstripper

Extract attachments from local mbox files. 

The goal is to reduce the size of the mbox file and store attachments you want to keep separately.

Python code that:
- walks over mbox files in a directory
- walks over messages in an mbox file
- finds attachments larger than a certain size (currently 200 kB hardcoded)
- stores the attachment to a folder
- replaces the attachment in the message with a line of text
- replaces the message in the mbox file
