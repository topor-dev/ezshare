import argparse
import os
from pathlib import Path

try:
    from ezshare import server
except ImportError:
    import server

DEFAULT_PORT = 8000


def parse_argv() -> argparse.Namespace:
    parser = argparse.ArgumentParser('ezshare')
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument(
        '--share-only', '-s', action='store_true', help='disable upload function'
    )
    grp.add_argument(
        '--upload-only', '-u', action='store_true', help='disable share function'
    )
    parser.add_argument(
        '--port',
        '-p',
        nargs=1,
        type=int,
        default=DEFAULT_PORT,
        help='specify alternate port [default: %d]' % (DEFAULT_PORT,),
        metavar='n',
    )
    parser.add_argument(
        'path',
        nargs='?',
        type=lambda p: Path(p).resolve(),
        default=os.getcwd(),
        help='share/upload root directory',
    )
    return parser.parse_known_args()[0]


def main() -> None:
    args = parse_argv()
    print('started on port %d, path: %s' % (args.port, args.path))
    if not (args.share_only or args.upload_only):
        print('share and upload mode')
    else:
        print('share' if args.share_only else 'upload', 'only mode')
    try:
        server.serve(args.share_only, args.upload_only, args.port, args.path)
    except KeyboardInterrupt:
        print('KeyboardInterrupt, exiting')


if __name__ == '__main__':
    main()
