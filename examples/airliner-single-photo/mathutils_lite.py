try:
    from mathutils import Vector
except ImportError:
    import numpy as _np
    class Vector:
        def __init__(self, v): self.v = _np.array(v, float)
        def __add__(self, o): return Vector(self.v + (o.v if isinstance(o, Vector) else _np.array(o)))
        def __mul__(self, k): return Vector(self.v * k)
        __rmul__ = __mul__
        def __iter__(self): return iter(self.v)
        def __getitem__(self, i): return self.v[i]
        def __len__(self): return 3
