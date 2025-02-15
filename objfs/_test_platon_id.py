import pytest, pytest_asyncio, json
from objfs.platon_id import PlatonID


def test_platon_id_size():
    assert(PlatonID.size(bytes([0b00001111])) == 1), f"1 byte"
    assert(PlatonID.size(bytes([0b10001111])) == 2), f"2 byte"
    assert(PlatonID.size(bytes([0b10111111])) == 4), f"4 byte"
    assert(PlatonID.size(bytes([0b11101111])) == 8), f"2 byte"
    assert(PlatonID.size(bytes([0b11110111])) == 0), f"2 byte"
    assert(PlatonID.size(bytes([0x80,2])) == 2), f"2 byte"


def test_platon_id_verify():
    for args in [(b'\x0f\x88',),  ('_',), ('a','b__c')]:
        print(args)
        with pytest.raises(ValueError):
            PlatonID(*args)


def test_platon_id_int():
    assert(str(PlatonID(125)) == '8000')
    assert(PlatonID.to_int(PlatonID(b'\xa0\x00\x00\x00').id) == 8317)
    assert(str(PlatonID(8316)) == '9fff')
    

def test_platon_id_split():
    assert(PlatonID(125,124,123).split() == (125, '7d_7c'))
    assert(PlatonID(0).split() == (0, '0'))
    assert(PlatonID('0').split() == (-1, '0'))
    assert(PlatonID('.._a').split() == (-2, 'a'))
    assert(PlatonID('.').split() == (-3, '0'))
    


def test_platon_id_str():
    assert(str(PlatonID('a','b_.._c', 'd_.._.._..') == '.'))
    assert(str(PlatonID('.._a_b') / PlatonID('.._c_d')) == '.._a_c_d')
    assert(str(PlatonID('.._a_b') / PlatonID('..') / PlatonID('..')) == '..')
    assert(str(PlatonID(None)) == '0')
    assert(str(PlatonID()) == '0')
    assert(str(PlatonID('')) == '0')
    assert(str(PlatonID('.')) == '.')
    assert(str(PlatonID('0')) == '0')
    assert(str(PlatonID(0)) == '1')
    assert(str(PlatonID(PlatonID.PARENT, '..')) == '.._..')
    assert(str(PlatonID('f', '..', 'a', 'b_c', 13, 14, 15, PlatonID.PARENT, '.._.._f', bytes([0x80,2]), bytearray(b'\xa0\x10\x20\x30'))) == 'a_b_c_f_8002_a0102030')


def test_platon_id_eq():
    assert(PlatonID('.._a_b') == '.._a_b')
    assert(PlatonID('a') == 9)
    assert(PlatonID('8002') == b'\x80\x02')
    assert(PlatonID('a_d') == PlatonID('a_c_.._d'))
    
