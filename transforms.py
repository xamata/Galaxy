# we will be working in 2d but finish product will be in transfromed, so this function will easily
# convert from 2D to transform_perspective
def transform(self, x, y):
    # can go easily from transform_2D to transform_perspective
    # return self.transform_2D(x, y)
    return self.transform_perspective(x, y)

    # shows the game in a 2D perspective


def transform_2D(self, x, y):
    # always return int coordinates bc float causing shakiness
    return int(x), int(y)


# shows the game in a transformed perspective
def transform_perspective(self, x, y):
    lin_y = y * self.perspective_point_y / self.height
    if lin_y > self.perspective_point_y:
        lin_y = self.perspective_point_y

    diff_x = x - self.perspective_point_x
    diff_y = self.perspective_point_y - lin_y

    # ATTRACTION - gradually shorten the distance between each horizontal line
    # creating a more realistic perspective
    factor_y = diff_y / self.perspective_point_y
    # squaring factor_y gives the position of the horizontal line a smaller coordinate, making the
    # distance between each horizontal gradually smaller
    factor_y = pow(factor_y, 2)  # factor_y * factor_y

    tr_x = self.perspective_point_x + diff_x * factor_y
    tr_y = self.perspective_point_y - factor_y * self.perspective_point_y

    # always return int coordinates bc float causes shakiness
    return int(tr_x), int(tr_y)
