import mailbox
import os


def main(path):
    """Remove messages from a mbox files in path that were in Trash in Gmail."""
    for filename in os.listdir(path):
        if not filename.endswith('.mbox'):
            continue
        count = 0
        mbox = mailbox.mbox(os.path.join(path, filename))
        mbox.lock()
        try:
            for key, msg in mbox.items():
                if 'Trash' in msg.get('X-Gmail-Labels'):
                    mbox.remove(key)
                    count += 1
        finally:
            mbox.flush()
            mbox.close()
        print('Removed {} messages from {}.'.format(count, filename))


if __name__ == '__main__':
    main()
