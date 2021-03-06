#!/usr/bin/python
#this script can be executed on windows
import os, sys, re, math, platform
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import FormatStrFormatter

FRAME_DURATION = 920    #728us(data) + 192us(preamble)
                        #for 1000 bytes packet at 11Mbps
GPIO_TO_DEVICE_DICT = {
    '27': 0,    #left node
    '17': 1,    #mid node
    '22': 2,    #right node
    '18': 3,    #unlocking signal
}

IDX_TO_DEVICE_NAME = ['left', 'mid', 'right', 'unlocking']
IDX_TO_COLOR = ['r', 'g', 'b', 'black']
IDX_TO_Y_AXIS = [1, 3, 5, 0]

SAVE_PDF_NAME = 'TX_timeline.pdf'

def parse_data(filename):
    if not os.path.isfile(filename):
        print('file %s don\'t exist' % filename)
        exit()
    timelines = [[], [], [], []]
    entry_regex = re.compile('^\[.*?\] \[\d+\.\d+\] GPIO: (\d{2}) falling$')
    rest_regex = re.compile('^\[.*?\] (\d+):(\d{2})f$')
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

def draw_ax(ax, timelines, first=True):
    ax.xaxis.grid('on')
    min_x = 999999999999    #get the smallest x axis
    max_x = 0   #get the longest x axis
    for idx in xrange(3):
        name = IDX_TO_DEVICE_NAME[idx]
        color = IDX_TO_COLOR[idx]
        y = IDX_TO_Y_AXIS[idx]
        for interval in timelines[idx]:
            p = patches.Rectangle((interval[0] / 1000.0, y - 1),
                (interval[1] - interval[0]) / 1000.0, 2,
                facecolor=color, linewidth=0)
            ax.add_patch(p)
            min_x = min(min_x, interval[0])
            max_x = max(max_x, interval[1])
    for interval in timelines[3]:
        ax.plot((interval[1] / 1000.0, interval[1] / 1000.0,),
             (0, 6,), 'black', linewidth=2)
    xlim_min, xlim_max = get_x_axis_span(timelines)
    ax.axis([xlim_min, xlim_max, 0, 6])
    x_ticks_tmp = []
    for timeline in timelines:
        for interval in timeline:
            x_ticks_tmp.append(interval[0] / 1000.0)
            x_ticks_tmp.append(interval[1] / 1000.0)
    x_ticks_tmp.sort()
    x_ticks = [x_ticks_tmp[0]]
    for i in xrange(1, len(x_ticks_tmp)):
        if x_ticks_tmp[i] - x_ticks[-1] <= 0.03: #avoid too dense ticks
            x_ticks[-1] = x_ticks_tmp[i]
        else:
            x_ticks.append(x_ticks_tmp[i])
    ax.xaxis.set_ticks(x_ticks)
    x_labels = ['%.3fms' % x for x in x_ticks]
    ax.xaxis.set_ticklabels(x_labels, rotation=70)
    ax.spines['right'].set_visible(False)
    if first:
        ax.yaxis.set_ticks(IDX_TO_Y_AXIS[:-1])
        ax.yaxis.set_ticklabels(IDX_TO_DEVICE_NAME[:-1])
    else:
        ax.spines['left'].set_visible(False)
        ax.yaxis.set_ticks([])
    ax.tick_params(length=0)

def get_x_axis_span(timelines, hspace=0.1):
    min_x = 999999999999
    max_x = 0
    for idx in xrange(len(timelines)):
        if timelines[idx]:
            min_x = min(min_x, timelines[idx][0][0])
            max_x = max(max_x, timelines[idx][-1][1])
    return min_x / 1000.0 - hspace, max_x / 1000.0 + hspace

def draw(list_of_timelines):
    left = 0
    bottom = 0
    top = 0
    right = 0

    fig = plt.figure()
    #get the length of each x-axis
    x_length = []
    total_length = 0.0
    hspace = 0.1
    for timelines in list_of_timelines:
        xlim_min, xlim_max = get_x_axis_span(timelines)
        x_length.append(xlim_max - xlim_min)
        total_length += x_length[-1] + hspace
    #generate ax for each part
    ax = []
    cumulative_length = 0.0
    for width in x_length:
        norm = (1 - left - right) * width / total_length
        x_start = (1 - left - right) * cumulative_length / total_length + left
        ax.append(fig.add_axes([x_start, bottom, norm, 1 - bottom - top]))
        cumulative_length += width + hspace
    #draw each part of the figure
    draw_ax(ax[0], list_of_timelines[0], True)
    for i in xrange(1, len(list_of_timelines)):
        draw_ax(ax[i], list_of_timelines[i], False)
    fig.set_size_inches(total_length * 4, 1)
    fig.savefig(SAVE_PDF_NAME, bbox_inches='tight')
    if platform.system() == 'Windows':
        os.system('start %s' % SAVE_PDF_NAME)

def redcue_data(timelines, intersted='mid'):
    '''
        process timelines to output data that is within certain time span when
        the mid node transmits
        return a list of timelines
    '''
    timespan = (FRAME_DURATION + 150) * 2
    interest_idx = IDX_TO_DEVICE_NAME.index(intersted)
    valid_intval = []
    for intval in timelines[interest_idx]:
        if len(valid_intval) > 0 and \
                valid_intval[-1][1] >= intval[0] - timespan:
            valid_intval[-1] = (valid_intval[-1][0], intval[1] + timespan,)
            continue
        valid_intval.append((intval[0] - timespan, intval[1] + timespan,))
    #at this point we get the valid intervals, next is to filter the input data
    list_of_timelines = []
    node_idxs = [0] * len(timelines)
    for cur_intval in valid_intval:
        tmp_timelines = [[], [], [], []]
        for idx in xrange(len(timelines)):
            for i in xrange(node_idxs[idx], len(timelines[idx])):
                intval = timelines[idx][i]
                overlap = max(min(cur_intval[1], intval[1])
                            - max(cur_intval[0], intval[0]), 0)
                #if TX timespan overlaps at least half with current interval
                if overlap / float(FRAME_DURATION) >= 0.5:
                    tmp_timelines[idx].append(intval)
                if intval[1] > cur_intval[1]:
                    node_idxs[idx] = i
                    break
        list_of_timelines.append(tmp_timelines)
    return list_of_timelines

def main():
    interested = 'mid'
    if len(sys.argv) > 1:
        interested = sys.argv[1]
    timelines = parse_data('data.txt')
    list_of_timelines = redcue_data(timelines, interested)
    draw(list_of_timelines)

if __name__ == '__main__':
    main()
