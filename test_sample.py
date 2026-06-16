import unittest 
import sample 



# Tóm tắt: Không có docstring cho TestArithmeticFunctions
class TestArithmeticFunctions (unittest .TestCase ):





# Tóm tắt: Không có docstring cho test_sum_positive_integers
    def test_sum_positive_integers (self ):
        self .assertEqual (sample .sum (1 ,2 ),3 )
        self .assertEqual (sample .sum (100 ,200 ),300 )



# Tóm tắt: Không có docstring cho test_sum_negative_integers
    def test_sum_negative_integers (self ):
        self .assertEqual (sample .sum (-1 ,-2 ),-3 )
        self .assertEqual (sample .sum (-10 ,-5 ),-15 )



# Tóm tắt: Không có docstring cho test_sum_mixed_integers
    def test_sum_mixed_integers (self ):
        self .assertEqual (sample .sum (5 ,-3 ),2 )
        self .assertEqual (sample .sum (-7 ,2 ),-5 )
        self .assertEqual (sample .sum (10 ,-10 ),0 )



# Tóm tắt: Không có docstring cho test_sum_with_zero
    def test_sum_with_zero (self ):
        self .assertEqual (sample .sum (0 ,5 ),5 )
        self .assertEqual (sample .sum (5 ,0 ),5 )
        self .assertEqual (sample .sum (0 ,-5 ),-5 )
        self .assertEqual (sample .sum (-5 ,0 ),-5 )
        self .assertEqual (sample .sum (0 ,0 ),0 )



# Tóm tắt: Không có docstring cho test_sum_float_numbers
    def test_sum_float_numbers (self ):
        self .assertAlmostEqual (sample .sum (1.5 ,2.5 ),4.0 )
        self .assertAlmostEqual (sample .sum (-1.0 ,0.5 ),-0.5 )
        self .assertAlmostEqual (sample .sum (0.1 ,0.2 ),0.3 )



# Tóm tắt: Không có docstring cho test_sum_large_numbers
    def test_sum_large_numbers (self ):
        self .assertEqual (sample .sum (10 **9 ,10 **9 ),2 *10 **9 )
        self .assertEqual (sample .sum (999999999 ,1 ),1000000000 )





# Tóm tắt: Không có docstring cho test_multiply_positive_integers
    def test_multiply_positive_integers (self ):
        self .assertEqual (sample .multiply (2 ,3 ),6 )
        self .assertEqual (sample .multiply (10 ,5 ),50 )



# Tóm tắt: Không có docstring cho test_multiply_negative_integers
    def test_multiply_negative_integers (self ):
        self .assertEqual (sample .multiply (-2 ,-3 ),6 )
        self .assertEqual (sample .multiply (-10 ,-5 ),50 )



# Tóm tắt: Không có docstring cho test_multiply_mixed_integers
    def test_multiply_mixed_integers (self ):
        self .assertEqual (sample .multiply (5 ,-3 ),-15 )
        self .assertEqual (sample .multiply (-7 ,2 ),-14 )



# Tóm tắt: Không có docstring cho test_multiply_with_zero
    def test_multiply_with_zero (self ):
        self .assertEqual (sample .multiply (0 ,5 ),0 )
        self .assertEqual (sample .multiply (5 ,0 ),0 )
        self .assertEqual (sample .multiply (0 ,0 ),0 )



# Tóm tắt: Không có docstring cho test_multiply_with_one
    def test_multiply_with_one (self ):
        self .assertEqual (sample .multiply (5 ,1 ),5 )
        self .assertEqual (sample .multiply (1 ,10 ),10 )
        self .assertEqual (sample .multiply (-5 ,1 ),-5 )



# Tóm tắt: Không có docstring cho test_multiply_float_numbers
    def test_multiply_float_numbers (self ):
        self .assertAlmostEqual (sample .multiply (1.5 ,2.0 ),3.0 )
        self .assertAlmostEqual (sample .multiply (-2.5 ,0.5 ),-1.25 )
        self .assertAlmostEqual (sample .multiply (0.1 ,0.2 ),0.02 )



# Tóm tắt: Không có docstring cho test_multiply_large_numbers
    def test_multiply_large_numbers (self ):
        self .assertEqual (sample .multiply (10 **3 ,10 **3 ),10 **6 )
        self .assertEqual (sample .multiply (10 **5 ,2 ),200000 )





# Tóm tắt: Không có docstring cho test_calculator_add_positive_integers
    def test_calculator_add_positive_integers (self ):
        calc =sample .Calculator ()
        self .assertEqual (calc .add (1 ,2 ),3 )



# Tóm tắt: Không có docstring cho test_calculator_add_negative_integers
    def test_calculator_add_negative_integers (self ):
        calc =sample .Calculator ()
        self .assertEqual (calc .add (-1 ,-2 ),-3 )



# Tóm tắt: Không có docstring cho test_calculator_add_with_zero
    def test_calculator_add_with_zero (self ):
        calc =sample .Calculator ()
        self .assertEqual (calc .add (0 ,10 ),10 )
        self .assertEqual (calc .add (0 ,0 ),0 )



# Tóm tắt: Không có docstring cho test_calculator_add_float_numbers
    def test_calculator_add_float_numbers (self ):
        calc =sample .Calculator ()
        self .assertAlmostEqual (calc .add (0.1 ,0.2 ),0.3 )
        self .assertAlmostEqual (calc .add (10.5 ,-5.2 ),5.3 )



# Tóm tắt: Không có docstring cho test_calculator_mul_positive_integers
    def test_calculator_mul_positive_integers (self ):
        calc =sample .Calculator ()
        self .assertEqual (calc .mul (2 ,3 ),6 )



# Tóm tắt: Không có docstring cho test_calculator_mul_negative_integers
    def test_calculator_mul_negative_integers (self ):
        calc =sample .Calculator ()
        self .assertEqual (calc .mul (-2 ,-3 ),6 )



# Tóm tắt: Không có docstring cho test_calculator_mul_with_zero
    def test_calculator_mul_with_zero (self ):
        calc =sample .Calculator ()
        self .assertEqual (calc .mul (0 ,10 ),0 )
        self .assertEqual (calc .mul (0 ,0 ),0 )



# Tóm tắt: Không có docstring cho test_calculator_mul_float_numbers
    def test_calculator_mul_float_numbers (self ):
        calc =sample .Calculator ()
        self .assertAlmostEqual (calc .mul (1.5 ,2.0 ),3.0 )
        self .assertAlmostEqual (calc .mul (0.1 ,0.5 ),0.05 )

if __name__ =='__main__':
    unittest .main ()