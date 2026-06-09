"""
AQL 判定引擎 - ISO 2859-1 / GB/T 2828.1 正常检验一次抽样方案
纯业务逻辑，无 UI 依赖
"""

# ============================================================
# 全局常量
# ============================================================

INSPECTION_LEVELS = ['S-1', 'S-2', 'S-3', 'S-4', 'I', 'II', 'III']

AQL_VALUES = [
    0.010, 0.015, 0.025, 0.040, 0.065,
    0.10, 0.15, 0.25, 0.40, 0.65,
    1.0, 1.5, 2.5, 4.0, 6.5,
    10, 15, 25, 40, 65,
    100, 150, 250, 400, 650, 1000
]

AQL_DISPLAY = [f"{v:g}" for v in AQL_VALUES]
AQL_DISPLAY_MAP = {f"{v:g}": v for v in AQL_VALUES}

DEFECT_CATEGORIES = ['致命缺陷', '严重缺陷', '次要缺陷']
DEFECT_KEYS = ['critical', 'major', 'minor']

# ============================================================
# ISO 2859-1 表1: 样本量字码表
# ============================================================

LOT_SIZE_RANGES = [
    (2, 8), (9, 15), (16, 25), (26, 50), (51, 90),
    (91, 150), (151, 280), (281, 500), (501, 1200),
    (1201, 3200), (3201, 10000), (10001, 35000),
    (35001, 150000), (150001, 500000), (500001, float('inf')),
]

CODE_LETTER_TABLE = {
    'S-1': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C', 'D', 'D', 'D'],
    'S-2': ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C', 'D', 'D', 'D', 'E', 'E', 'E'],
    'S-3': ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'E', 'E', 'F', 'F', 'G', 'G', 'H'],
    'S-4': ['A', 'A', 'B', 'C', 'C', 'D', 'E', 'E', 'F', 'G', 'G', 'H', 'J', 'J', 'K'],
    'I':   ['A', 'A', 'B', 'C', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N'],
    'II':  ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q'],
    'III': ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R'],
}

CODE_SAMPLE_SIZES = {
    'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20, 'G': 32,
    'H': 50, 'J': 80, 'K': 125, 'L': 200, 'M': 315,
    'N': 500, 'P': 800, 'Q': 1250, 'R': 2000
}

CODE_LETTERS_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R']

# ============================================================
# ISO 2859-1 表2-A: 正常检验一次抽样方案
# ============================================================

