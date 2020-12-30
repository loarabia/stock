import argparse
import os

from collections import namedtuple

###############################################################################
# stock.py
#
# Uses a model based on the ShillerPE ratio to determine how much money to
# invest. The result it returns is a multiplier to be used with a dollar amount
# i.e. 1.50 * $1000 => invest $1500.
#
# The model is simple. 
#
# As the ShillerPE goes UP and reaches new highs you keep investing the same 
# amount (the multiplier will always be 1 or very close to it). The fun starts
# when the ShillerPE goes down. The further the ShillerPE drops from a high 
# the higher the multiplier goes *and* the faster it accelerates. 
# 
# The implementation uses a specific slice (hand picked) of a reciprocal
# function that has the desired behavior. It then maps the ShillerPE value into
# this slice of the reciprocal function (as the X value) to get a value and
# then maps that value out to the desired range of multipliers. 
#
# TODO: Write the default shillerPE value to a file and load the default from
#   that same file.
# TODO: Add ability to pass above config file by command line
# TODO: Add ability to discover above config file in subdirs
# TODO: Snarf the ShillerPE Min and Max values directly from the web
# TODO: Put the vast bulk of this documenation into command line docs
# TODO: Account for some noise in the multiplier and clamp it to 1. Perhaps 
#   clamp based on the variability of the ShillerPE over a 3 days period where
#   the ultimate trend was still up.
# TODO: Add command line docs about CAPE
###############################################################################

# multiplicative inverse aka reciprocal
def reciprocal(x):
    return 1/x

# The slice of the reciprocal function will be taken from the domain below. 
# These were hand tuned by looking at the function in a graphing tool.
X1 = .1
X2 = 2

Point = namedtuple('Point', ['x', 'y'])

P1 = Point(x=X1, y=reciprocal(X1))
P2 = Point(x=X2, y=reciprocal(X2))

SHILLER_MAX_FILE = "max.txt"
SHILLER_MIN_FILE = "min.txt"

def read_shiller_val(fname):
    with open(fname, "r", encoding="utf_16") as max_file:
        max_data = max_file.read()
        return float(max_data)

# the minimum value and maximum value of the targeted index over the last ~5 years.
# This is the window we'll map to. There is some research that indicates the business 
# cycle is about 4 years. So 5 seems okay. Also, hand tuned.
#
# This particular index is the Shiller PE 
# http://www.multpl.com/shiller-pe/table
SHILLER_5YR_MAX = read_shiller_val(SHILLER_MAX_FILE) if os.path.exists(SHILLER_MAX_FILE) else 34.03
SHILLER_5YR_MIN = read_shiller_val(SHILLER_MIN_FILE) if os.path.exists(SHILLER_MIN_FILE) else 21.90

# Min and Max allowed values of the returned multiplier.
MULT_MIN = 1
MULT_MAX = 10

# Unused but left to help understand the interpolate function that follows
def interpolate_x(x, p1, p2):
    return interpolate(x, p1.x, p2.x, p1.y, p2.y)

# Unused but left to help understand the interpolate function that follows
def interpolate_y(y, p1, p2):
    return interpolate(y, p1.y, p2.y, p1.x, p2.x)

# general linear interpolation
# given a known value (un) between two known points (u1, v1) and (u2,v2) return the unknown vn value
def interpolate(un, u1, u2, v1, v2):
    return v1 + (un-u1) * ((v2-v1)/(u2-u1))

def clamp(value, minval, maxval):
    return minval if value < minval else maxval if value > maxval else value

# map the shiller index onto the slice of the reciprocal function
def interpolateIndex(shiller_index_value):
    return interpolate(shiller_index_value, SHILLER_5YR_MIN, SHILLER_5YR_MAX, P1.x, P2.x)

def main():
    parser = argparse.ArgumentParser(description="Print a multiplier telling you how much money to spend on buying stock")
    parser.add_argument('--shiller-pe', '--cape', '-c', type=float, default=27.77, dest='cape')
    
    args = parser.parse_args()

    current_shiller_value = args.cape

    # The easiest way to think of what is going on. You have a math function, the reciprocal 1/x. It maps
    # scalar (unit-less) x values into scalar y values.
    #
    # We're going to map two different data sets onto those axes.
    # X axis: The shiller PE data will be mapped onto the X values between P1.X and P2.X.
    # Y axis: The multiplier data will be mapped on the Y values.
    #
    # This mapping happens in two steps.
    #
    # First, map the ShillerPE values into reciprocal's domain.
    vy = reciprocal(clamp(interpolateIndex(current_shiller_value), P1.x, P2.x))

    # Second, map the output reciprocal's value onto the multiplier values 
    #
    # Note: 10 and 1 seem to be backwards but you're doing a reciprocal function
    # p1 = (10, P1.y)
    # p2 = (1,  P2.y)
    # pn = (??, vy) 
    # As the function drops you wanted bigger X values.
    # As the function increases, you wanted smaller X values.
    final = interpolate(vy, P1.y, P2.y, MULT_MAX, MULT_MIN)

    print(final)

main()