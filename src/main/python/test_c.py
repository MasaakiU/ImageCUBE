

import re



s = "20180812_HeLa_quartz_d31PA_1_CRR_NR100x155y83_minus_x161y45_3300-3800.spc"



m = re.match(".*_(d[0-9]+[A-Za-z]+)_.*", s)
print(m.group(1))




