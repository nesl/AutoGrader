import sys
import numpy

TASK_ID = 0
TASK_ID = 5
TOLERENCE = 1
PIN_IDX = 0


def grade(time_series, st, et, P, R):
    exp_period_ticks = (P + 1) * 50
    exp_on_ticks = exp_period_ticks * R / 100
    if R == 0 or R >= 100:  # corner cases
        st_interest = st + 50 + 2 * exp_period_ticks
        et_interest = et - 2 * exp_period_ticks
        on_ratio = numpy.mean(time_series[st_interest:et_interest])
        if R == 0:
            return max(0., (on_ratio - 0.001) * -1000.)
        elif R == 100:
            return max(0., (on_ratio - 0.999) * 1000.)
    else:
        st_interest = st + 50 + exp_period_ticks
        et_interest = et - exp_period_ticks
        rising_edges = [i+1 for i in range(st_interest, et_interest - 1) if time_series[i] == 0 and time_series[i+1] == 1]
        #print(rising_edges)
        if len(rising_edges) < 5:
            return 0.
        on_durations = [sum(time_series[rising_edges[i]:rising_edges[i+1]]) for i in range(len(rising_edges) - 1)]
        #print(on_durations, st, et, exp_period_ticks, exp_on_ticks)
        periods = [v for v in numpy.diff(rising_edges)]
        if rising_edges[0] - st_interest > exp_period_ticks:
            periods.append(rising_edges[0] - st_interest)
        if et_interest - rising_edges[-1] > exp_period_ticks:
            periods.append(et_interest - rising_edges[-1])
        period_penalty = (numpy.mean([max(0, abs(p - exp_period_ticks) - TOLERENCE) for p in periods]) ** 2) * 0.03
        ratio_penalty = (numpy.mean([max(0, abs(d - exp_on_ticks) - TOLERENCE) for d in on_durations]) ** 2) * 0.03
        return 1. - min(0.5, period_penalty) - min(0.5, ratio_penalty)

tasks = [
        {'length': 25000, 'sequence': [(0, 3, 40)]},
        {'length': 25000, 'sequence': [(0, 31, 100)]},
        {'length': 50000, 'sequence': [(0, 2, 20), (25000, 10, 80)]},
        {'length': 60000, 'sequence': [(0, 5, 10), (20000, 10, 40), (40000, 15, 90)]},
]

tasks.append({
    'length': 20000 * 20,
    'sequence': [(x * 20000, x, (8 * x + 10) % 102) for x in range(20)]
})
tasks.append({
    'length': 17500 * 40,
    'sequence': [(x * 17500, (x + 17) % 32, (1000 - 4 * x) % 102) for x in range(40)]
})

length = tasks[TASK_ID]['length']
sequence = tasks[TASK_ID]['sequence']

# read waveform file
wavfile = sys.argv[1]
events = []
with open(wavfile, 'r') as f:
    for line in f.readlines():
        packet = line.split(',')
        pktType = int(packet[0])
        pktTime = int(packet[1])
        pktVal = int(packet[2])
        if pktType == ord('D'):
            # get binary on/off PWM signal
            v = (pktVal & (1 << PIN_IDX)) >> PIN_IDX
            events.append( (pktTime, v) )

time_series = numpy.zeros(length, dtype=numpy.int)
events.append((length, 0))
for e_idx in range(len(events) - 1):
    s = max(0, events[e_idx][0])
    e = min(length, events[e_idx+1][0])
    time_series[s:e] = events[e_idx][1]

points = []
for i in range(len(sequence)):
    st = sequence[i][0]
    et = sequence[i+1][0] if i+1 < len(sequence) else length
    points.append(grade(time_series, st, et, sequence[i][1], sequence[i][2]))
final_result = numpy.mean(points)
print(final_result)
