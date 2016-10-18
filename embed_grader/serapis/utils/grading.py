import struct

def get_words_from_line(line):
    return [x.strip() for x in line.strip().split(',')]

def check_format(file_content):
    #P packet contains number of packets in the payload 
    #(i.e. number of packets after the first two packets)
    has_p_packet = False
    #L packet contains the total number of ticks for
    #which the output waveform should be recorded
    has_l_packet = False
    max_timestamp = None
    

    #split file string by new line
    lines = file_content.decode('UTF-8').strip().split('\n')

    #first line should be a "P" packet
    p_packet = lines[0]
    words = get_words_from_line(p_packet)
    if chr(int(words[0]))=='P':
        has_p_packet = True
    else:
        return (False, "First packet is not P packet")
    
    #the length of payload specified in P packet should be correct
    if (len(words) != 3) or (int(words[1]) != (len(lines)-2)):
        print((int(words[1])), len(lines))
        return (False, "Payload length does not match length in P packet")

    #second packet has to be an "L" packet
    l_packet = lines[1]
    words = get_words_from_line(l_packet)
    if (len(words) == 3) and chr(int(words[0]))=='L':
        has_l_packet = True
        max_timestamp = int(words[1])
    else:
        return (False, "Second packet is not L packet")

    #The third packet, i.e. right after L packet, should have a timestamp of "0"
    time_0_packet = lines[2]
    words = get_words_from_line(time_0_packet)
    if (len(words) != 3) or (int(words[1])!=0):
        return (False, "Third packet should have timestamp 0")

    #After the P and L packets, the rest should be either "D" or "A" packets
    #Expected packet format: "D/A, timestamp, digital/analog value in bitstream" 
    #The timestamp should increase monotonically
    prev_time = -1
    for line in lines[2:]:
        words = get_words_from_line(line)

        #all lines should have three parts
        if len(words)!=3:
            return (False, "Packet length is not 3")

        #first letter should be "D" or "A"
        first_letter = chr(int(words[0]))
        if first_letter!='D' and first_letter!='A':
            return (False, ("Expected either 'D' or 'A' packet, but received %s"%first_letter)) 

        #timestamps should increase monotonically
        cur_time = int(words[1])
        if prev_time >= cur_time:
            return (False, "Timestamp not in order")
        
        #timestamp should not exceed max
        if cur_time > max_timestamp:
            return (False, "Timestamp exceeds specified maximum")
        
        #update prev_time
        prev_time = cur_time
    
    return (True, "Pass")


def check_format_by_filename(filename):
    with open(filename, 'rb') as f:
        return check_format(f.read())


def get_length(file_content):
    #Assuming file format has already been verified
    #split file string by new line
    lines = file_content.decode('UTF-8').strip().split('\n')

    #second packet has to be an "L" packet
    l_packet = lines[1]
    first_letter,time,_ = get_words_from_line(l_packet)
    if chr(int(first_letter))=='L':
        return int(time)
    else:
        return None

def get_length_by_filename(filename):
    with open(filename, 'rb') as f:
        return get_length(f.read())

#testing
#print(check_format_by_filename('sample.txt'))
    
