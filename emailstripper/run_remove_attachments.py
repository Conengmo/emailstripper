import mailbox
import email.mime.text
import os
import datetime as dt
import dateutil.parser
import re


def main(path, filename=None):
    """Extract, store and remove attachments from all or a single mbox file in path."""
    iterator = [filename] if filename is not None else os.listdir(path)
    for filename in iterator:
        if not filename.endswith('.mbox'):
            continue
        count = 0
        mbox = mailbox.mbox(os.path.join(path, filename))
        mbox.lock()
        try:
            for key, msg in mbox.items():
                msg_date = msg['Date']
                msg_from = msg['From']
                count_before = count
                count = walk_over_parts(msg, count, path, filename, msg_date, msg_from)
                if count > count_before:
                    mbox.__setitem__(key, msg)
        finally:
            mbox.flush()
            mbox.close()
        print('Removed {} attachments from {}.'.format(count, filename))


def walk_over_parts(parent, count, path, filename, msg_date, msg_from):
    """Walk over the parts of a parent and try to remove attachments.
    
    This function works recursive. So parent is a message, or a part of a message, or a subpart of a part, etc.
    """
    if not parent.is_multipart():
        return count
    for i, part in enumerate(parent.get_payload()):
        if part.get_content_type() in ["text/plain", "text/html"]:
            continue
        if part.is_multipart():
            count = walk_over_parts(part, count, path, filename, msg_date, msg_from)
            return count
        content_size, attachment_name = parse_attachment(part)
        if content_size is not None and content_size > 100e3:
            print('Removing attachment {} with size {:.0f} kB.'.format(attachment_name, content_size / 1e3))
            store_attachment(part, attachment_name, filename, path, msg_date, msg_from)
            payload = parent.get_payload()
            payload[i] = get_replace_text(attachment_name, content_size)
            parent.set_payload(payload)
            count += 1
    return count


def parse_attachment(part):
    """Parse the message part and find whether it's an attachment."""
    if not part.get_content_disposition() in ['inline', 'attachment']:
        return None, None
    attachment_name = part.get_filename()
    if attachment_name.endswith('.eml'):
        print('Storing .eml files not supported, skipping {}.'.format(attachment_name))
        return None, None
    content = part.get_payload()
    assert type(content) is str
    content_size = len(content)
    return content_size, attachment_name


def store_attachment(part, attachment_name, filename, base_path, msg_date, msg_from):
    """Store an attachement as a file on disk."""
    store_filename = get_storage_filename(attachment_name, msg_date, msg_from)
    store_folder = filename.rstrip('.mbox') + ' attachments'
    path = os.path.join(base_path, store_folder)
    if not os.path.exists(path):
        os.makedirs(path)
    content = part.get_payload(decode=True)
    with open(os.path.join(path, store_filename), 'wb') as f:
        f.write(content)


def get_storage_filename(attachment_name, msg_date, msg_from):
    """Return a string that can be used as filename for storing the attachment."""
    try:
        date = dt.datetime.strptime(msg_date, '%a, %d %b %Y %H:%M:%S %z')
    except ValueError:
        date = dateutil.parser.parse(msg_date)
    date_str = date.strftime('%Y%m%dT%H%M')
    # Assume there is an email address in there:
    from_address = re.search(r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', msg_from).group(0)
    res = '{} from-{} {}'.format(date_str, from_address, attachment_name)
    # Replace characters not suitable for a filename:
    return re.sub(r'[<>:"\/\|\?\*\t\n\r\0]', r'-', res)


def get_replace_text(attachment_name, content_size):
    """Return a message object to replace an attachment with."""
    return email.mime.text.MIMEText('Attachment "{}" with size {:.0f} kB has been removed ({}).\r\n'
                                    .format(attachment_name, content_size / 1e3, dt.date.today()))


if __name__ == '__main__':
    main(path='C:\\Users\\Frank\\Downloads\\takeout')

