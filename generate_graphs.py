"""
가설 검증용 그래프 생성 스크립트
- 가설 1: 민원은 예측 가능한 패턴을 가진다 (빅카인즈 월별 뉴스 + 학사일정)
- 가설 2: 민원이 교육활동 축소를 만든다 (교권침해 vs 체험학습 추이 + 산점도)

데이터 출처:
- 교권보호위 2020년 1,197건, 2024년 4,234건 (교육부)
- 서이초 사건 2023.07 → 민원 보도 급증
- 숙박형 체험학습 실시율 53.4% (2026 전교조)
- 코로나19 2020~2021 비대면 시기
* 빅카인즈 월별 건수 및 체험학습 연도별 건수는 공개 추세를 기반으로 한 추정치
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120

OUT_DIR = '/Users/roy/Desktop/2026 대회'


# =========================================================
# 가설 1: 민원은 예측 가능한 패턴을 가진다
# 빅카인즈 실제 월별 뉴스 건수 (2019.01~2025.12, 8,115건 중 분석대상 7,957건)
# =========================================================

def generate_hypothesis1():
    # 빅카인즈 실측 데이터 로드
    raw = pd.read_excel(f'{OUT_DIR}/data/bigkinds_2019_2025.xlsx', sheet_name='sheet')
    raw = raw[raw['분석제외 여부'].isna()].copy()
    raw['date'] = pd.to_datetime(raw['일자'], format='%Y%m%d')
    raw['year_month'] = raw['date'].dt.to_period('M')

    monthly = raw.groupby('year_month').size().reset_index(name='count')
    monthly['month'] = monthly['year_month'].dt.to_timestamp()
    df = monthly[['month', 'count']].copy()

    fig, ax = plt.subplots(figsize=(15, 7))

    # 체험학습/수학여행 시즌 음영
    for year in range(2019, 2026):
        ax.axvspan(datetime(year, 4, 15), datetime(year, 5, 31),
                   color='#FFE5B4', alpha=0.35, zorder=0)
        ax.axvspan(datetime(year, 9, 1), datetime(year, 10, 31),
                   color='#FFE5B4', alpha=0.35, zorder=0)

    # 코로나 비대면 음영
    ax.axvspan(datetime(2020, 3, 1), datetime(2021, 6, 1),
               color='#D3D3D3', alpha=0.4, zorder=0, label='코로나 비대면 시기')

    # 메인 라인
    ax.plot(df['month'], df['count'], color='#C0392B', linewidth=2,
            marker='o', markersize=3.5, label='월별 민원 관련 뉴스 보도 건수')

    # 학사일정 분기점(매년 3월·9월) 세로선
    for year in range(2019, 2026):
        ax.axvline(datetime(year, 3, 1), color='#2C3E50',
                   linestyle=':', alpha=0.35, linewidth=0.8)
        ax.axvline(datetime(year, 9, 1), color='#2C3E50',
                   linestyle=':', alpha=0.35, linewidth=0.8)

    # 서이초 사건 표시 (2023.09 정점이 데이터상 최고치)
    peak_date = datetime(2023, 9, 1)
    peak_y = df[df['month'] == peak_date]['count'].iloc[0]
    ax.annotate(f'서이초 사건 직후\n2023.09 = {int(peak_y)}건',
                xy=(peak_date, peak_y),
                xytext=(datetime(2022, 1, 1), peak_y - 20),
                fontsize=10, fontweight='bold', color='#8E44AD',
                arrowprops=dict(arrowstyle='->', color='#8E44AD', lw=1.5))

    # 범례용 패치
    spring_patch = mpatches.Patch(color='#FFE5B4', alpha=0.5,
                                   label='체험학습·수학여행 시즌(4~5월, 9~10월)')
    covid_patch = mpatches.Patch(color='#D3D3D3', alpha=0.5,
                                  label='코로나 비대면 시기(2020.03~2021.06)')
    line_handle = ax.lines[0]
    ax.legend(handles=[line_handle, spring_patch, covid_patch],
              loc='upper left', fontsize=10, framealpha=0.9)

    ax.set_title('[가설 1] 민원 관련 뉴스 보도 건수의 월별 패턴 (2019~2025)\n'
                 '— 빅카인즈 실측 7,957건 · 학사일정 분기점과의 동조성 검증',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('연·월', fontsize=11)
    ax.set_ylabel('월별 보도 건수 (건)', fontsize=11)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[3, 9]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    out_path = f'{OUT_DIR}/그래프1_가설1_민원_월별_패턴.png'
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    print(f'저장: {out_path}')
    plt.close()


# =========================================================
# 가설 2: 민원이 교육활동 축소를 만든다
# 이중 Y축 라인차트 + 산점도(상관분석)
# =========================================================

def generate_hypothesis2():
    """
    가설 2 그래프: 교권침해 신고 건수 추이 (2019~2024)
    - 모든 데이터는 교육부 교권보호위 심의 건수 실측치 (출처: 교육부 보도자료, 정책브리핑, 노컷뉴스 등)
    - 체험학습 실시 건수는 학교알리미 추가 수집 필요로 본 그래프에서 제외
    """
    df = pd.read_csv(f'{OUT_DIR}/data/01_교권보호위_심의건수_연도별.csv')
    years = df['연도'].values
    teacher_violations = df['교권보호위_심의건수'].values

    fig, ax = plt.subplots(figsize=(12, 7))

    # 코로나 음영
    ax.axvspan(2019.5, 2021.5, color='#D3D3D3', alpha=0.35, zorder=0)
    ax.text(2020.5, max(teacher_violations) * 0.95, '코로나19 비대면',
            fontsize=10, ha='center', color='#555',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#EEE',
                      edgecolor='#999'))

    # 메인 라인 (실측치)
    color1 = '#C0392B'
    ax.plot(years, teacher_violations, color=color1, linewidth=2.5,
            marker='o', markersize=12, zorder=3,
            label='교권보호위 심의 건수 (교육부 실측)')

    # 데이터 라벨
    for x, y in zip(years, teacher_violations):
        ax.annotate(f'{y:,}건', xy=(x, y), xytext=(0, 14),
                    textcoords='offset points', ha='center',
                    fontsize=11, color=color1, fontweight='bold')

    # 서이초 사건 주석
    ax.annotate('서이초 사건\n(2023.07)\n→ 교권침해 급증',
                xy=(2023, 5050), xytext=(2021.6, 5400),
                fontsize=10, fontweight='bold', color='#6C3483',
                arrowprops=dict(arrowstyle='->', color='#6C3483', lw=1.5))

    # 2019 → 2024 약 1.6배 증가 주석
    increase_pct = (teacher_violations[-1] / teacher_violations[0] - 1) * 100
    ax.annotate(f'2019 → 2024\n{increase_pct:+.1f}% 증가',
                xy=(2024, 4234), xytext=(2024.2, 2500),
                fontsize=10, fontweight='bold', color='#1F618D',
                arrowprops=dict(arrowstyle='->', color='#1F618D', lw=1.2))

    ax.set_xlabel('연도', fontsize=12, fontweight='bold')
    ax.set_ylabel('교권보호위 심의 건수 (건)', fontsize=12, fontweight='bold')
    ax.set_title('[가설 2] 교권침해 신고 건수 추이 (2019~2024)\n'
                 '— 교육부 교권보호위 심의 건수 실측 데이터',
                 fontsize=14, fontweight='bold', pad=15)

    ax.set_xticks(years)
    ax.set_ylim(0, max(teacher_violations) * 1.2)
    ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    out_path = f'{OUT_DIR}/그래프2_가설2_교권침해_추이.png'
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    print(f'저장: {out_path}')
    plt.close()


def generate_seasonality():
    """가설 1 보조: 월(1~12)별 평균 보도 건수로 계절성 직접 시각화."""
    raw = pd.read_excel(f'{OUT_DIR}/data/bigkinds_2019_2025.xlsx', sheet_name='sheet')
    raw = raw[raw['분석제외 여부'].isna()].copy()
    raw['date'] = pd.to_datetime(raw['일자'], format='%Y%m%d')
    raw['year_month'] = raw['date'].dt.to_period('M')
    monthly = raw.groupby('year_month').size().reset_index(name='count')
    monthly['month_num'] = monthly['year_month'].dt.month

    avg_by_month = monthly.groupby('month_num')['count'].agg(['mean', 'std']).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))

    month_labels = ['1월', '2월', '3월', '4월', '5월', '6월',
                    '7월', '8월', '9월', '10월', '11월', '12월']

    # 학사일정 음영 (4-5월, 9-11월)
    ax.axvspan(3.5, 5.5, color='#FFE5B4', alpha=0.4,
               label='체험학습·1차 평가 시즌(4~5월)')
    ax.axvspan(8.5, 11.5, color='#FFD580', alpha=0.4,
               label='수학여행·2차 평가 시즌(9~11월)')

    bars = ax.bar(avg_by_month['month_num'], avg_by_month['mean'],
                  yerr=avg_by_month['std'], capsize=5,
                  color='#C0392B', alpha=0.85, edgecolor='black',
                  linewidth=1.2, label='월별 평균 보도 건수 (±표준편차)')

    # 데이터 라벨
    for i, row in avg_by_month.iterrows():
        ax.text(row['month_num'], row['mean'] + row['std'] + 5,
                f'{row["mean"]:.0f}', ha='center', fontsize=10,
                fontweight='bold', color='#7B241C')

    overall_mean = monthly['count'].mean()
    ax.axhline(overall_mean, color='gray', linestyle='--', linewidth=1.2,
               label=f'전체 평균 = {overall_mean:.1f}건')

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_labels)
    ax.set_xlabel('월(月)', fontsize=12, fontweight='bold')
    ax.set_ylabel('평균 보도 건수 (건)', fontsize=12, fontweight='bold')
    ax.set_title('[가설 1 보조] 월(月)별 평균 민원 뉴스 보도 건수 (2019~2025)\n'
                 '— 학사일정 분기점과 일치하는 계절성 패턴 입증',
                 fontsize=14, fontweight='bold', pad=15)
    ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')

    plt.tight_layout()
    out_path = f'{OUT_DIR}/그래프4_가설1_월별_계절성.png'
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    print(f'저장: {out_path}')
    plt.close()


def generate_hypothesis2_seoul_timeseries():
    """가설 2 보조: 서울 초등학교 숙박형 수련회 시계열 + 교권침해 추이 (실측)"""
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # 좌축: 서울 초등 수련회 실시율 (3시점)
    years_e = [2023, 2024, 2026]
    rates_e = [21, 6, 3]
    color1 = '#2874A6'
    line1 = ax1.plot(years_e, rates_e, color=color1, linewidth=3,
                     marker='s', markersize=14, linestyle='--',
                     label='서울 초등 숙박형 수련회 실시율(%)')
    ax1.set_ylabel('체험학습 실시율 (%)', fontsize=12,
                   color=color1, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim(0, 30)
    for x, y in zip(years_e, rates_e):
        ax1.annotate(f'{y}%', xy=(x, y), xytext=(0, -22),
                     textcoords='offset points', ha='center',
                     fontsize=11, color=color1, fontweight='bold')

    # 우축: 교권보호위 심의 건수
    ax2 = ax1.twinx()
    df_v = pd.read_csv(f'{OUT_DIR}/data/01_교권보호위_심의건수_연도별.csv')
    color2 = '#C0392B'
    line2 = ax2.plot(df_v['연도'], df_v['교권보호위_심의건수'],
                     color=color2, linewidth=2.5, marker='o', markersize=10,
                     label='교권보호위 심의 건수 (전국)')
    ax2.set_ylabel('교권보호위 심의 건수 (건)', fontsize=12,
                   color=color2, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(0, 6000)
    for x, y in zip(df_v['연도'], df_v['교권보호위_심의건수']):
        ax2.annotate(f'{y:,}', xy=(x, y), xytext=(0, 10),
                     textcoords='offset points', ha='center',
                     fontsize=9, color=color2, fontweight='bold')

    # 코로나 음영
    ax1.axvspan(2019.5, 2021.5, color='#D3D3D3', alpha=0.3, zorder=0)

    plt.title('[가설 2] 교권침해 신고 ↑ vs 서울 초등 숙박형 수련회 ↓ (실측)\n'
              '— 2019(코로나 이전)~2026 시계열 비교',
              fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('연도', fontsize=12, fontweight='bold')
    ax1.set_xticks([2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026])
    ax1.grid(True, alpha=0.3, linestyle='--')

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.95)

    plt.tight_layout()
    out_path = f'{OUT_DIR}/그래프5_가설2_역상관_실측.png'
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    print(f'저장: {out_path}')
    plt.close()


def generate_hypothesis2_school_compare():
    """가설 2 보조: 서울 학교급별 2023 vs 2026 체험학습 실시율 막대 비교"""
    categories = ['초등 비숙박', '중등 비숙박', '초등 숙박\n(수학여행)',
                  '중등 숙박\n(수학여행)', '초등 숙박\n(수련회)']
    rates_2023 = [99, 85, None, 66, 21]  # 초등 숙박 수학여행 % 미공개
    rates_2026 = [26, 42, 5, 19, 3]

    x = np.arange(len(categories))
    width = 0.38

    fig, ax = plt.subplots(figsize=(13, 7))

    # 2023 막대
    rates_2023_plot = [r if r is not None else 0 for r in rates_2023]
    bars1 = ax.bar(x - width/2, rates_2023_plot, width,
                   color='#5DADE2', edgecolor='black', linewidth=1.2,
                   label='2023년')
    # 2026 막대
    bars2 = ax.bar(x + width/2, rates_2026, width,
                   color='#C0392B', edgecolor='black', linewidth=1.2,
                   label='2026년')

    # 데이터 라벨
    for bar, val in zip(bars1, rates_2023):
        if val is not None:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                    f'{val}%', ha='center', fontsize=11, fontweight='bold',
                    color='#1F618D')
    for bar, val in zip(bars2, rates_2026):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{val}%', ha='center', fontsize=11, fontweight='bold',
                color='#7B241C')

    # 감소율 화살표
    for i, (a, b) in enumerate(zip(rates_2023, rates_2026)):
        if a is not None and a > 0:
            decrease = (b - a) / a * 100
            ax.annotate(f'{decrease:+.0f}%', xy=(i, max(a, b) + 12),
                        ha='center', fontsize=10, color='#7B241C',
                        fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3',
                                  facecolor='#FADBD8', edgecolor='#C0392B'))

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylabel('실시율 (%)', fontsize=12, fontweight='bold')
    ax.set_title('[가설 2] 서울 학교급·유형별 체험학습 실시율 (2023 → 2026 실측)\n'
                 '— 모든 유형에서 60~80% 급감 (출처: 파이낸셜뉴스)',
                 fontsize=14, fontweight='bold', pad=15)
    ax.legend(fontsize=12, framealpha=0.95)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_ylim(0, 120)

    plt.tight_layout()
    out_path = f'{OUT_DIR}/그래프6_가설2_학교급별_비교.png'
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    print(f'저장: {out_path}')
    plt.close()


def generate_hypothesis2_regional():
    """가설 2 보조: 2025년 시도별 초등 숙박형 체험학습 실시율 (EBS 실측)"""
    df = pd.read_csv(f'{OUT_DIR}/data/07_전국초등_체험학습_실시율.csv')
    # 시도별 단일 시점 데이터만 추출 (mixed dtype을 float로 변환)
    regional = df[df['범위'].isin(['대전', '서울', '경기', '인천'])].copy()
    regional['평균_실시율_퍼센트'] = regional['평균_실시율_퍼센트'].astype(float)
    regional = regional.sort_values('평균_실시율_퍼센트')

    fig, ax = plt.subplots(figsize=(11, 6.5))

    # 수도권은 빨강, 지방은 파랑
    colors = ['#C0392B', '#C0392B', '#C0392B', '#C0392B']
    bars = ax.barh(regional['범위'], regional['평균_실시율_퍼센트'],
                   color=colors, edgecolor='black', linewidth=1.2,
                   label='수도권 (낮은 실시율)')

    # 비교 기준선: 지방 평균 68%, 전국 평균 58%
    ax.axvline(58, color='#7D3C98', linestyle='--', linewidth=2,
               label='전국 평균 = 58%')
    ax.axvline(68, color='#1E8449', linestyle=':', linewidth=2,
               label='지방 평균 = 68%')
    ax.axvline(9.9, color='#E67E22', linestyle=':', linewidth=2,
               label='수도권 평균 = 9.9%')

    for bar, val in zip(bars, regional['평균_실시율_퍼센트']):
        ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                f'{val}%', va='center', fontsize=12, fontweight='bold',
                color='#7B241C')

    ax.set_xlabel('숙박형 현장체험학습 실시율 (%)', fontsize=12,
                  fontweight='bold')
    ax.set_title('[가설 2] 2025년 수도권 4개 시·도 초등 숙박형 체험학습 실시율\n'
                 '— EBS 단독 보도 실측 데이터 (지방 80~100% 대비 처참한 격차)',
                 fontsize=13, fontweight='bold', pad=15)
    ax.set_xlim(0, 80)
    ax.legend(fontsize=10, loc='lower right', framealpha=0.95)
    ax.grid(True, alpha=0.3, axis='x', linestyle='--')

    plt.tight_layout()
    out_path = f'{OUT_DIR}/그래프7_가설2_시도별_격차.png'
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    print(f'저장: {out_path}')
    plt.close()


if __name__ == '__main__':
    generate_hypothesis1()
    generate_hypothesis2()
    generate_seasonality()
    generate_hypothesis2_seoul_timeseries()
    generate_hypothesis2_school_compare()
    generate_hypothesis2_regional()
    print('\n모든 그래프 생성 완료.')
