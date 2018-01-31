import mailbox
import email.mime.text
import os
import datetime as dt
import dateutil.parser
import re


def main(path):
    """Extract, store and remove attachments from mbox files in path."""
    for filename in os.listdir(path):
        if not filename.endswith('.mbox'):
            continue
        count = 0
        mbox = mailbox.mbox(os.path.join(path, filename))
        mbox.lock()
        try:
            for key, msg in mbox.items():
                if not msg.is_multipart():
                    continue
                for i, part in enumerate(msg.get_payload()):
                    if part.get_content_type() in ["text/plain", "text/html"]:
                        continue
                    content_size, attachment_name = parse_attachment(part)
                    if content_size is not None and content_size > 100e3:
                        print('Removing attachment {} with size {:.0f} kB.'.format(attachment_name, content_size / 1e3))
                        store_attachment(part, msg, attachment_name, filename, path)
                        payload = msg.get_payload()
                        payload[i] = get_replace_text(attachment_name, content_size)
                        msg.set_payload(payload)
                        mbox.__setitem__(key, msg)
                        count += 1
        finally:
            mbox.flush()
            mbox.close()
        print('Removed {} attachments from {}.'.format(count, filename))


def parse_attachment(part):
    """Parse the message part and find whether it's an attachment."""
    content_disposition = part.get("Content-Disposition", None)
    if not content_disposition:
        return None, None
    dispositions = content_disposition.strip().split(";")
    if not bool(content_disposition and dispositions[0].lower() == "attachment"):
        return None, None
    content = part.get_payload()
    content_size = len(content)
    attachment_name = get_attachment_name(dispositions)
    return content_size, attachment_name


def get_attachment_name(dispositions):
    """Parse the attachment filename from the email."""
    for param in dispositions[1:]:
        needle = 'filename'
        if needle in param.lower():
            start = param.lower().find(needle) + len(needle) + 1
            return param[start:].strip('"')
    else:
        return None


def store_attachment(part, msg, attachment_name, filename, base_path):
    """Store an attachement as a file on disk."""
    store_filename = get_storage_filename(msg, attachment_name)
    store_folder = filename.rstrip('.mbox') + ' attachments'
    path = os.path.join(base_path, store_folder)
    if not os.path.exists(path):
        os.makedirs(path)
    content = part.get_payload(decode=True)
    with open(os.path.join(path, store_filename), 'wb') as f:
        f.write(content)


def get_storage_filename(msg, attachment_name):
    """Return a string that can be used as filename for storing the attachment."""
    try:
        date = dt.datetime.strptime(msg['Date'], '%a, %d %b %Y %H:%M:%S %z')
    except ValueError:
        date = dateutil.parser.parse(msg['Date'])
    date_str = date.strftime('%Y%m%dT%H%M')
    # Assume there is an email address in there:
    from_address = re.search(r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', msg['From']).group(0)
    res = '{} from-{} {}'.format(date_str, from_address, attachment_name)
    # Replace characters not suitable for a filename:
    return re.sub(r'[<>:"\/\|\?\*\t\n\r\0]', r'-', res)


def get_replace_text(attachment_name, content_size):
    """Return a message object to replace an attachment with."""
    return email.mime.text.MIMEText('Attachment "{}" with size {:.0f} kB has been removed ({}).\r\n'
                                    .format(attachment_name, content_size / 1e3, dt.date.today()))


if __name__ == '__main__':
    main(path='C:\\Users\\Frank\\Downloads\\takeout')

