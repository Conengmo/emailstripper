import mailbox
import email.mime.text
import os
import datetime as dt
import re


def parse_attachment(part):
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
    for param in dispositions[1:]:
        needle = 'filename'
        if needle in param.lower():
            start = param.lower().find(needle) + len(needle) + 1
            return param[start:].strip('"')
    else:
        return None


def store_attachment(part, msg, attachment_name, filename):
    store_filename = get_storage_filename(msg, attachment_name)
    store_folder = filename.rstrip('.mbox') + ' attachments'
    path = os.path.join('..', store_folder)
    if not os.path.exists(path):
        os.makedirs(path)
    content = part.get_payload(decode=True)
    with open(os.path.join(path, store_filename), 'wb') as f:
        f.write(content)


def get_replace_text(attachment_name, content_size):
    return email.mime.text.MIMEText('Attachment "{}" with size {:.0f} kB has been removed ({}).\r\n'
                                    .format(attachment_name, content_size / 1e3, dt.date.today()))


def get_storage_filename(msg, attachment_name):
    """Return a string that can be used as filename for storing the attachment."""
    date = dt.datetime.strptime(msg['Date'], '%a, %d %b %Y %H:%M:%S %z')
    date_str = date.strftime('%Y%m%dT%H%M')
    # Assume there is an email address in there:
    from_address = re.search(r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', msg['From']).group(0)
    res = '{} from-{} {}'.format(date_str, from_address, attachment_name)
    return res


def main():
    path = '..'
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
                        store_attachment(part, msg, attachment_name, filename)
                        payload = msg.get_payload()
                        payload[i] = get_replace_text(attachment_name, content_size)
                        msg.set_payload(payload)
                        mbox.__setitem__(key, msg)
                        count += 1
        finally:
            mbox.flush()
            mbox.close()
        print('Removed {} attachments from {}.'.format(count, filename))
        if filename.startswith('Cator'):
            raise RuntimeError()


if __name__ == '__main__':
    main()

