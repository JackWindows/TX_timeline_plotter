#!/usr/bin/python

from draw import *

OVERLAP_THRESH = 15 #threshold for determining overlap

def timelines_to_timeline(timelines):
    timeline = []
    for i in xrange(len(timelines)):
        dev_name = IDX_TO_DEVICE_NAME[i]
        for ts in timelines[i]:
            timeline.append((ts, dev_name,))
    timeline.sort()
    return timeline

def print_outcome(timelines, overlap_cnt):
    print "transmitted packet count:"
    for i in xrange(len(timelines)):
        print "%-5s: %4d" % (IDX_TO_DEVICE_NAME[i], len(timelines[i]))
    print "\noverlap count: left %d, right %d, both %d" % \
            (overlap_cnt['left'], overlap_cnt['right'], overlap_cnt['both'])

def main():
    timelines = parse_data('data.txt')
    timeline = timelines_to_timeline(timelines)

    overlap_cnt = {}
    overlap_cnt['left'] = 0
    overlap_cnt['right'] = 0
    overlap_cnt['both'] = 0

    for i in xrange(len(timeline)):
        if timeline[i][1] == 'mid':
            overlap = {}
            overlap['left'] = False
            overlap['right'] = False
            for d in [-2, -1, 1, 2]:
                idx = i + d
                if 0 <= idx < len(timeline) and \
                        abs(timeline[idx][0][1] - timeline[i][0][1]) \
                        <= OVERLAP_THRESH:
                    dev_name = timeline[idx][1]
                    assert(dev_name != 'mid')
                    assert(overlap[dev_name] == False)
                    overlap[dev_name] = True
                    overlap_cnt[dev_name] += 1
                    if overlap['left'] and overlap['right']:
                        overlap_cnt['both'] += 1
    print_outcome(timelines, overlap_cnt)

if __name__ == '__main__':
    main()