def _build_sampling_plan_raw():
    return {
        'A': {'n': 2, 'data': [None]*26},
        'B': {'n': 3, 'data': [None]*26},
        'C': {'n': 5, 'data': [None]*15 + [(0,1),(0,1),(0,1)] + [None]*8},
        'D': {'n': 8, 'data': [None]*13 + [(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(3,4),(4,5),(5,6),(6,7),(7,8)]},
        'E': {'n': 13, 'data': [None]*11 + [(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10)]},
        'F': {'n': 20, 'data': [None]*9 + [(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(4,5),(5,6),(6,7),(7,8),(8,9),(10,11),(11,12),(12,13)]},
        'G': {'n': 32, 'data': [None]*7 + [(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(5,6),(6,7),(7,8),(8,9),(10,11),(11,12),(12,13),(14,15),(15,16)]},
        'H': {'n': 50, 'data': [None]*6 + [(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,11),(11,12),(14,15),(16,17),(18,19),(20,21)]},
        'J': {'n': 80, 'data': [None]*5 + [(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(10,11),(11,12),(12,13),(14,15),(16,17),(18,19),(21,22),(23,24)]},
        'K': {'n': 125, 'data': [None]*5 + [(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(10,11),(11,12),(12,13),(14,15),(16,17),(18,19),(21,22),(23,24),(26,27)]},
        'L': {'n': 200, 'data': [None]*4 + [(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(9,10),(10,11),(12,13),(14,15),(16,17),(18,19),(21,22),(23,24),(26,27),(28,29)]},
        'M': {'n': 315, 'data': [None]*3 + [(0,1),(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(9,10),(10,11),(12,13),(14,15),(16,17),(18,19),(21,22),(23,24),(26,27),(28,29)]},
        'N': {'n': 500, 'data': [None]*2 + [(0,1),(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(10,11),(11,12),(13,14),(15,16),(17,18),(19,20),(21,22),(23,24),(26,27),(28,29)]},
        'P': {'n': 800, 'data': [None] + [(0,1),(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(10,11),(12,13),(13,14),(15,16),(17,18),(19,20),(21,22),(23,24),(26,27),(28,29),(31,32)]},
        'Q': {'n': 1250, 'data': [(0,1),(0,1),(0,1),(0,1),(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(10,11),(11,12),(14,15),(16,17),(18,19),(21,22),(23,24),(26,27),(28,29),(31,32)]},
        'R': {'n': 2000, 'data': [(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(10,11),(11,12),(14,15),(16,17),(18,19),(21,22),(23,24),(26,27),(28,29),(31,32),(34,35),(38,39),(42,43),(46,47),(50,51)]},
    }

SAMPLING_PLAN_RAW = _build_sampling_plan_raw()


# ============================================================
# AQL 查找引擎
# ============================================================

class AQLEngine:
    """ISO 2859-1 标准查找与判定引擎"""

    def __init__(self):
        self._plan_cache = {}

    def get_code_letter(self, lot_size, inspection_level):
        """根据批量和检验水平返回样本量字码"""
        if lot_size < 2:
            return None
        for i, (lo, hi) in enumerate(LOT_SIZE_RANGES):
            if lot_size <= hi:
                return CODE_LETTER_TABLE[inspection_level][i]
        return None

    def get_code_letter_by_sample_size(self, actual_n):
        """根据实际抽样数向下靠档查找对应字码"""
        sorted_codes = sorted(CODE_SAMPLE_SIZES.items(), key=lambda x: x[1])
        code = 'A'
        for cl, n in sorted_codes:
            if n <= actual_n:
                code = cl
            else:
                break
        return code

    def get_aql_index(self, aql_value):
        """返回 AQL 值在标准列表中的索引"""
        try:
            return AQL_VALUES.index(aql_value)
        except ValueError:
            closest = min(AQL_VALUES, key=lambda x: abs(x - aql_value))
            return AQL_VALUES.index(closest)

    def get_sampling_plan(self, code_letter, aql_value):
        """根据字码和 AQL 返回 (sample_size, Ac, Re)"""
        if code_letter not in CODE_LETTERS_ORDER:
            return None

        aql_idx = self.get_aql_index(aql_value)
        cache_key = (code_letter, aql_idx)

        if cache_key in self._plan_cache:
            return self._plan_cache[cache_key]

        start_idx = CODE_LETTERS_ORDER.index(code_letter)
        for i in range(start_idx, len(CODE_LETTERS_ORDER)):
            cl = CODE_LETTERS_ORDER[i]
            plan = SAMPLING_PLAN_RAW.get(cl)
            if not plan:
                continue
            data = plan['data']
            if aql_idx < len(data) and data[aql_idx] is not None:
                ac, re = data[aql_idx]
                result = (plan['n'], ac, re)
                self._plan_cache[cache_key] = result
                return result

        last_cl = CODE_LETTERS_ORDER[-1]
        last_plan = SAMPLING_PLAN_RAW[last_cl]
        if aql_idx < len(last_plan['data']) and last_plan['data'][aql_idx] is not None:
            ac, re = last_plan['data'][aql_idx]
            result = (last_plan['n'], ac, re)
        else:
            result = (last_plan['n'], 0, 1)

        self._plan_cache[cache_key] = result
        return result

    def judge_category(self, defect_count, ac, re):
        """判定单个缺陷类别"""
        if defect_count <= ac:
            return 'accept', f"{defect_count} ≤ {ac} → 接收"
        else:
            return 'reject', f"{defect_count} ≥ {re} → 拒收"

    def judge_overall(self, results):
        """综合判定：任一类拒收则整批拒收"""
        for r in results:
            if r['verdict'] == 'reject':
                return 'reject'
        return 'accept'
