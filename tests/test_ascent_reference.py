"""Independent exact two-level energy oracle for the ascent-sign convention.

This is a scientific reference check, not a replacement for VASP execution.
"""
import unittest,math
class AscentReference(unittest.TestCase):
 def test_inertial_direction_is_not_an_energy_gradient(self):
  for gap in [-.2,.2]:
   for g in [-3e-4,3e-4]:
    native_A=-math.copysign(3e-5,g)  # momentum can have either sign
    old_target=-native_A;new_target=-math.copysign(abs(native_A),g)
    def energy(target):
     theta=-target*.05
     return gap*math.sin(theta)**2+2*g*math.cos(theta)*math.sin(theta)
    self.assertLess(energy(old_target),0.)
    self.assertGreater(energy(new_target),0.)
if __name__=='__main__':unittest.main()
