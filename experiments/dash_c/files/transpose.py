#!/usr/bin/env python3

# This script transposes CSV files to the correct format for use with PGFPlots.


import sys, csv


def column(matrix, i):
    return [row[i] for row in matrix]


def str2int(value):
    try:
        return int(value)
    except:
        return value


def max_len(lst):
    result = 0
    for item in lst:
        if result < len(item):
            result = len(item)

    return result


def cut(matrix, header_col, data_col):
    headers = sorted(set(column(matrix, header_col)), key=str2int)
    result = [[header] for header in headers]
    for row in matrix:
        idx = headers.index(row[header_col])
        result[idx].append(row[data_col])

    return result


def transpose(matrix):
    n = max_len(matrix)
    result = [[] for i in range(n)]
    for i in range(len(matrix)):
        for j in range(n):
            try:
                result[j].append(matrix[i][j])
            except:
                result[j].append(None)
    
    return result


def dump(matrix):
    result = ''
    for i, row in enumerate(matrix):
        if i: result += '\n'
        for j, item in enumerate(row):
            if j: result += ','
            if item:
                result += item
    
    return(result)


def main():
    if len(sys.argv) == 2:
        header_col = 0
        data_col   = -1
        filename   = sys.argv[1]
    elif len(sys.argv) == 3:
        header_col = int(sys.argv[1])
        data_col   = -1
        filename   = sys.argv[2]
    elif len(sys.argv) == 4:
        header_col = int(sys.argv[1])
        data_col   = int(sys.argv[2])
        filename   = int(sys.argv[3])
    else:
        print('Usage: ' + sys.argv[0] + ' [HEADER COLUMN] [DATA COLUMN] FILE')
        exit(1)

    with open(filename) as input_file:
        matrix = list(csv.reader(input_file))
        matrix = matrix[1:]

    result = transpose(cut(matrix, header_col, data_col))
    print(dump(result))


if __name__ == '__main__':
    main()
