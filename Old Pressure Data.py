 def getPressure(self):
        if debugMode == False:
            return round(_map(self.pressure.raw_to_v(self.pressure.read()), 0.5, 4.5, 0, 30) * 6.89476 + 101.325 - 12, 2)
        else:
            return round(uniform(100.000, 130.000), 2)