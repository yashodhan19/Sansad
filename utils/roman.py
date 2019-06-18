# Module to convert roman numerals

roman_numerals = [('M', 1000), ('CM', 900), ('D', 500), ('CD', 400),
                  ('C', 100), ('XC', 90), ('L', 50), ('XL', 40), ('X', 10),
                  ('IX', 9), ('V', 5), ('IV', 4), ('I', 1)]


def from_roman(roman_numeral):
    """
    :param roman_numeral: string - Roman Number
    :return: int
    """

    ix = 0
    iy = 0
    result = 0
    while ix < len(roman_numeral):
        while iy < len(roman_numerals) and not roman_numeral.startswith(
                roman_numerals[iy][0], ix):
            iy += 1
        if iy < len(roman_numerals):
            result += roman_numerals[iy][1]
            ix += len(roman_numerals[iy][0])
        else:
            raise ValueError('Invalid Roman numeral')
    return result
