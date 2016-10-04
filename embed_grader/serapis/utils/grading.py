import struct


def check_format(binary):
    has_p_packet = False
    has_l_packet = False
    length = None
    cnt = 0
    prev_timestamp = -1
    length = 0

    if len(binary) % 9 != 0:
        return (False, "Corrupted file")

    num_packets = len(binary) // 9
    for cnt in range(num_packets):
        ts = cnt * 9
        te = (cnt + 1) * 9
        (sflag, cmd, timestamp, data, eflag) = struct.unpack('=ccIHc', binary[ts:te])
        try:
            sflag, cmd, eflag = sflag.decode('ascii'), cmd.decode('ascii'), eflag.decode('ascii')
        except:
            return (False, "Undecodable asciis")

        if sflag != 'S' or eflag != 'E':
            return (False, "Incorrect packet format")

        print(cmd, timestamp)
        if cnt < 2:
            if cmd == 'P':
                has_p_packet = True
            elif cmd == 'L':
                has_l_packet = True
                length = timestamp
            else:
                return (False, "Unexpected packet type in first 2 packets")
        else:
            if cmd != 'D' and cmd != 'A':
                return (False, "Expect waveform specific packet for the rest of files")
            if cnt == 2 and timestamp != 0:
                return (False, "Not start with timestamp 0")
            if timestamp <= prev_timestamp:
                return (False, "Timestamp not in order")
            if timestamp > length:
                return (False, "Timestamp exceeds specified length")
            prev_timestamp = timestamp

    if not has_p_packet:
        return (False, "No P-packet is found")
    if not has_l_packet:
        return (False, "No L-packet is found")

    return (True, "Pass")


def check_format_by_filename(filename):
    with open(filename, 'rb') as f:
        return check_format(f.read())


def get_length(binary):
    for i in range(2):
        ts = cnt * 9
        te = (cnt + 1) * 9
        (_, cmd, timestamp, _, _) = struct.unpack('=ccIHc', binary[ts:te])
        cmd = cmd.decode('ascii')
        if cmd == 'L':
            return timestamp
    return None


def get_length_by_filename(filename):
    with open(filename, 'rb') as f:
        return get_length(f.read())
