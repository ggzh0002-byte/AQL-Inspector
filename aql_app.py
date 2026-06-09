#!/usr/bin/env python3
"""
AQL判定工具
ISO 2859-1 / GB/T 2828.1 正常检验一次抽样方案
Windows 桌面应用程序
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import os
import sys
import threading
from datetime import datetime

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# ============================================================
# 全局常量
# ============================================================

APP_NAME = "AQL判定工具"
APP_VERSION = "1.0.0"

# 检验水平选项
INSPECTION_LEVELS = ['S-1', 'S-2', 'S-3', 'S-4', 'I', 'II', 'III']
DEFAULT_INSPECTION_LEVEL = 'II'

# AQL 值全系列 (ISO 2859-1)
AQL_VALUES = [
    0.010, 0.015, 0.025, 0.040, 0.065,
    0.10, 0.15, 0.25, 0.40, 0.65,
    1.0, 1.5, 2.5, 4.0, 6.5,
    10, 15, 25, 40, 65,
    100, 150, 250, 400, 650, 1000
]

# 用于下拉菜单的 AQL 显示字符串
AQL_DISPLAY = [f"{v:g}" for v in AQL_VALUES]
AQL_DISPLAY_MAP = {f"{v:g}": v for v in AQL_VALUES}

# 默认 AQL 值
DEFAULT_CRITICAL_AQL = 0.010
DEFAULT_MAJOR_AQL = 1.0
DEFAULT_MINOR_AQL = 2.5

# 缺陷类别
DEFECT_CATEGORIES = ['致命缺陷', '严重缺陷', '次要缺陷']
DEFECT_KEYS = ['critical', 'major', 'minor']

# ============================================================
# ISO 2859-1 表1: 样本量字码表
# ============================================================

LOT_SIZE_RANGES = [
    (2, 8),
    (9, 15),
    (16, 25),
    (26, 50),
    (51, 90),
    (91, 150),
    (151, 280),
    (281, 500),
    (501, 1200),
    (1201, 3200),
    (3201, 10000),
    (10001, 35000),
    (35001, 150000),
    (150001, 500000),
    (500001, float('inf')),
]

# 每个检验水平下，各批量范围对应的样本量字码
CODE_LETTER_TABLE = {
    'S-1': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C', 'D', 'D', 'D'],
    'S-2': ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C', 'D', 'D', 'D', 'E', 'E', 'E'],
    'S-3': ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'E', 'E', 'F', 'F', 'G', 'G', 'H'],
    'S-4': ['A', 'A', 'B', 'C', 'C', 'D', 'E', 'E', 'F', 'G', 'G', 'H', 'J', 'J', 'K'],
    'I':   ['A', 'A', 'B', 'C', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N'],
    'II':  ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q'],
    'III': ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R'],
}

# 每个字码的默认样本量
CODE_SAMPLE_SIZES = {
    'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20, 'G': 32,
    'H': 50, 'J': 80, 'K': 125, 'L': 200, 'M': 315,
    'N': 500, 'P': 800, 'Q': 1250, 'R': 2000
}

# 字码顺序（用于箭头查找）
CODE_LETTERS_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R']

# ============================================================
# ISO 2859-1 表2-A: 正常检验一次抽样方案
# 每个字码对应26个AQL列的 Ac/Re 值
# None = ↓ (向下箭头，使用下一个字码的方案)
# (Ac, Re) = 接收数和拒收数
# ============================================================

def _build_sampling_plan_raw():
    """构建原始抽样方案表"""
    return {
        'A': {'n': 2, 'data': [
            None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None
        ]},
        'B': {'n': 3, 'data': [
            None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None
        ]},
        'C': {'n': 5, 'data': [
            None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None,
            (0,1), (0,1), (0,1), None, None,
            None, None, None, None, None, None
        ]},
        'D': {'n': 8, 'data': [
            None, None, None, None, None, None, None, None, None, None,
            None, None, None,
            (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3),
            (3,4), (3,4), (4,5), (5,6), (6,7), (7,8)
        ]},
        'E': {'n': 13, 'data': [
            None, None, None, None, None, None, None, None, None, None,
            None,
            (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4), (4,5),
            (4,5), (5,6), (6,7), (7,8), (8,9), (9,10)
        ]},
        'F': {'n': 20, 'data': [
            None, None, None, None, None, None, None, None, None,
            (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (4,5), (5,6), (6,7), (7,8), (8,9), (10,11), (11,12), (12,13)
        ]},
        'G': {'n': 32, 'data': [
            None, None, None, None, None, None, None,
            (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (5,6), (5,6), (6,7), (7,8), (8,9), (10,11), (11,12),
            (12,13), (14,15), (15,16)
        ]},
        'H': {'n': 50, 'data': [
            None, None, None, None, None, None,
            (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (11,12),
            (14,15), (16,17), (18,19), (20,21)
        ]},
        'J': {'n': 80, 'data': [
            None, None, None, None, None,
            (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (5,6), (6,7), (7,8), (8,9), (10,11), (11,12), (12,13),
            (14,15), (16,17), (18,19), (21,22), (23,24)
        ]},
        'K': {'n': 125, 'data': [
            None, None, None, None, None,
            (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4), (4,5),
            (5,6), (6,7), (7,8), (8,9), (10,11), (11,12), (12,13), (14,15),
            (16,17), (18,19), (21,22), (23,24), (26,27)
        ]},
        'L': {'n': 200, 'data': [
            None, None, None, None,
            (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (5,6), (6,7), (7,8), (9,10), (10,11), (12,13), (14,15),
            (16,17), (18,19), (21,22), (23,24), (26,27), (28,29)
        ]},
        'M': {'n': 315, 'data': [
            None, None, None,
            (0,1), (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (5,6), (6,7), (7,8), (9,10), (10,11), (12,13), (14,15),
            (16,17), (18,19), (21,22), (23,24), (26,27), (28,29)
        ]},
        'N': {'n': 500, 'data': [
            None, None,
            (0,1), (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (5,6), (6,7), (7,8), (8,9), (10,11), (11,12), (13,14),
            (15,16), (17,18), (19,20), (21,22), (23,24), (26,27), (28,29)
        ]},
        'P': {'n': 800, 'data': [
            None,
            (0,1), (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (5,6), (6,7), (7,8), (8,9), (10,11), (12,13),
            (13,14), (15,16), (17,18), (19,20), (21,22), (23,24), (26,27),
            (28,29), (31,32)
        ]},
        'Q': {'n': 1250, 'data': [
            (0,1), (0,1), (0,1),
            (0,1), (0,1), (0,1), (1,2), (1,2), (2,3), (2,3), (3,4),
            (4,5), (5,6), (6,7), (7,8), (8,9), (10,11), (11,12), (14,15),
            (16,17), (18,19), (21,22), (23,24), (26,27), (28,29), (31,32)
        ]},
        'R': {'n': 2000, 'data': [
            (0,1), (1,2), (1,2), (2,3), (2,3), (3,4), (4,5), (5,6),
            (6,7), (7,8), (8,9), (10,11), (11,12), (14,15), (16,17),
            (18,19), (21,22), (23,24), (26,27), (28,29), (31,32),
            (34,35), (38,39), (42,43), (46,47), (50,51)
        ]},
    }


SAMPLING_PLAN_RAW = _build_sampling_plan_raw()


# ============================================================
# AQL 查找引擎
# ============================================================

class AQLEngine:
    """ISO 2859-1 标准查找与判定引擎"""

    def __init__(self):
        self._plan_cache = {}  # (code_letter, aql_index) -> (n, Ac, Re)

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
            # 查找最接近的 AQL 值
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

        # 从当前字码开始，向下查找第一个有数值的计划
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

        # 如果到最后一个字码仍无结果，返回最大计划
        last_cl = CODE_LETTERS_ORDER[-1]
        last_plan = SAMPLING_PLAN_RAW[last_cl]
        if aql_idx < len(last_plan['data']) and last_plan['data'][aql_idx] is not None:
            ac, re = last_plan['data'][aql_idx]
            result = (last_plan['n'], ac, re)
        else:
            # 使用最大样本量，Ac=0, Re=1
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


# ============================================================
# 深色工业风主题配置
# ============================================================

class DarkTheme:
    """深色工业风主题色彩"""

    BG_ROOT = '#1a1a2e'
    BG_FRAME = '#20243a'
    BG_LABELFRAME = '#20243a'
    BG_ENTRY = '#2d3148'
    BG_BUTTON = '#3a3f5c'
    BG_BUTTON_ACTIVE = '#4a5080'
    BG_TREEVIEW = '#20243a'
    BG_TREEVIEW_SEL = '#3a3f5c'

    FG = '#e0e0e0'
    FG_HEADER = '#ffffff'
    FG_DIM = '#888888'

    GREEN = '#4cdf80'
    GREEN_BG = '#1a3a2a'
    RED = '#ff5566'
    RED_BG = '#3a1a1a'
    YELLOW = '#ffb84d'
    YELLOW_BG = '#3a3010'
    BLUE = '#5b9eff'
    ORANGE = '#ff8c42'

    FONT_DEFAULT = ('Microsoft YaHei UI', 10)
    FONT_SMALL = ('Microsoft YaHei UI', 9)
    FONT_HEADING = ('Microsoft YaHei UI', 12, 'bold')
    FONT_TITLE = ('Microsoft YaHei UI', 16, 'bold')
    FONT_RESULT = ('Microsoft YaHei UI', 24, 'bold')
    FONT_BIG = ('Microsoft YaHei UI', 14, 'bold')
    FONT_MONO = ('Consolas', 11)


def apply_dark_theme(root):
    """应用深色工业风主题"""
    style = ttk.Style(root)
    style.theme_use('clam')

    # 全局配置
    root.configure(bg=DarkTheme.BG_ROOT)

    # 通用样式
    style.configure('.',
                    background=DarkTheme.BG_ROOT,
                    foreground=DarkTheme.FG,
                    fieldbackground=DarkTheme.BG_ENTRY,
                    borderwidth=1,
                    font=DarkTheme.FONT_DEFAULT)

    # Frame
    style.configure('TFrame', background=DarkTheme.BG_ROOT)
    style.configure('Card.TFrame', background=DarkTheme.BG_FRAME)

    # LabelFrame
    style.configure('TLabelframe',
                    background=DarkTheme.BG_ROOT,
                    foreground=DarkTheme.FG_HEADER,
                    bordercolor=DarkTheme.BG_BUTTON)
    style.configure('TLabelframe.Label',
                    background=DarkTheme.BG_ROOT,
                    foreground=DarkTheme.FG_HEADER,
                    font=DarkTheme.FONT_HEADING)

    # Label
    style.configure('TLabel',
                    background=DarkTheme.BG_ROOT,
                    foreground=DarkTheme.FG,
                    font=DarkTheme.FONT_DEFAULT)
    style.configure('Title.TLabel',
                    font=DarkTheme.FONT_TITLE,
                    foreground=DarkTheme.FG_HEADER)
    style.configure('Heading.TLabel',
                    font=DarkTheme.FONT_HEADING,
                    foreground=DarkTheme.FG_HEADER)
    style.configure('Value.TLabel',
                    font=('Microsoft YaHei UI', 12, 'bold'),
                    foreground=DarkTheme.BLUE)
    style.configure('Green.TLabel',
                    font=DarkTheme.FONT_BIG,
                    foreground=DarkTheme.GREEN)
    style.configure('Red.TLabel',
                    font=DarkTheme.FONT_BIG,
                    foreground=DarkTheme.RED)
    style.configure('Result.TLabel',
                    font=DarkTheme.FONT_RESULT,
                    foreground=DarkTheme.GREEN)

    # Entry
    style.configure('TEntry',
                    fieldbackground=DarkTheme.BG_ENTRY,
                    foreground=DarkTheme.FG,
                    insertcolor=DarkTheme.FG)
    style.map('TEntry',
              fieldbackground=[('disabled', DarkTheme.BG_FRAME)],
              foreground=[('disabled', DarkTheme.FG_DIM)])

    # Combobox
    style.configure('TCombobox',
                    fieldbackground=DarkTheme.BG_ENTRY,
                    foreground=DarkTheme.FG,
                    arrowcolor=DarkTheme.FG,
                    background=DarkTheme.BG_ENTRY)
    style.map('TCombobox',
              fieldbackground=[('readonly', DarkTheme.BG_ENTRY)],
              foreground=[('readonly', DarkTheme.FG)],
              selectbackground=[('readonly', DarkTheme.BG_TREEVIEW_SEL)],
              selectforeground=[('readonly', DarkTheme.FG)])

    # 强制 Combobox 下拉列表颜色 (clam theme workaround)
    root.option_add('*TCombobox*Listbox.background', DarkTheme.BG_ENTRY)
    root.option_add('*TCombobox*Listbox.foreground', DarkTheme.FG)
    root.option_add('*TCombobox*Listbox.selectBackground', DarkTheme.BG_TREEVIEW_SEL)
    root.option_add('*TCombobox*Listbox.selectForeground', DarkTheme.FG)
    root.option_add('*TCombobox*Listbox.font', DarkTheme.FONT_DEFAULT)

    # Button
    style.configure('TButton',
                    background=DarkTheme.BG_BUTTON,
                    foreground=DarkTheme.FG,
                    borderwidth=1,
                    focusthickness=2,
                    focuscolor=DarkTheme.BLUE,
                    font=DarkTheme.FONT_DEFAULT)
    style.map('TButton',
              background=[('active', DarkTheme.BG_BUTTON_ACTIVE),
                          ('pressed', DarkTheme.BG_BUTTON_ACTIVE),
                          ('disabled', DarkTheme.BG_FRAME)],
              foreground=[('disabled', DarkTheme.FG_DIM)])

    # 大判定按钮
    style.configure('Judge.TButton',
                    background='#d4380d',
                    foreground='#ffffff',
                    font=('Microsoft YaHei UI', 24, 'bold'),
                    borderwidth=3,
                    bordercolor='#ff4d2e',
                    padding=(20, 8))
    style.map('Judge.TButton',
              background=[('active', '#ff4d2e'),
                          ('pressed', '#d4380d'),
                          ('disabled', '#5a3a30')],
              foreground=[('disabled', '#999999')])

    # 导出按钮
    style.configure('Export.TButton',
                    background=DarkTheme.BG_BUTTON,
                    foreground=DarkTheme.FG,
                    font=DarkTheme.FONT_DEFAULT,
                    padding=(15, 8))

    # Treeview (历史记录)
    style.configure('Treeview',
                    background=DarkTheme.BG_TREEVIEW,
                    foreground=DarkTheme.FG,
                    fieldbackground=DarkTheme.BG_TREEVIEW,
                    bordercolor=DarkTheme.BG_BUTTON,
                    font=DarkTheme.FONT_SMALL,
                    rowheight=26)
    style.configure('Treeview.Heading',
                    background=DarkTheme.BG_FRAME,
                    foreground=DarkTheme.FG_HEADER,
                    font=('Microsoft YaHei UI', 9, 'bold'),
                    relief='flat',
                    borderwidth=1)
    style.map('Treeview',
              background=[('selected', DarkTheme.BG_TREEVIEW_SEL)],
              foreground=[('selected', DarkTheme.FG)])

    # Scrollbar
    style.configure('TScrollbar',
                    background=DarkTheme.BG_FRAME,
                    troughcolor=DarkTheme.BG_ROOT,
                    arrowcolor=DarkTheme.FG,
                    bordercolor=DarkTheme.BG_ROOT)
    style.map('TScrollbar',
              background=[('active', DarkTheme.BG_BUTTON)])

    # Separator
    style.configure('TSeparator', background=DarkTheme.BG_BUTTON)

    return style


# ============================================================
# 历史记录管理
# ============================================================

class HistoryManager:
    """历史记录存储与读取"""

    def __init__(self):
        self.history_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                         'aql_history.json')
        self.records = []
        self.load()

    def load(self):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.records = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.records = []

    def save(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def add_record(self, record):
        self.records.insert(0, record)  # 最新的在前
        self.save()

    def filter(self, date_from=None, date_to=None, result_filter=None):
        filtered = self.records
        if date_from:
            filtered = [r for r in filtered if r['判定时间'][:10] >= date_from]
        if date_to:
            filtered = [r for r in filtered if r['判定时间'][:10] <= date_to]
        if result_filter and result_filter != '全部':
            filtered = [r for r in filtered if r['整批结论'] == result_filter]
        return filtered

    def export_csv(self, filepath, records=None):
        if records is None:
            records = self.records
        if not records:
            return False

        fieldnames = [
            '判定时间', '检验水平', '批量', '实际抽样数',
            '致命缺陷AQL', '致命Ac', '致命Re', '致命缺陷数', '致命判定',
            '严重缺陷AQL', '严重Ac', '严重Re', '严重缺陷数', '严重判定',
            '次要缺陷AQL', '次要Ac', '次要Re', '次要缺陷数', '次要判定',
            '整批结论'
        ]

        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in records:
                    row = {k: r.get(k, '') for k in fieldnames}
                    writer.writerow(row)
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False


# ============================================================
# 可编辑标签组件 (双击修改，回车确认)
# ============================================================

# ============================================================
# 主应用程序
# ============================================================

class AQLApp:
    """AQL判定工具主界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry('1280x900')
        self.root.minsize(1100, 750)

        # 设置窗口图标 (尝试多种方式)
        self._set_app_icon()

        # 应用深色主题
        self.style = apply_dark_theme(self.root)

        # 引擎和历史管理器
        self.engine = AQLEngine()
        self.history = HistoryManager()

        # 判定按钮锁定
        self.judge_locked = False

        # 构建界面
        self._build_ui()

        # 初始计算
        self.root.after(100, self._auto_calculate)

        # 窗口居中
        self._center_window()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_app_icon(self):
        """设置应用图标"""
        try:
            # 尝试使用 ICO 文件
            icon_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f'+{x}+{y}')

    # ----------------------------------------------------------
    # 界面构建
    # ----------------------------------------------------------

    def _build_ui(self):
        """构建完整用户界面"""
        # 主容器
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 标题栏
        self._build_title_bar()

        # 内容区 (左 + 右)
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill='both', expand=True, pady=(5, 0))

        # 左侧面板 (可滚动)
        left_container = ttk.Frame(self.content_frame)
        left_container.pack(side='left', fill='both', expand=True, padx=(0, 5))

        self.left_canvas = tk.Canvas(left_container, bg=DarkTheme.BG_ROOT,
                                     highlightthickness=0, bd=0)
        self.left_scrollbar = ttk.Scrollbar(left_container, orient='vertical',
                                            command=self.left_canvas.yview)
        # 必须用 tk.Frame，ttk.Frame 在 Canvas 内不触发 Configure
        self.left_frame = tk.Frame(self.left_canvas, bg=DarkTheme.BG_ROOT)

        self.left_canvas_window = self.left_canvas.create_window(
            (0, 0), window=self.left_frame, anchor='nw')
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)

        self.left_canvas.pack(side='left', fill='both', expand=True)
        self.left_scrollbar.pack(side='right', fill='y')

        # 绑定滚动区域刷新
        self.left_frame.bind('<Configure>', self._on_left_frame_configure)
        self.left_canvas.bind('<Configure>', self._on_canvas_configure)

        # 鼠标滚轮滚动
        def _on_mousewheel(event):
            self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        self.left_canvas.bind('<Enter>', lambda e: self.left_canvas.bind_all('<MouseWheel>', _on_mousewheel))
        self.left_canvas.bind('<Leave>', lambda e: self.left_canvas.unbind_all('<MouseWheel>'))

        # 右侧面板 (历史记录)
        self.right_frame = ttk.Frame(self.content_frame, width=520)
        self.right_frame.pack(side='right', fill='both', padx=(5, 0))
        self.right_frame.pack_propagate(False)

        # 构建各子面板
        self._build_settings_panel()    # 抽样标准设置
        self._build_standards_panel()   # 标准值显示
        self._build_judgment_panel()    # 批次判定
        self._build_result_panel()      # 判定结果
        self._build_history_panel()     # 历史记录

        # 底部导出按钮
        self._build_bottom_bar()

        # 初始加载历史记录
        self._refresh_history()

    def _on_left_frame_configure(self, event):
        """内部 frame 大小变化时更新滚动区域"""
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        """canvas 宽度变化时同步内部 frame 宽度"""
        self.left_canvas.itemconfig(self.left_canvas_window, width=event.width)

    def _build_title_bar(self):
        """标题栏"""
        title_frame = tk.Frame(self.main_frame, bg=DarkTheme.BG_ROOT)
        title_frame.pack(fill='x')

        tk.Label(
            title_frame,
            text="AQL 判定工具",
            font=DarkTheme.FONT_TITLE,
            bg=DarkTheme.BG_ROOT,
            fg=DarkTheme.FG_HEADER
        ).pack(side='left')

        tk.Label(
            title_frame,
            text=f"ISO 2859-1 / GB/T 2828.1   v{APP_VERSION}",
            font=DarkTheme.FONT_SMALL,
            bg=DarkTheme.BG_ROOT,
            fg=DarkTheme.FG_DIM
        ).pack(side='right')

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=(5, 0))

    def _build_settings_panel(self):
        """抽样标准设置区"""
        panel = ttk.LabelFrame(self.left_frame, text="  抽样标准设置  ", padding=(12, 10))
        panel.pack(fill='x', pady=(0, 8))

        # 第一行: 检验水平 + 批量
        row1 = ttk.Frame(panel)
        row1.pack(fill='x', pady=(0, 6))

        ttk.Label(row1, text="检验水平:", width=10).pack(side='left')
        self.inspection_level_var = tk.StringVar(value=DEFAULT_INSPECTION_LEVEL)
        self.level_combo = ttk.Combobox(
            row1,
            textvariable=self.inspection_level_var,
            values=INSPECTION_LEVELS,
            state='readonly',
            width=8
        )
        self.level_combo.pack(side='left', padx=(0, 20))
        self.level_combo.bind('<<ComboboxSelected>>', lambda e: self._auto_calculate())

        ttk.Label(row1, text="批量:", width=6).pack(side='left')
        self.lot_size_var = tk.StringVar()
        self.lot_size_entry = ttk.Entry(row1, textvariable=self.lot_size_var, width=12)
        self.lot_size_entry.pack(side='left')
        self.lot_size_entry.bind('<KeyRelease>', lambda e: self._auto_calculate())

        # 字码和样本数显示
        self.code_letter_var = tk.StringVar(value='—')
        self.sample_size_var = tk.StringVar(value='—')

        info_frame = ttk.Frame(panel)
        info_frame.pack(fill='x', pady=(0, 6))

        ttk.Label(info_frame, text="样本量字码:", width=10).pack(side='left')
        tk.Label(
            info_frame,
            textvariable=self.code_letter_var,
            font=('Microsoft YaHei UI', 14, 'bold'),
            bg=DarkTheme.BG_FRAME,
            fg=DarkTheme.BLUE,
            width=4,
            anchor='center'
        ).pack(side='left')

        ttk.Label(info_frame, text=" 应抽样本数:", width=11).pack(side='left')
        tk.Label(
            info_frame,
            textvariable=self.sample_size_var,
            font=('Microsoft YaHei UI', 14, 'bold'),
            bg=DarkTheme.BG_FRAME,
            fg=DarkTheme.ORANGE,
            width=6,
            anchor='center'
        ).pack(side='left')

        # AQL 设定行
        aql_frame = ttk.Frame(panel)
        aql_frame.pack(fill='x', pady=(4, 0))

        # 列标题
        ttk.Label(aql_frame, text="", width=10).grid(row=0, column=0)
        ttk.Label(aql_frame, text="缺陷类别", font=DarkTheme.FONT_SMALL).grid(row=0, column=1, padx=(5, 15))
        ttk.Label(aql_frame, text="AQL 值", font=DarkTheme.FONT_SMALL).grid(row=0, column=2, padx=5)

        self.aql_vars = {}
        self.aql_combos = {}
        categories = [
            ('critical', '致命缺陷', DEFAULT_CRITICAL_AQL),
            ('major', '严重缺陷', DEFAULT_MAJOR_AQL),
            ('minor', '次要缺陷', DEFAULT_MINOR_AQL),
        ]

        for i, (key, label, default) in enumerate(categories):
            row = i + 1
            ttk.Label(aql_frame, text="").grid(row=row, column=0)  # spacer
            tk.Label(
                aql_frame, text=label,
                bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG,
                font=DarkTheme.FONT_DEFAULT, width=8, anchor='w'
            ).grid(row=row, column=1, padx=(5, 15), pady=2)

            self.aql_vars[key] = tk.StringVar(value=f"{default:g}")
            self.aql_combos[key] = ttk.Combobox(
                aql_frame,
                textvariable=self.aql_vars[key],
                values=AQL_DISPLAY,
                state='readonly',
                width=8
            )
            self.aql_combos[key].grid(row=row, column=2, padx=5, pady=2)
            self.aql_combos[key].bind('<<ComboboxSelected>>', lambda e: self._auto_calculate())

    def _build_standards_panel(self):
        """标准值自动呈现与手动覆盖区"""
        panel = ttk.LabelFrame(self.left_frame, text="  标准值  ", padding=(12, 10))
        panel.pack(fill='x', pady=(0, 8))

        # 表格标题
        header_frame = tk.Frame(panel, bg=DarkTheme.BG_FRAME)
        header_frame.pack(fill='x', pady=(0, 4))

        headers = [('缺陷类别', 10), ('AQL', 8), ('Ac (接收)', 8), ('Re (拒收)', 8)]
        for text, width in headers:
            tk.Label(
                header_frame, text=text,
                bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG_HEADER,
                font=('Microsoft YaHei UI', 9, 'bold'),
                width=width, anchor='center'
            ).pack(side='left', padx=2)

        ttk.Separator(panel, orient='horizontal').pack(fill='x')

        # 数据行
        self.ac_vars = {}
        self.re_vars = {}
        self.aql_display_labels = {}

        categories = [
            ('critical', '致命缺陷'),
            ('major', '严重缺陷'),
            ('minor', '次要缺陷'),
        ]

        for key, label in categories:
            row_frame = tk.Frame(panel, bg=DarkTheme.BG_FRAME)
            row_frame.pack(fill='x', pady=1)

            tk.Label(
                row_frame, text=label,
                bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG,
                font=DarkTheme.FONT_DEFAULT, width=10, anchor='w'
            ).pack(side='left', padx=2)

            aql_lbl = tk.Label(
                row_frame, text='—',
                bg=DarkTheme.BG_FRAME, fg=DarkTheme.BLUE,
                font=DarkTheme.FONT_MONO, width=8, anchor='center'
            )
            aql_lbl.pack(side='left', padx=2)
            self.aql_display_labels[key] = aql_lbl

            ac_var = tk.StringVar(value='—')
            ac_lbl = tk.Label(
                row_frame, textvariable=ac_var,
                bg=DarkTheme.BG_ENTRY, fg=DarkTheme.FG,
                font=DarkTheme.FONT_DEFAULT, width=6,
                relief='sunken', borderwidth=1, anchor='center'
            )
            ac_lbl.pack(side='left', padx=2)
            self.ac_vars[key] = ac_var

            re_var = tk.StringVar(value='—')
            re_lbl = tk.Label(
                row_frame, textvariable=re_var,
                bg=DarkTheme.BG_ENTRY, fg=DarkTheme.FG,
                font=DarkTheme.FONT_DEFAULT, width=6,
                relief='sunken', borderwidth=1, anchor='center'
            )
            re_lbl.pack(side='left', padx=2)
            self.re_vars[key] = re_var

    def _build_judgment_panel(self):
        """批次判定区"""
        panel = ttk.LabelFrame(self.left_frame, text="  批次判定  ", padding=(12, 10))
        panel.pack(fill='x', pady=(0, 8))

        # 实际抽样数输入（在缺陷数上方）
        actual_frame = tk.Frame(panel, bg=DarkTheme.BG_FRAME)
        actual_frame.pack(fill='x', pady=(0, 6))

        tk.Label(
            actual_frame, text='实际抽样数:',
            bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG,
            font=DarkTheme.FONT_DEFAULT, width=10, anchor='e'
        ).pack(side='left', padx=(5, 8))

        self.actual_sample_var = tk.StringVar(value='')
        self.actual_sample_entry = ttk.Entry(
            actual_frame,
            textvariable=self.actual_sample_var,
            width=10,
            font=DarkTheme.FONT_DEFAULT
        )
        self.actual_sample_entry.pack(side='left')

        tk.Label(
            actual_frame, text='(默认等于应抽数)',
            bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG_DIM,
            font=DarkTheme.FONT_SMALL
        ).pack(side='left', padx=(8, 0))

        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=(4, 6))

        # 缺陷数输入
        input_frame = tk.Frame(panel, bg=DarkTheme.BG_FRAME)
        input_frame.pack(fill='x', pady=(0, 8))

        self.defect_vars = {}
        self.defect_entries = {}

        categories = [
            ('critical', '致命缺陷数:', 0),
            ('major', '严重缺陷数:', 0),
            ('minor', '次要缺陷数:', 0),
        ]

        for i, (key, label, default) in enumerate(categories):
            tk.Label(
                input_frame, text=label,
                bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG,
                font=DarkTheme.FONT_DEFAULT, width=10, anchor='e'
            ).grid(row=i, column=0, padx=(5, 8), pady=3)

            self.defect_vars[key] = tk.StringVar(value='0')
            self.defect_entries[key] = ttk.Entry(
                input_frame,
                textvariable=self.defect_vars[key],
                width=10,
                font=DarkTheme.FONT_DEFAULT
            )
            self.defect_entries[key].grid(row=i, column=1, pady=3)

        # 调整状态提示标签
        self.adjust_status_var = tk.StringVar(value='')
        self.adjust_status_label = tk.Label(
            panel, textvariable=self.adjust_status_var,
            bg=DarkTheme.BG_FRAME, fg=DarkTheme.YELLOW,
            font=DarkTheme.FONT_SMALL, anchor='w'
        )
        self.adjust_status_label.pack(fill='x', pady=(0, 4))

        # 判定按钮
        btn_frame = tk.Frame(panel, bg=DarkTheme.BG_FRAME)
        btn_frame.pack(fill='x', pady=(4, 0))

        self.judge_btn = ttk.Button(
            btn_frame,
            text="  判  定  ",
            style='Judge.TButton',
            command=self._execute_judgment
        )
        self.judge_btn.pack(fill='x', ipady=4)

    def _build_result_panel(self):
        """判定结果显示区"""
        panel = ttk.LabelFrame(self.left_frame, text="  判定结果  ", padding=(12, 10))
        panel.pack(fill='x', pady=(0, 8))

        # 逐项结果
        self.result_labels = {}
        categories = [
            ('critical', '致命缺陷'),
            ('major', '严重缺陷'),
            ('minor', '次要缺陷'),
        ]

        for key, label in categories:
            row = tk.Frame(panel, bg=DarkTheme.BG_FRAME)
            row.pack(fill='x', pady=2)

            tk.Label(
                row, text=f"{label}:",
                bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG,
                font=DarkTheme.FONT_DEFAULT, width=10, anchor='w'
            ).pack(side='left')

            lbl = tk.Label(
                row, text='—',
                bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG_DIM,
                font=DarkTheme.FONT_DEFAULT, anchor='w'
            )
            lbl.pack(side='left', padx=(5, 0))
            self.result_labels[key] = lbl

        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=(6, 6))

        # 整批结论
        self.final_verdict_label = tk.Label(
            panel, text='等待判定',
            bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG_DIM,
            font=('Microsoft YaHei UI', 22, 'bold'),
            anchor='center', pady=10
        )
        self.final_verdict_label.pack(fill='x')

    def _build_history_panel(self):
        """历史记录面板"""
        panel = ttk.LabelFrame(self.right_frame, text="  历史记录  ", padding=(10, 8))
        panel.pack(fill='both', expand=True)

        # 筛选栏
        filter_frame = ttk.Frame(panel)
        filter_frame.pack(fill='x', pady=(0, 6))

        ttk.Label(filter_frame, text="结果筛选:", font=DarkTheme.FONT_SMALL).pack(side='left')
        self.filter_var = tk.StringVar(value='全部')
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=['全部', '接收', '拒收'],
            state='readonly',
            width=6
        )
        filter_combo.pack(side='left', padx=(5, 10))
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_history())

        ttk.Label(filter_frame, text="日期:", font=DarkTheme.FONT_SMALL).pack(side='left')
        self.date_from_var = tk.StringVar()
        date_from_entry = ttk.Entry(filter_frame, textvariable=self.date_from_var, width=10)
        date_from_entry.pack(side='left', padx=(5, 2))
        date_from_entry.bind('<KeyRelease>', lambda e: self._refresh_history())

        ttk.Label(filter_frame, text="~", font=DarkTheme.FONT_SMALL).pack(side='left')
        self.date_to_var = tk.StringVar()
        date_to_entry = ttk.Entry(filter_frame, textvariable=self.date_to_var, width=10)
        date_to_entry.pack(side='left', padx=(2, 5))
        date_to_entry.bind('<KeyRelease>', lambda e: self._refresh_history())

        # 提示文字
        tk.Label(
            filter_frame,
            text="(YYYY-MM-DD)",
            font=('Microsoft YaHei UI', 7),
            bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG_DIM
        ).pack(side='left')

        # 表格
        tree_frame = ttk.Frame(panel)
        tree_frame.pack(fill='both', expand=True)

        columns = ('时间', '批量', '结论', '致命', '严重', '次要')
        self.history_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        col_widths = [130, 60, 60, 70, 70, 70]
        col_anchors = ['w', 'center', 'center', 'center', 'center', 'center']
        for col, width, anchor in zip(columns, col_widths, col_anchors):
            self.history_tree.heading(col, text=col, anchor='center')
            self.history_tree.column(col, width=width, anchor=anchor, minwidth=40)

        # 滚动条
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb.set)

        self.history_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        # 双击查看详情
        self.history_tree.bind('<Double-1>', self._show_record_detail)

    def _build_bottom_bar(self):
        """底部操作栏"""
        bar = tk.Frame(self.main_frame, bg=DarkTheme.BG_ROOT)
        bar.pack(fill='x', pady=(8, 0))

        ttk.Button(
            bar,
            text="📁 导出到CSV",
            style='Export.TButton',
            command=self._export_csv
        ).pack(side='left', padx=(0, 10))

        ttk.Button(
            bar,
            text="🗑 清除历史",
            style='Export.TButton',
            command=self._clear_history
        ).pack(side='left')

        # 记录数
        self.record_count_var = tk.StringVar(value='共 0 条记录')
        tk.Label(
            bar,
            textvariable=self.record_count_var,
            bg=DarkTheme.BG_ROOT, fg=DarkTheme.FG_DIM,
            font=DarkTheme.FONT_SMALL
        ).pack(side='right')

    # ----------------------------------------------------------
    # 业务逻辑
    # ----------------------------------------------------------

    def _auto_calculate(self, event=None):
        """自动计算并刷新所有标准值"""
        # 获取批量
        try:
            lot_size = int(self.lot_size_var.get())
        except ValueError:
            self.code_letter_var.set('—')
            self.sample_size_var.set('—')
            self.actual_sample_var.set('')
            self.adjust_status_var.set('')
            self._clear_standards()
            return

        if lot_size < 2:
            self.code_letter_var.set('无效')
            self.sample_size_var.set('—')
            self.actual_sample_var.set('')
            self.adjust_status_var.set('')
            self._clear_standards()
            return

        # 获取检验水平
        inspection_level = self.inspection_level_var.get()

        # 查字码
        code_letter = self.engine.get_code_letter(lot_size, inspection_level)
        if code_letter is None:
            self.code_letter_var.set('—')
            self.sample_size_var.set('—')
            self._clear_standards()
            return

        self.code_letter_var.set(code_letter)
        sample_size = CODE_SAMPLE_SIZES.get(code_letter, 0)
        self.sample_size_var.set(str(sample_size))
        self.actual_sample_var.set(str(sample_size))
        self.adjust_status_var.set('')

        # 计算各类缺陷标准值
        for key in DEFECT_KEYS:
            aql_str = self.aql_vars[key].get()
            aql_value = AQL_DISPLAY_MAP.get(aql_str, 0)

            plan = self.engine.get_sampling_plan(code_letter, aql_value)
            if plan:
                n, ac, re = plan
                self.aql_display_labels[key].configure(text=aql_str)
                self.ac_vars[key].set(str(ac))
                self.re_vars[key].set(str(re))
            else:
                self.aql_display_labels[key].configure(text='—')
                self.ac_vars[key].set('—')
                self.re_vars[key].set('—')

    def _clear_standards(self):
        """清除标准值显示"""
        for key in DEFECT_KEYS:
            self.aql_display_labels[key].configure(text='—')
            self.ac_vars[key].set('—')
            self.re_vars[key].set('—')

    def _execute_judgment(self):
        """执行批次判定"""
        if self.judge_locked:
            return

        # 锁定按钮 2.5 秒防误触，显示倒计时
        self.judge_locked = True
        self._lock_countdown = 3
        self._update_lock_display()

        try:
            self._do_judgment()
        finally:
            self.root.after(2500, self._unlock_judge_button)

    def _update_lock_display(self):
        """更新按钮锁定倒计时显示"""
        if not self.judge_locked:
            return
        if self._lock_countdown > 0:
            self.judge_btn.configure(
                state='disabled',
                text=f'⏳ 已锁定 ({self._lock_countdown}s)'
            )
            self._lock_countdown -= 1
            self.root.after(800, self._update_lock_display)
        else:
            self.judge_btn.configure(
                state='disabled',
                text='⏳ 请稍候...'
            )

    def _do_judgment(self):
        """实际判定逻辑"""
        # 获取标准抽样数和实际抽样数
        try:
            standard_n = int(self.sample_size_var.get())
        except ValueError:
            messagebox.showwarning('错误', '请先输入批量以获取标准抽样数。')
            return

        try:
            actual_n = int(self.actual_sample_var.get())
        except ValueError:
            actual_n = standard_n

        if actual_n <= 0:
            messagebox.showwarning('错误', '实际抽样数必须大于0。')
            return

        # 比较标准抽样数和实际抽样数，决定判定方式
        adjusted_standards = None
        status_msg = ''

        if actual_n == standard_n:
            # 相等：直接用界面当前 Ac/Re
            pass
        elif actual_n < standard_n:
            # 少于：警告用户
            if not messagebox.askyesno(
                '警告',
                f'实际抽样数 ({actual_n}) 低于标准 ({standard_n})。\n\n'
                '判定仅供参考，风险自负。\n\n是否继续？',
                parent=self.root
            ):
                return
            adjusted_standards = self._lookup_adjusted_standards(actual_n)
            status_msg = f'⚠ 实际抽样数 ({actual_n}) 低于标准 ({standard_n})，已按实际数调整'
        else:
            # 多于：以实际数重查
            adjusted_standards = self._lookup_adjusted_standards(actual_n)
            status_msg = f'ℹ 实际抽样数 ({actual_n}) 高于标准 ({standard_n})，已按实际数调整'
            self.adjust_status_label.configure(fg=DarkTheme.BLUE)

        if status_msg:
            self.adjust_status_var.set(status_msg)

        # 获取当前标准值（UI上显示的，可能含手动覆盖）
        results = []
        all_pass = True

        for key, category in zip(DEFECT_KEYS, DEFECT_CATEGORIES):
            # 获取缺陷数
            try:
                defect_count = int(self.defect_vars[key].get())
            except ValueError:
                defect_count = 0

            # 确定使用的 Ac/Re
            if adjusted_standards:
                # 使用调整后的 Ac/Re
                ac_val = adjusted_standards[key]['ac']
                re_val = adjusted_standards[key]['re']
                orig_ac = int(self.ac_vars[key].get())
                orig_re = int(self.re_vars[key].get())
                standard_text = f'(原标准 Ac≤{orig_ac} Re≥{orig_re} → 调整 Ac≤{ac_val} Re≥{re_val})'
            else:
                # 使用界面当前 Ac/Re
                try:
                    ac_val = int(self.ac_vars[key].get())
                    re_val = int(self.re_vars[key].get())
                except ValueError:
                    ac_val, re_val = 0, 1
                standard_text = f'(标准: Ac≤{ac_val}, Re≥{re_val})'

            # 判定
            if defect_count <= ac_val:
                verdict = 'accept'
                verdict_text = '✅ 接收'
                color = DarkTheme.GREEN
                bg_color = DarkTheme.GREEN_BG
            else:
                verdict = 'reject'
                verdict_text = '❌ 拒收'
                color = DarkTheme.RED
                bg_color = DarkTheme.RED_BG
                all_pass = False

            # 更新结果标签
            detail = f"发现 {defect_count} 个 {standard_text}  {verdict_text}"
            self.result_labels[key].configure(
                text=detail,
                fg=color,
                bg=bg_color
            )

            results.append({
                'category': category,
                'key': key,
                'defect_count': defect_count,
                'ac': ac_val,
                're': re_val,
                'verdict': verdict,
                'verdict_text': verdict_text,
            })

        # 整批结论
        if all_pass:
            self.final_verdict_label.configure(
                text='◉  整 批 接 收  ◉',
                fg=DarkTheme.GREEN,
                bg=DarkTheme.GREEN_BG
            )
            final_verdict = '接收'
            self._flash_widget(self.final_verdict_label, DarkTheme.GREEN_BG, '#0d2818')
            self._play_sound(800, 200)
        else:
            self.final_verdict_label.configure(
                text='◉  整 批 拒 收  ◉',
                fg=DarkTheme.RED,
                bg=DarkTheme.RED_BG
            )
            final_verdict = '拒收'
            self._flash_widget(self.final_verdict_label, DarkTheme.RED_BG, '#281010')
            self._play_sound(400, 400)

        # 保存历史记录
        self._save_to_history(results, final_verdict, actual_n)

        # 刷新历史显示
        self._refresh_history()

    def _lookup_adjusted_standards(self, actual_n):
        """根据实际抽样数向下靠档，重新查表得出调整后的 Ac/Re"""
        actual_code = self.engine.get_code_letter_by_sample_size(actual_n)
        adjusted = {}
        for key in DEFECT_KEYS:
            aql_str = self.aql_vars[key].get()
            aql_value = AQL_DISPLAY_MAP.get(aql_str, 0)
            plan = self.engine.get_sampling_plan(actual_code, aql_value)
            if plan:
                n, ac, re = plan
                adjusted[key] = {'ac': ac, 're': re, 'n': n, 'code': actual_code}
            else:
                adjusted[key] = {'ac': 0, 're': 1, 'n': 0, 'code': actual_code}
        return adjusted

    def _flash_widget(self, widget, color1, color2, count=3):
        """闪烁效果"""
        if count <= 0:
            widget.configure(bg=color1)
            return
        current = widget.cget('bg')
        next_color = color2 if current == color1 else color1
        widget.configure(bg=next_color)
        self.root.after(200, lambda: self._flash_widget(widget, color1, color2, count - 1))

    def _play_sound(self, freq, duration):
        """播放提示音（异步，不阻塞界面）"""
        def _beep():
            if HAS_WINSOUND:
                try:
                    winsound.Beep(freq, duration)
                except Exception:
                    pass
            else:
                sys.stdout.write('\a')
                sys.stdout.flush()
        threading.Thread(target=_beep, daemon=True).start()

    def _unlock_judge_button(self):
        """解锁判定按钮"""
        self.judge_locked = False
        self.judge_btn.configure(state='normal', text='  判  定  ')

    def _save_to_history(self, results, final_verdict, actual_n=None):
        """保存判定记录"""
        record = {
            '判定时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '检验水平': self.inspection_level_var.get(),
            '批量': self.lot_size_var.get(),
            '实际抽样数': actual_n if actual_n is not None else self.sample_size_var.get(),
            '整批结论': final_verdict,
        }

        for r in results:
            key = r['key']
            aql_str = self.aql_vars[key].get()
            prefix_map = {
                'critical': '致命缺陷',
                'major': '严重缺陷',
                'minor': '次要缺陷',
            }
            prefix = prefix_map[key]
            record[f'{prefix}AQL'] = aql_str
            record[f'{prefix}Ac'] = r['ac']
            record[f'{prefix}Re'] = r['re']
            record[f'{prefix}缺陷数'] = r['defect_count']
            record[f'{prefix}判定'] = r['verdict_text']

        self.history.add_record(record)

    def _refresh_history(self):
        """刷新历史记录列表"""
        # 清空现有行
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # 获取筛选条件
        date_from = self.date_from_var.get().strip() or None
        date_to = self.date_to_var.get().strip() or None
        result_filter = self.filter_var.get()

        records = self.history.filter(date_from, date_to, result_filter)

        # 填充表格
        for r in records:
            time_str = r.get('判定时间', '')
            lot_size = r.get('批量', '')
            conclusion = r.get('整批结论', '')
            critical_r = r.get('致命缺陷判定', '')
            major_r = r.get('严重缺陷判定', '')
            minor_r = r.get('次要缺陷判定', '')

            # 简化显示
            def simplify(text):
                if '接收' in str(text):
                    return '✓'
                elif '拒收' in str(text):
                    return '✗'
                return '-'

            values = (
                time_str,
                lot_size,
                conclusion,
                simplify(critical_r),
                simplify(major_r),
                simplify(minor_r),
            )

            # 根据结论设置行颜色
            tag = 'accept' if conclusion == '接收' else 'reject'
            self.history_tree.insert('', 'end', values=values, tags=(tag,))

        # 配置标签颜色
        self.history_tree.tag_configure('accept', foreground=DarkTheme.GREEN)
        self.history_tree.tag_configure('reject', foreground=DarkTheme.RED)

        # 更新计数
        self.record_count_var.set(f'共 {len(records)} 条记录 (总计 {len(self.history.records)} 条)')

    def _show_record_detail(self, event=None):
        """显示记录详情"""
        selection = self.history_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.history_tree.item(item, 'values')
        time_str = values[0] if len(values) > 0 else ''

        # 查找完整记录
        record = None
        for r in self.history.records:
            if r.get('判定时间') == time_str:
                record = r
                break

        if not record:
            return

        # 构建详情窗口
        detail_win = tk.Toplevel(self.root)
        detail_win.title('判定详情')
        detail_win.geometry('500x420')
        detail_win.configure(bg=DarkTheme.BG_FRAME)
        detail_win.transient(self.root)

        # 居中
        detail_win.update_idletasks()
        dw, dh = 500, 420
        sw = detail_win.winfo_screenwidth()
        sh = detail_win.winfo_screenheight()
        detail_win.geometry(f'{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}')

        # 内容
        tk.Label(
            detail_win, text='判定记录详情',
            font=DarkTheme.FONT_HEADING,
            bg=DarkTheme.BG_FRAME, fg=DarkTheme.FG_HEADER
        ).pack(pady=(15, 10))

        text = tk.Text(
            detail_win,
            bg=DarkTheme.BG_ENTRY,
            fg=DarkTheme.FG,
            font=DarkTheme.FONT_MONO,
            relief='flat',
            padx=15,
            pady=15,
            wrap='word',
            height=16
        )
        text.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        # 格式化显示
        lines = []
        important_keys = [
            '判定时间', '检验水平', '批量', '整批结论',
            '致命缺陷AQL', '致命Ac', '致命Re', '致命缺陷数', '致命判定',
            '严重缺陷AQL', '严重Ac', '严重Re', '严重缺陷数', '严重判定',
            '次要缺陷AQL', '次要Ac', '次要Re', '次要缺陷数', '次要判定',
        ]
        for k in important_keys:
            v = record.get(k, '—')
            lines.append(f"  {k}:  {v}")

        text.insert('1.0', '\n'.join(lines))
        text.configure(state='disabled')

        ttk.Button(
            detail_win,
            text='关闭',
            command=detail_win.destroy
        ).pack(pady=(0, 15))

    def _export_csv(self):
        """导出历史记录为 CSV"""
        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title='导出历史记录',
            defaultextension='.csv',
            filetypes=[
                ('CSV 文件', '*.csv'),
                ('所有文件', '*.*'),
            ],
            initialfile=f"AQL_History_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if not filepath:
            return

        # 使用当前筛选结果
        date_from = self.date_from_var.get().strip() or None
        date_to = self.date_to_var.get().strip() or None
        result_filter = self.filter_var.get()
        records = self.history.filter(date_from, date_to, result_filter)

        if self.history.export_csv(filepath, records):
            messagebox.showinfo('导出成功', f'已导出 {len(records)} 条记录到:\n{filepath}')
        else:
            messagebox.showwarning('导出失败', '没有记录可导出或导出过程出错。')

    def _clear_history(self):
        """清除历史记录"""
        if not self.history.records:
            messagebox.showinfo('提示', '没有历史记录可清除。')
            return

        result = messagebox.askyesno(
            '确认清除',
            f'确定要清除全部 {len(self.history.records)} 条历史记录吗？\n此操作不可恢复。',
            parent=self.root
        )

        if result:
            self.history.records = []
            self.history.save()
            self._refresh_history()
            messagebox.showinfo('完成', '历史记录已清除。')

    def _on_close(self):
        """关闭窗口"""
        self.root.destroy()

    def run(self):
        """启动应用"""
        self.root.mainloop()


# ============================================================
# 入口
# ============================================================

def main():
    app = AQLApp()
    app.run()


if __name__ == '__main__':
    main()
