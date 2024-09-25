from .file_utils import scan_video_directory


def print_thing(name):
    print("\tHERE WE GO! ", name)


def test_func(name):
    print(f"\tTest func here baby! {name}")


def scan_files(directory):
    pass
    # print(f"Scanning directory: {directory}")
    videos = scan_video_directory(directory)
    print(f"Found {len(videos)} videos in {directory}")
