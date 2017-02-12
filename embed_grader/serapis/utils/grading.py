import struct

from serapis.models import *


def _get_words_from_line(line):
    words = [x.strip() for x in line.split(',')]
    if len(words) != 3:
        return None
    try:
        return (chr(int(words[0])), int(words[1]), int(words[2]))
    except:
        return None

def _format_error_message(line_idx, msg):
    return "Error line %d: %s" % (line_idx, msg)

def check_format(file_content):
    # split file string by new line
    lines = file_content.decode('UTF-8').strip().split('\n')
    packets = []
    for line_idx, line in enumerate(lines, 1):
        packet = _get_words_from_line(line)
        if not packet:
            return (False, _format_error_message(
                line_idx, "Format error"))
        packets.append(packet)

    # first line should be a "P" packet
    # P packet contains number of packets in the payload 
    # (i.e. number of packets after the first two packets)
    pk_type, pk_num_lines, _ = packets[0]
    if pk_type != 'P':
        return (False, _format_error_message(1, "First packet is not P packet"))
    if pk_num_lines != len(lines) - 2:
        return (False, _format_error_message(
            1, "Payload length does not match length in P packet"))
    if pk_num_lines <= 0:
        return (False, _format_error_message(
            1, "Empty waveform file"))

    # second packet has to be an "L" packet
    # L packet contains the total number of ticks for
    # which the output waveform should be recorded
    pk_type, pk_timestamp, _ = packets[1]
    if pk_type != 'L':
        return (False, _format_error_message(
            2, "Second packet is not L packet"))
    max_timestamp = pk_timestamp

    # The third packet, i.e. right after L packet, should have a timestamp
    # of "0"
    _, pk_timestamp, _ = packets[2]
    if pk_timestamp != 0:
        return (False, _format_error_message(
            3, "Third packet should have timestamp 0"))

    # After the P and L packets, the rest should be either "D" or "A" packets
    # Expected packet format: "D/A, timestamp, digital/analog value in
    # bitstream"

    # The timestamp should increase monotonically
    prev_time = -1
    for line_idx, packet in enumerate(packets[2:], 1):
        pk_type, pk_time, pk_valu = packet
        
        # packet type should be "D" or "A"
        if pk_type != 'D' and pk_type != 'A':
            return (False, _format_error_message(line_idx,
                "Expected either 'D' or 'A' packet, but received %s" % pk_type))

        # timestamps should increase monotonically
        if prev_time >= pk_time:
            return (False, _format_error_message(
                line_idx, "Timestamp not in order"))
        
        # timestamp should not exceed max
        if pk_time > max_timestamp:
            return (False, _format_error_message(
                line_idx, "Timestamp exceeds specified maximum"))
        
        # update prev_time
        prev_time = pk_time
    
    return (True, "Pass")


def check_format_by_filename(filename):
    with open(filename, 'rb') as f:
        return check_format(f.read())


def get_length(file_content):
    # Assuming file format has already been verified
    # split file string by new line
    lines = file_content.decode('UTF-8').strip().split('\n')

    # second packet has to be an "L" packet
    pk_type, pk_timestamp, _ = _get_words_from_line(lines[1])
    return pk_timestamp


def get_length_by_filename(filename):
    with open(filename, 'rb') as f:
        return get_length(f.read())

   
def get_last_fully_graded_submission(author, assignment):
    """
    Return:
      a Submission object which is the last fully graded submission
    """
    submission_list = Submission.objects.filter(
            student_id=author, assignment_id=assignment).order_by('-id')
    for s in submission_list:
        if s.is_fully_graded(include_hidden=True):
            return s
    return None

# def get_submission_with_hightest_score(author, assignment):
#     """
#     Return:
#       a submission object which has the highest score

#     """

#     submission_list = Submission.objects.filter(student_id=author, assignment_id=assignment)
