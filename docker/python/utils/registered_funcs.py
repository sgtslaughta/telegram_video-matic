from .file_utils import scan_video_directory


def print_thing(name):
    print("\tHERE WE GO! ", name)


def test_func(name):
    print(f"\tTest func here baby! {name}")


def scan_videos(directory):
    print(f"Scanning directory: {directory}")
    videos = scan_video_directory(directory)
    for video in videos:
        print(f"Video: {video}")
        for key, value in videos[video].items():
            print(f"\t{key}: {value}")
        print("\n")
