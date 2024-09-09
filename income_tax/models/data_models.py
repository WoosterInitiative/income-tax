from decimal import Decimal
from enum import Enum, auto
from typing import Annotated

from collections.abc import Mapping
from pydantic import BaseModel, RootModel
from annotated_types import Le

from income_tax.custom_types import WholeDollar


class PovertyLine(BaseModel):
    family_size: int
    poverty_line: WholeDollar


class StateOfResidenceEnum(Enum):
    CONTIGUOUS_48_AND_DC = auto()
    ALASKA = auto()
    HAWAII = auto()


class PovertyLineTable(BaseModel):
    state_of_residence: StateOfResidenceEnum
    values: Mapping[int, WholeDollar]
    additional_person_extra: WholeDollar

    def get_poverty_rate(self, tax_family_size: int):
        try:
            return self.values[tax_family_size]
        except KeyError:
            largest_size = max([k for k in self.values.keys()])
            largest_value = self.values[largest_size]
            additional_persons = tax_family_size - largest_size
            adder = additional_persons * self.additional_person_extra

            return largest_value + adder


class PovertyLines(RootModel):
    root: list[PovertyLineTable]

    def get_state_table(self, state_of_residence: StateOfResidenceEnum):
        filtered_list = [
            table
            for table in self.root
            if table.state_of_residence == state_of_residence
        ]
        results = len(filtered_list)
        if results > 1:
            msg = f"More than one match found [{results}]"
            raise ValueError(msg)
        if results == 0:
            msg = f"No results found matching '{state_of_residence}'"
            raise ValueError(msg)
        return filtered_list[0]

    def get_poverty_rate(
        self, state_of_residence: StateOfResidenceEnum, tax_family_size: int
    ):
        table = self.get_state_table(state_of_residence=state_of_residence)

        return table.get_poverty_rate(tax_family_size=tax_family_size)


CONTIGUOUS_48_AND_DC = {
    1: 13590,
    2: 18310,
    3: 23030,
    4: 27750,
    5: 32470,
    6: 37190,
    7: 41910,
    8: 46630,
}

CONTIGUOUS_48_AND_DC_EXTRA = 4720

ALASKA = {
    1: 16990,
    2: 22890,
    3: 28790,
    4: 34690,
    5: 40590,
    6: 46490,
    7: 52390,
    8: 58290,
}

ALASKA_EXTRA = 5900

HAWAII = {
    1: 15630,
    2: 21060,
    3: 26490,
    4: 31920,
    5: 37350,
    6: 42780,
    7: 48210,
    8: 53640,
}

HAWAII_EXTRA = 5430

poverty_lines = PovertyLines(
    root=[
        PovertyLineTable(
            state_of_residence=StateOfResidenceEnum.CONTIGUOUS_48_AND_DC,
            values=CONTIGUOUS_48_AND_DC,
            additional_person_extra=CONTIGUOUS_48_AND_DC_EXTRA,
        ),
        PovertyLineTable(
            state_of_residence=StateOfResidenceEnum.ALASKA,
            values=ALASKA,
            additional_person_extra=ALASKA_EXTRA,
        ),
        PovertyLineTable(
            state_of_residence=StateOfResidenceEnum.HAWAII,
            values=HAWAII,
            additional_person_extra=HAWAII_EXTRA,
        ),
    ]
)


