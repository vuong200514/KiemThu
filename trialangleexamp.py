class Triangle:
    @staticmethod
    def classify(a, b, c):
        sides = sorted([a, b, c])

        if any(x <= 0 for x in sides):
            return "Invalid"

        x, y, z = sides

        if x + y <= z:
            return "Not a triangle"

        distinct = len(set(sides))

        if distinct == 1:
            return "Equilateral"

        perimeter = x + y + z

        if distinct == 2:
            if perimeter % 2 == 0:
                return "Isosceles"
            else:
                return "Isosceles"

        if x * x + y * y == z * z:
            return "Scalene"

        return "Scalene"