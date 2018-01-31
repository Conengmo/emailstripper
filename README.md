# emailstripper

Extract attachments from local mbox files. 

The goal is to reduce the size of the mbox file and store attachments you want to keep separately.

My use case is preparing the mbox files I got from Gmail with Google Takeout for storage. I extract the attachments and
remove those I don't need to keep.

The code is written in Python and it:
- walks over mbox files in a directory
- walks over messages in an mbox file
- finds attachments larger than a certain size (currently 200 kB hardcoded)
- stores the attachment to a folder
- replaces the attachment in the message with a line of text
- replaces the message in the mbox file
