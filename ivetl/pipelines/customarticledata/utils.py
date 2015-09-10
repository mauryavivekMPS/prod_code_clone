def parse_custom_data_line(line):
    return {
        'doi': line[0].strip(),
        'toc_section': line[1].strip(),
        'collection': line[2].strip(),
        'editor': line[3].strip(),
        'custom': line[4].strip(),
        'custom_2': line[5].strip(),
        'custom_3': line[6].strip()
    }
