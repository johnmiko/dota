from scipy.interpolate import interp1d


class MultiStep:
    def __init__(self, maps: list, min_in=None, new_min=None, max_in=None, new_max=None, limits_first=False,
                 new_col_name=None):
        self.maps = maps
        self.min = min_in
        self.new_min = new_min
        self.max = max_in
        self.new_max = new_max
        self.limits_first = limits_first
        if new_col_name is None:
            self.new_col_name = 'scaled'
        else:
            self.new_col_name = new_col_name

    def apply(self, df, cols):
        """
        Only works for a single column right now
        :param df:
        :param cols:
        :return:
        """
        if self.new_col_name == 'scaled':
            new_col = f'{cols} {self.new_col_name}'
        else:
            new_col = self.new_col_name
        df[new_col] = df[cols].copy()
        df[new_col] = df[new_col].astype(float)
        if self.limits_first:
            if self.min is not None:
                df.loc[df[new_col] < self.min, new_col] = self.new_min
            if self.max is not None:
                df.loc[df[new_col] > self.max, new_col] = self.new_max
            for map in self.maps:
                df = map.apply(df, new_col)
        else:
            for map in self.maps:
                df = map.apply(df, new_col)
            if self.min is not None:
                df.loc[df[new_col] < self.min, new_col] = self.new_min
            if self.max is not None:
                df.loc[df[new_col] > self.max, new_col] = self.new_max
        return df


class Map:
    def __init__(self, l, h, nl=0, nh=1):
        # Improvement: default low = column name min, default high = column max
        # default scaling from 0-1
        self.l = l
        self.h = h
        self.nl = nl
        self.nh = nh

    def apply(self, df, cols):
        # df[cols] = df[cols].copy()
        m = interp1d([self.l, self.h], [self.nl, self.nh])
        rows = (df[cols] >= self.l) & (df[cols] <= self.h)
        df.loc[rows, cols] = m(df.loc[rows, cols])
        return df


class LinearMap:
    class Range:
        def __init__(self, l, h, nl, nh):
            self.l = l
            self.h = h
            self.nl = nl
            self.nh = nh

    @staticmethod
    def apply(df, col, new_col, ranges):
        # def apply(df, col, new_col, l, h, nl=0, nh=1):
        for range in ranges:
            m = interp1d([range.l, range.h], [range.nl, range.nh])
            rows = (df[col] >= range.l) & (df[col] <= range.h)
            df.loc[rows, new_col] = m(df.loc[rows, col])
        return df


def linear_map(df, col, new_col, l, h, nl=0, nh=1):
    """
    :param df:
    :param col:
    :param new_col:
    :param l:Low
    :param h: High
    :param nl: New Low
    :param nh: New High
    :return:
    """
    m = interp1d([l, h], [nl, nh])
    rows = (df[col] >= l) & (df[col] <= h)
    df.loc[rows, new_col] = m(df.loc[rows, col])
    return df