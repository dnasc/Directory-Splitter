import argparse
from functools import wraps
import logging
import math
import os
import shutil
import sys
import time

logger = logging.getLogger('DIRSPLITTER')
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logger_formatter = logging.Formatter('%(asctime)s - %(name)s:%(levelname)s:%(message)s', '%Y-%m-%d %H:%M:%S')
stream_handler.setFormatter(logger_formatter)
logger.addHandler(stream_handler)

logger.propagate = False


def log_decorator(msg: str):
    def timer(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            t1 = time.time()
            r = f(*args, **kwargs)
            t2 = time.time()
            logger.info('It took {:.2f}s to {}.'.format(t2 - t1, msg))
            return r

        return wrapper

    return timer


@log_decorator('get file list')
def get_file_list(dir_path: str) -> list:
    """
    Get the list of files in a specific directory.

    :param dir_path: Directory path.
    :return: File list.
    """

    return sorted([os.path.join(dir_path, f) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])


def get_ith_sub_dir_name(split_dir_index: int, num_split_dirs: int) -> str:
    """
    Get the ith split directory name. For instance, if split_dir_index == 10 and num_split_dirs == 100 then '010' will
    be returned.

    :param split_dir_index: Split directory index.
    :param num_split_dirs: Number of split directories.
    :return: Sub directory name.
    """

    num_zeros = int(math.floor(math.log10(num_split_dirs)) - math.floor(math.log10(split_dir_index)))
    return '0' * num_zeros + str(split_dir_index)


def get_file_split_dir_index(file_index: int, num_split_dirs: int, num_files: int) -> int:
    """
    Get the split directory index where a specific file should be placed.

    :param file_index: File index - 1,2..,num_files
    :param num_split_dirs: Number of split directories.
    :param num_files: Number of files.
    :return: Split directory index.
    """

    num_files_p_split = num_files // num_split_dirs
    return (file_index - 1) // num_files_p_split + 1 if file_index <= num_files_p_split * num_split_dirs else num_split_dirs


@log_decorator('create split directories')
def create_split_dirs(parent_dir: str, num_split_dirs: int):
    """
    Create split directories.

    :param parent_dir: Directory where the split directories should be placed.
    :param num_split_dirs: Number of split directories.
    :return: None.
    """

    try:
        os.makedirs(parent_dir)
    except FileExistsError:
        pass

    for i in range(1, num_split_dirs + 1):
        sub_dir_name = get_ith_sub_dir_name(i, num_split_dirs)
        sub_dir_name = os.path.join(parent_dir, sub_dir_name)

        try:
            os.mkdir(sub_dir_name)
        except FileExistsError:
            pass


@log_decorator('split directory')
def split_directory(in_dir_path: str, out_dir_path: str, command: str, num_split_dirs: int):
    """
    Split a directory (in_dir_path) into num_split_dirs directories placed in out_dir_path.

    :param in_dir_path: Directory to be split.
    :param out_dir_path: Directory where split directories should be placed.
    :param command: Move or copy files from directory.
    :param num_split_dirs: Number of split directories.
    :return: None
    """

    bn_func = os.path.basename
    get_sub_dir_func = get_ith_sub_dir_name

    file_list = get_file_list(in_dir_path)
    num_files = len(file_list)

    logger.info('{} files to be split into {} directories'.format(num_files, num_split_dirs))

    create_split_dirs(out_dir_path, num_split_dirs)

    copy_or_move_func = shutil.move if command == 'm' else shutil.copy

    last_update_dir_index = 0
    n_k_print = 100

    for i, f_name in enumerate(file_list, 1):
        f_base_name = bn_func(f_name)

        sub_dir_index = get_file_split_dir_index(i, num_split_dirs, num_files)
        sub_dir_name = get_sub_dir_func(sub_dir_index, num_split_dirs)
        sub_dir_path = os.path.join(out_dir_path, sub_dir_name)

        new_f_name = os.path.join(sub_dir_path, f_base_name)

        copy_or_move_func(f_name, new_f_name)

        current_update_dir_index = sub_dir_index
        if last_update_dir_index != current_update_dir_index and current_update_dir_index % n_k_print == 0:
            logger.info('{} files into {} directory.'.format('Copying' if command == 'c' else 'Moving', sub_dir_name))

        last_update_dir_index = current_update_dir_index


def main():
    parser = argparse.ArgumentParser(description='Directory splitter utility.')
    parser.add_argument('-in_dir', help='Directory to be split into n directories.', required=True, type=str)
    parser.add_argument('-out_dir', help='Directory where the n split directories should be placed.', required=True,
                        type=str)
    parser.add_argument('-command', help='Move (m) or copy (c) files from split directory.', choices={'m', 'c'},
                        required=True)
    parser.add_argument('-n', help='Into how many directories the directory should be split.', type=int, required=True)
    parser.parse_args()

    args = parser.parse_args()
    in_dir = args.in_dir
    out_dir = args.out_dir
    num_split_dirs = args.n
    command = args.command

    split_directory(in_dir, out_dir, command, num_split_dirs)


if __name__ == '__main__':
    sys.exit(main())
