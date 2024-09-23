import re
from datetime import datetime

def tokenize_and_extract_date(file_name):
    # Step 1: Clean the string by replacing undesired characters with spaces
    cleaned_string = re.sub(r'[._\-]+', ' ', file_name)

    # Step 2: Define the regex pattern to extract the date (supports day, month, and optional year)
    date_pattern = r"(\d{1,2})(?:th|st|nd|rd)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+(\d{4}))?"

    # Step 3: Search for the date in the cleaned string
    match = re.search(date_pattern, cleaned_string)

    if match:
        day = int(match.group(1))
        month = match.group(2)
        year = match.group(3)

        # If year is not present, use the current year
        if not year:
            year = datetime.now().year
        else:
            year = int(year)

        # Convert to datetime object
        date_str = f"{day} {month} {year}"
        date_obj = datetime.strptime(date_str, '%d %B %Y')

        # # Step 4: Remove the date part from the string for tokenization
        # cleaned_string = re.sub(date_pattern, '', cleaned_string)
    else:
        date_obj = None

    # Step 5: Tokenize the rest of the cleaned string into parts
    tokens = cleaned_string.strip().split()

    return tokens, date_obj



fname = "Bath_v_Northampton_Guinness_Premiership_20th_September_2024.mkv"
fname2 = "Newcastle Falcons v Bristol Bears - 20th September.mp4"
print(tokenize_and_extract_date(fname))  # ['Bath', 'v', 'Northampton', 'Guinness', 'Premiership', '20th', 'September', '2024', 'mkv']
print(tokenize_and_extract_date(fname2))  # ['Newcastle', 'Falcons', 'v', 'Bristol', 'Bears', '20th', 'September', 'mp4']


def nfo_creator(file_name, file_path, tokens=None):
    tokens, date_obj = tokenize_and_extract_date(file_name)
    if date_obj:
        date_str = date_obj.strftime('%Y-%m-%d')
    else:
        date_str = "Unknown"

    nfo = f"""
    <movie>
        <title>{' '.join(tokens)}</title>
        <year>{date_str}</year>
    </movie>
    """
    return nfo