# ビルド
# python setup.py build_ext --inplace

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import numpy as np

# from Cython.Compiler.Options import get_directive_defaults
# directive_defaults = get_directive_defaults()
# directive_defaults['linetrace'] = True
# directive_defaults['binding'] = True

setup(
    cmdclass = {'build_ext': build_ext},
    # ext_modules = [Extension("time_taking_calc", ["time_taking_calc.pyx"], define_macros=[('CYTHON_TRACE', '1')],)],
    ext_modules = [Extension("time_taking_calc", ["time_taking_calc.pyx"])],
    include_dirs=[np.get_include()] # gcc (C言語のコンパイラ) に numpy にまつわるヘッダファイルの所在を教えてあげなければいけない
)