applicable_figures_dict = {
    150: 0.0000,
    151: 0.0004,
    152: 0.0008,
    153: 0.0012,
    154: 0.0016,
    155: 0.0020,
    156: 0.0024,
    157: 0.0028,
    158: 0.0032,
    159: 0.0036,
    160: 0.0040,
    161: 0.0044,
    162: 0.0048,
    163: 0.0052,
    164: 0.0056,
    165: 0.0060,
    166: 0.0064,
    167: 0.0068,
    168: 0.0072,
    169: 0.0076,
    170: 0.0080,
    171: 0.0084,
    172: 0.0088,
    173: 0.0092,
    174: 0.0096,
    175: 0.0100,
    176: 0.0104,
    177: 0.0108,
    178: 0.0112,
    179: 0.0116,
    180: 0.0120,
    181: 0.0124,
    182: 0.0128,
    183: 0.0132,
    184: 0.0136,
    185: 0.0140,
    186: 0.0144,
    187: 0.0148,
    188: 0.0152,
    189: 0.0156,
    190: 0.0160,
    191: 0.0164,
    192: 0.0168,
    193: 0.0172,
    194: 0.0176,
    195: 0.0180,
    196: 0.0184,
    197: 0.0188,
    198: 0.0192,
    199: 0.0196,
    200: 0.0200,
    201: 0.0204,
    202: 0.0208,
    203: 0.0212,
    204: 0.0216,
    205: 0.0220,
    206: 0.0224,
    207: 0.0228,
    208: 0.0232,
    209: 0.0236,
    210: 0.0240,
    211: 0.0244,
    212: 0.0248,
    213: 0.0252,
    214: 0.0256,
    215: 0.0260,
    216: 0.0264,
    217: 0.0268,
    218: 0.0272,
    219: 0.0276,
    220: 0.0280,
    221: 0.0284,
    222: 0.0288,
    223: 0.0292,
    224: 0.0296,
    225: 0.0300,
    226: 0.0304,
    227: 0.0308,
    228: 0.0312,
    229: 0.0316,
    230: 0.0320,
    231: 0.0324,
    232: 0.0328,
    233: 0.0332,
    234: 0.0336,
    235: 0.0340,
    236: 0.0344,
    237: 0.0348,
    238: 0.0352,
    239: 0.0356,
    240: 0.0360,
    241: 0.0364,
    242: 0.0368,
    243: 0.0372,
    244: 0.0376,
    245: 0.0380,
    246: 0.0384,
    247: 0.0388,
    248: 0.0392,
    249: 0.0396,
    250: 0.0400,
    251: 0.0404,
    252: 0.0408,
    253: 0.0412,
    254: 0.0416,
    255: 0.0420,
    256: 0.0424,
    257: 0.0428,
    258: 0.0432,
    259: 0.0436,
    260: 0.0440,
    261: 0.0444,
    262: 0.0448,
    263: 0.0452,
    264: 0.0456,
    265: 0.0460,
    266: 0.0464,
    267: 0.0468,
    268: 0.0472,
    269: 0.0476,
    270: 0.0480,
    271: 0.0484,
    272: 0.0488,
    273: 0.0492,
    274: 0.0496,
    275: 0.0500,
    276: 0.0504,
    277: 0.0508,
    278: 0.0512,
    279: 0.0516,
    280: 0.0520,
    281: 0.0524,
    282: 0.0528,
    283: 0.0532,
    284: 0.0536,
    285: 0.0540,
    286: 0.0544,
    287: 0.0548,
    288: 0.0552,
    289: 0.0556,
    290: 0.0560,
    291: 0.0564,
    292: 0.0568,
    293: 0.0572,
    294: 0.0576,
    295: 0.0580,
    296: 0.0584,
    297: 0.0588,
    298: 0.0592,
    299: 0.0596,
    300: 0.0600,
    301: 0.0603,
    302: 0.0605,
    303: 0.0608,
    304: 0.0610,
    305: 0.0613,
    306: 0.0615,
    307: 0.0618,
    308: 0.0620,
    309: 0.0623,
    310: 0.0625,
    311: 0.0628,
    312: 0.0630,
    313: 0.0633,
    314: 0.0635,
    315: 0.0638,
    316: 0.0640,
    317: 0.0643,
    318: 0.0645,
    319: 0.0648,
    320: 0.0650,
    321: 0.0653,
    322: 0.0655,
    323: 0.0658,
    324: 0.0660,
    325: 0.0663,
    326: 0.0665,
    327: 0.0668,
    328: 0.0670,
    329: 0.0673,
    330: 0.0675,
    331: 0.0678,
    332: 0.0680,
    333: 0.0683,
    334: 0.0685,
    335: 0.0688,
    336: 0.0690,
    337: 0.0693,
    338: 0.0695,
    339: 0.0698,
    340: 0.0700,
    341: 0.0703,
    342: 0.0705,
    343: 0.0708,
    344: 0.0710,
    345: 0.0713,
    346: 0.0715,
    347: 0.0718,
    348: 0.0720,
    349: 0.0723,
    350: 0.0725,
    351: 0.0728,
    352: 0.0730,
    353: 0.0733,
    354: 0.0735,
    355: 0.0738,
    356: 0.0740,
    357: 0.0743,
    358: 0.0745,
    359: 0.0748,
    360: 0.0750,
    361: 0.0753,
    362: 0.0755,
    363: 0.0758,
    364: 0.0760,
    365: 0.0763,
    366: 0.0765,
    367: 0.0768,
    368: 0.0770,
    369: 0.0773,
    370: 0.0775,
    371: 0.0778,
    372: 0.0780,
    373: 0.0783,
    374: 0.0785,
    375: 0.0788,
    376: 0.0790,
    377: 0.0793,
    378: 0.0795,
    379: 0.0798,
    380: 0.0800,
    381: 0.0803,
    382: 0.0805,
    383: 0.0808,
    384: 0.0810,
    385: 0.0813,
    386: 0.0815,
    387: 0.0818,
    388: 0.0820,
    389: 0.0823,
    390: 0.0825,
    391: 0.0828,
    392: 0.0830,
    393: 0.0833,
    394: 0.0835,
    395: 0.0838,
    396: 0.0840,
    397: 0.0843,
    398: 0.0845,
    399: 0.0848,
    400: 0.0850,
}


class ApplicableFigures(BaseModel):
    figures: Mapping[int, float | Decimal]

    def get_figure(self, percent: Annotated[int, Le(401)]):
        min_percent = min(self.figures.keys())
        max_percent = max(self.figures.keys())
        if percent <= min_percent:
            return self.figures[min_percent]
        if percent > max_percent:
            return self.figures[max_percent]
        return self.figures[percent]


applicable_figures = ApplicableFigures(
    figures=applicable_figures_dict,
)
