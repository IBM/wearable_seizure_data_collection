def read_wrist_id(filename):
    wrst_id_file = open(filename, 'r')
    Lines = wrst_id_file.readlines()

    count = 0
    # Strips the newline character
    id_dict = {}
    for line in Lines:
        #print("Line{}: {}".format(count, line.strip()))
        line = line.replace(',',' ')
        line = line.replace('-', ' ')
        line = ' '.join(line.split())
        # line format: 1, 1D - A001BC OR 1d4b13
        line = line.split(' ')
        wrst_id = line[0]
        bch_id = line[1]
        redcap_id_strs = line[2:]
        redcap_ids = []
        for redcap_id_str in redcap_id_strs:
            if redcap_id_str.upper() != 'OR':
                redcap_ids.append(redcap_id_str)

        id_dict[wrst_id] = redcap_ids

    return id_dict


if __name__ == '__main__':
    filename = 'wristband_id.txt'
    id_dict = read_wrist_id(filename)
    print(id_dict)

