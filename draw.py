#this script should be executed on windows
import os, sys, re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import FormatStrFormatter
from interval import interval

FRAME_DURATION = 920    #718us(data) + 192us(preamble)
                        #for 1000 bytes packet at 11Mbps
GPIO_TO_DEVICE_DICT = {
    '27': 0,    #left node
    '17': 1,    #mid node
    '22': 2,    #right node
}

IDX_TO_DEVICE_NAME = ['left', 'mid', 'right']
IDX_TO_COLOR = ['r', 'g', 'b']
IDX_TO_Y_AXIS = [1, 3, 5]

SAVE_PDF_NAME = 'TX_timeline.pdf'

def parse_data(filename):
    if not os.path.isfile(filename):
        print('file %s don\'t exist' % filename)
        exit()
    timelines = [[], [], []]
    entry_regex = re.compile('^\[.*?\] \[\d+\.\d+\] GPIO: (\d{2}) falling$')
    rest_regex = re.compile('^\[.*?\] \[ *(\d+) us\] GPIO: (\d{2}) falling$')
    entry_found = False
    cur_time = None
    with open(filename) as f:
        for line in f:
            if not entry_found:
                m = entry_regex.match(line)
                if m:
                    gpio = m.group(1)
                    cur_time = FRAME_DURATION
                    entry_found = True
                else:
                    continue
            else:
                m = rest_regex.match(line)
                if m:
                    duration = int(m.group(1))
                    cur_time += duration
                    gpio = m.group(2)
                else:
                    continue
            timelines[GPIO_TO_DEVICE_DICT[gpio]].append((cur_time - FRAME_DURATION, cur_time,))
    if not entry_found:
        print('file doesn\'t contain data')
        exit()
    return timelines

def draw(timelines):
    fig, ax = plt.subplots()
    ax.xaxis.grid('on')
    max_x = 0   #get the longest x axis
    for idx in range(len(timelines)):
        name = IDX_TO_DEVICE_NAME[idx]
        color = IDX_TO_COLOR[idx]
        y = IDX_TO_Y_AXIS[idx]
        for interval in timelines[idx]:
            p = patches.Rectangle((interval[0] / 1000.0, y - 1),
                (interval[1] - interval[0]) / 1000.0, 2,
                facecolor=color, linewidth=0)
            ax.add_patch(p)
            max_x = max(max_x, interval[1])
    fig.set_size_inches(max_x / 1000.0, 1)
    ax.axis([0, max_x // 1000 + 1, 0, 6])
    ax.xaxis.set_ticks(range(0, max_x // 1000 + 1, 1))
    ax.yaxis.set_ticks(IDX_TO_Y_AXIS)
    ax.yaxis.set_ticklabels(IDX_TO_DEVICE_NAME)
    ax.tick_params(length=0)
    ax.xaxis.set_major_formatter(FormatStrFormatter("%dms"))
    fig.savefig(SAVE_PDF_NAME, bbox_inches='tight')
    os.system('start %s' % SAVE_PDF_NAME)

def redcue_data(timelines):
    '''
        process timelines to output data that is within certain time span when
        the mid node transmits
    '''
    timespan = (FRAME_DURATION + 150) * 2
    mid_idx = IDX_TO_DEVICE_NAME.index('mid')
    valid_interval = interval()
    for inter in timelines[mid_idx]:
        valid_interval |= interval([inter[0] - timespan, inter[1] + timespan])
    #at this point we get the valid_intervals, next is to filter the input data
    ret_timelines = [[], [], []]
    for idx in range(len(timelines)):
        for inter in timelines[idx]:
            if interval([inter[0], inter[1]]) in valid_interval:
                ret_timelines[idx].append(inter)
    return ret_timelines

def main():
    timelines = parse_data('data.txt')
    timelines = redcue_data(timelines)
    draw(timelines)

if __name__ == '__main__':
    main()
