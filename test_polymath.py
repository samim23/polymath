import numpy as np
from polymath import root_mean_square

def yahya_test():
    assert 7 == round(root_mean_square([9,7,5]))
